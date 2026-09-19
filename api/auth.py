from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import datetime

from database.connection import get_db
from database.schema import User
from configs.security import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "Citizen" # Citizen, Planner, Government Official, Administrator, Researcher

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    must_change_password: bool = False
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    must_change_password: bool = False

class FirebaseLogin(BaseModel):
    email: EmailStr
    role: Optional[str] = "Planner"
    display_name: Optional[str] = None
    firebase_uid: Optional[str] = None
    password: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: Optional[str] = None
    new_password: str

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    user = db.query(User).filter_by(email=email).first()
    if user is None:
        raise credentials_exception
    return user

def require_role(roles: list[str]):
    def dependency(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return user
    return dependency

@router.post("/register", response_model=UserResponse)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter_by(email=user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=hashed,
        role=user_in.role,
        must_change_password=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/token", response_model=Token)
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=form_data.username).first()
    if not user or not verify_password(user.password_hash, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": bool(user.must_change_password)
    }

@router.post("/firebase-login", response_model=Token)
def firebase_login(data: FirebaseLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        # Create new user record for Firebase or direct user
        pwd = data.password if data.password else (data.firebase_uid or "mirrorcity_authenticated_user")
        user = User(
            email=data.email,
            password_hash=hash_password(pwd),
            role=data.role or "Planner",
            must_change_password=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update role if passed
        if data.role and user.role != data.role:
            user.role = data.role
            db.commit()
            db.refresh(user)

    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "must_change_password": bool(user.must_change_password)
    }

@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    if data.current_password and not verify_password(current_user.password_hash, data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(data.new_password)
    current_user.must_change_password = False
    db.commit()
    db.refresh(current_user)
    return {
        "message": "Password updated successfully. Forced password change cleared.",
        "must_change_password": False
    }

@router.get("/me", response_model=UserResponse)
def get_me(user: User = Depends(get_current_user)):
    return user
