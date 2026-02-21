from fastapi import Header, HTTPException
from app.database import SessionLocal
from app.models import APIKey

def get_api_key(x_api_key: str = Header(None)):
    db = SessionLocal()

    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key missing")

    key_record = db.query(APIKey).filter(
        APIKey.key == x_api_key,
        APIKey.is_active == True
    ).first()

    if not key_record:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return key_record.user