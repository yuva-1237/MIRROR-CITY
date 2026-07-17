from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List
import datetime

from database.connection import get_db
from database.schema import User, AuditLog
from api.auth import require_role, get_current_user
from database.seed import seed_database

router = APIRouter(prefix="/admin", tags=["admin"])

class UserRoleUpdate(BaseModel):
    role: str

class UserAdminResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True

@router.get("/users", response_model=List[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Administrator"]))
):
    return db.query(User).all()

@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Administrator"]))
):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    valid_roles = ["Citizen", "Planner", "Government Official", "Administrator", "Researcher"]
    if role_update.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Choose from: {', '.join(valid_roles)}")
        
    user.role = role_update.role
    
    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        action=f"Updated User {user.email} role to {role_update.role}"
    )
    db.add(log)
    db.commit()
    db.refresh(user)
    return user

@router.post("/seed", status_code=status.HTTP_200_OK)
def trigger_reseeding(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Administrator"]))
):
    """Clean and reseed database tables."""
    try:
        # We call the seed function
        seed_database()
        
        log = AuditLog(
            user_id=current_user.id,
            action="Re-seeded system database tables"
        )
        db.add(log)
        db.commit()
        return {"status": "success", "message": "Database tables re-seeded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-seeding failed: {str(e)}")

@router.get("/logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["Administrator"]))
):
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
