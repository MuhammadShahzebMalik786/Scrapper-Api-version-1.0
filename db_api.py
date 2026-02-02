#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
import os
from database import Car, get_session

app = FastAPI(title="Mobile Scraper DB API", version="1.0.0")

API_TOKEN = os.getenv('API_TOKEN', 'mobile-scraper-2026-secure-token')
security = HTTPBearer(auto_error=False)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

@app.get("/")
async def root():
    return {
        "service": "Mobile Scraper Database API",
        "version": "1.0.0",
        "endpoints": {
            "GET /cars": "List cars with filters",
            "GET /cars/{id}": "Get single car",
            "GET /stats": "Database statistics",
            "GET /search?q=": "Search cars"
        }
    }

@app.get("/cars")
async def get_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    token: str = Depends(verify_token)
):
    session = get_session()
    try:
        cars = session.query(Car).offset(skip).limit(limit).all()
        return [{"id": car.id, "url_title": car.url_title, "price": car.price, 
                "location": car.location, "mileage": car.mileage} for car in cars]
    finally:
        session.close()

@app.get("/cars/{car_id}")
async def get_car(car_id: int, token: str = Depends(verify_token)):
    session = get_session()
    try:
        car = session.query(Car).filter(Car.id == car_id).first()
        if not car:
            raise HTTPException(status_code=404, detail="Car not found")
        
        # Convert to dict and remove SQLAlchemy internal attributes
        car_dict = {c.name: getattr(car, c.name) for c in car.__table__.columns}
        return car_dict
    finally:
        session.close()

@app.get("/stats")
async def get_stats():
    session = get_session()
    try:
        total_cars = session.query(func.count(Car.id)).scalar()
        return {"total_cars": total_cars, "database_connected": True}
    except Exception as e:
        return {"error": str(e), "database_connected": False}
    finally:
        session.close()

@app.get("/search")
async def search_cars(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    token: str = Depends(verify_token)
):
    session = get_session()
    try:
        cars = session.query(Car).filter(
            Car.url_title.ilike(f"%{q}%")
        ).limit(limit).all()
        return [{"id": car.id, "url_title": car.url_title, "price": car.price} for car in cars]
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
