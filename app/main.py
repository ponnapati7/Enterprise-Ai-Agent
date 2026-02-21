from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.llm import ask_llm
from app.database import engine, SessionLocal
from app.models import Base, DocumentAnalysis, User

from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from sqlalchemy import func
import time

app = FastAPI()

Base.metadata.create_all(bind=engine)



@app.get("/")
def home():
    return {"message": "Enterprise AI Agent Running 🚀"}


@app.post("/register")
def register(username: str, password: str):
    db = SessionLocal()

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed = hash_password(password)

    new_user = User(username=username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    db.close()

    return {"message": "User created successfully"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()

    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        db.close()
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access_token = create_access_token(data={"sub": user.username})
    db.close()

    return {"access_token": access_token, "token_type": "bearer"}




from fastapi import Depends
from app.api_key_auth import get_api_key
import time

from fastapi import HTTPException, Depends
from datetime import datetime, date


DAILY_LIMIT = 20


@app.get("/ask")
def ask(
    question: str,
    current_user: User = Depends(get_current_user)
):
    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == current_user.id).first()

        today = date.today()


        if user.last_request_date is None or user.last_request_date.date() != today:
            user.daily_requests = 0
            user.last_request_date = datetime.utcnow()

     
        if user.daily_requests >= DAILY_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="Daily usage limit exceeded"
            )

        
        start_time = time.time()
        answer = ask_llm(question)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000

    
        record = DocumentAnalysis(
            user_id=current_user.id,
            input_text=question,
            ai_response=answer,
            confidence_score=None
        )

        db.add(record)

        user.total_requests += 1
        user.daily_requests += 1

        db.commit()
        db.refresh(record)

        return {
            "id": record.id,
            "response": answer,
            "remaining_today": DAILY_LIMIT - user.daily_requests
        }
    finally:
        db.close()

        embedding = get_embedding(question)

    record = DocumentAnalysis(
    input_text=question,
    ai_response=answer,
    confidence_score=None,
    response_time_ms=response_time,
    embedding=embedding
)



@app.get("/history")
def get_history(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(DocumentAnalysis).filter(
            DocumentAnalysis.user_id == current_user.id
        ).order_by(DocumentAnalysis.id.desc()).all()


        return [
            {
                "id": r.id,
                "question": r.input_text,
                "answer": r.ai_response,
                "response_time_ms": r.response_time_ms,
                "created_at": r.created_at
            }
            for r in records
        ]
    finally:
        db.close()




@app.get("/analytics")
def get_analytics(current_user: User = Depends(get_current_user)):
    db = SessionLocal()
    try:
        total_queries = db.query(func.count(DocumentAnalysis.id)).scalar()

        avg_response_time = db.query(
            func.avg(DocumentAnalysis.response_time_ms)
        ).scalar()

        min_response_time = db.query(
            func.min(DocumentAnalysis.response_time_ms)
        ).scalar()

        max_response_time = db.query(
            func.max(DocumentAnalysis.response_time_ms)
        ).scalar()

        latest_query = db.query(
            func.max(DocumentAnalysis.created_at)
        ).scalar()

        return {
            "total_queries": total_queries,
            "average_response_time_ms": avg_response_time,
            "fastest_response_ms": min_response_time,
            "slowest_response_ms": max_response_time,
            "latest_query_time": latest_query
        }

    finally:
        db.close()

from app.models import APIKey
from fastapi import Depends

@app.post("/generate-api-key")
def generate_api_key(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        new_key = APIKey.generate_key()

        api_key = APIKey(
            key=new_key,
            user_id=current_user.id
        )

        db.add(api_key)
        db.commit()

        return {
            "api_key": new_key,
            "message": "Store this key securely. You won't see it again."
        }

    finally:
        db.close()

@app.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(get_current_user)):
    db = SessionLocal()

    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        total_users = db.query(func.count(User.id)).scalar()
        total_requests = db.query(func.count(DocumentAnalysis.id)).scalar()

        today = datetime.utcnow().date()

        today_requests = db.query(func.count(DocumentAnalysis.id)).filter(
            func.date(DocumentAnalysis.created_at) == today
        ).scalar()

        most_active_user = db.query(User.username).order_by(
            User.total_requests.desc()
        ).first()

        users_hitting_limit = db.query(User.username).filter(
            User.daily_requests >= DAILY_LIMIT
        ).all()

        return {
            "total_users": total_users,
            "total_requests": total_requests,
            "today_requests": today_requests,
            "most_active_user": most_active_user[0] if most_active_user else None,
            "users_hitting_daily_limit": [u[0] for u in users_hitting_limit]
        }

    finally:
        db.close()

from sqlalchemy.orm import Session
from app.database import get_db

@app.get("/admin/dashboard")
def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    total_users = db.query(func.count(User.id)).scalar()
    total_api_keys = db.query(func.count(APIKey.id)).scalar()
    total_queries = db.query(func.count(DocumentAnalysis.id)).scalar()

    avg_response_time = db.query(
        func.avg(DocumentAnalysis.response_time_ms)
    ).scalar()

    top_user = db.query(
        DocumentAnalysis.user_id,
        func.count(DocumentAnalysis.id).label("total")
    ).group_by(DocumentAnalysis.user_id)\
     .order_by(func.count(DocumentAnalysis.id).desc())\
     .first()

    return {
        "total_users": total_users,
        "total_api_keys": total_api_keys,
        "total_queries": total_queries,
        "avg_response_time_ms": avg_response_time,
        "top_active_user_id": top_user[0] if top_user else None
    }

from app.embeddings import get_embedding


from sqlalchemy import text

@app.get("/semantic-search")
def semantic_search(query: str):
    db = SessionLocal()
    try:
        query_embedding = get_embedding(query)

        sql = text("""
            SELECT id, input_text, ai_response,
                   embedding <-> :query_embedding AS distance
            FROM document_analysis
            ORDER BY embedding <-> :query_embedding
            LIMIT 5;
        """)

        results = db.execute(sql, {
            "query_embedding": query_embedding
        }).fetchall()

        return [
            {
                "id": r.id,
                "question": r.input_text,
                "answer": r.ai_response,
                "similarity_score": r.distance
            }
            for r in results
        ]

    finally:
        db.close()