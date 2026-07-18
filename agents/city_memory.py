import json
import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from database.connection import SessionLocal
from database.schema import CityMemory

logger = logging.getLogger(__name__)

class CityMemoryManager:
    def __init__(self):
        pass

    def remember(self, domain: str, event_type: str, message: str, data_json: Dict[str, Any] = None):
        """Log a new event/reasoning into the city memory."""
        try:
            mem = CityMemory(
                domain=domain,
                event_type=event_type,
                message=message,
                data_json=json.dumps(data_json) if data_json else None,
                timestamp=datetime.datetime.utcnow()
            )
            with SessionLocal() as db:
                db.add(mem)
                db.commit()
        except Exception as e:
            logger.error(f"Error in CityMemoryManager.remember: {e}")

    def recall(self, domain: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent events from the city memory."""
        try:
            with SessionLocal() as db:
                query = db.query(CityMemory)
                if domain:
                    query = query.filter_by(domain=domain)
                results = query.order_by(CityMemory.timestamp.desc()).limit(limit).all()
                
                output = []
                for item in results:
                    output.append({
                        "id": item.id,
                        "domain": item.domain,
                        "event_type": item.event_type,
                        "message": item.message,
                        "data": json.loads(item.data_json) if item.data_json else None,
                        "timestamp": item.timestamp.isoformat()
                    })
                return output
        except Exception as e:
            logger.error(f"Error in CityMemoryManager.recall: {e}")
            return []

    def query_search(self, term: str) -> List[Dict[str, Any]]:
        """Search memory messages by term."""
        try:
            with SessionLocal() as db:
                results = db.query(CityMemory).filter(CityMemory.message.like(f"%{term}%")).order_by(CityMemory.timestamp.desc()).limit(30).all()
                output = []
                for item in results:
                    output.append({
                        "id": item.id,
                        "domain": item.domain,
                        "event_type": item.event_type,
                        "message": item.message,
                        "data": json.loads(item.data_json) if item.data_json else None,
                        "timestamp": item.timestamp.isoformat()
                    })
                return output
        except Exception as e:
            logger.error(f"Error in CityMemoryManager.query_search: {e}")
            return []

city_memory = CityMemoryManager()

