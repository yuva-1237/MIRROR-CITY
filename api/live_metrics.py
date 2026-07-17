import json
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.connection import get_db
from database.schema import LiveMetric, User
from api.auth import get_current_user
from agents.city_memory import city_memory

router = APIRouter(prefix="/live", tags=["live"])

@router.get("/metrics")
def get_historical_metrics(
    limit: int = Query(60, description="Number of historical ticks to retrieve"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical time-series metrics snapshots for charting."""
    records = db.query(LiveMetric).order_by(LiveMetric.timestamp.desc()).limit(limit).all()
    
    # Sort chronologically for frontend line charts
    records = list(reversed(records))
    
    history = []
    for r in records:
        history.append({
            "timestamp": r.timestamp.isoformat(),
            "metrics": json.loads(r.metrics_json)
        })
        
    return {
        "count": len(history),
        "history": history
    }

@router.get("/memory")
def get_city_memory(
    domain: Optional[str] = Query(None, description="Filter by agent domain (e.g., traffic, flood)"),
    limit: int = Query(30, description="Number of memory logs to recall"),
    current_user: User = Depends(get_current_user)
):
    """Query persistent AI agent observation and reasoning memory."""
    return {
        "memory": city_memory.recall(domain=domain, limit=limit)
    }

@router.get("/memory/search")
def search_city_memory(
    query: str = Query(..., description="Term to search in memory"),
    current_user: User = Depends(get_current_user)
):
    """Perform keyword searches over the persistent city memory log."""
    return {
        "query": query,
        "results": city_memory.query_search(query)
    }
