#!/usr/bin/env python3

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import threading
import logging
import os
from datetime import datetime
from database import db_manager, Car
from db_operations import get_database_stats
from config import Config

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs(Config.LOG_DIR, exist_ok=True)

app = FastAPI(
    title="Mobile.de Scraper API",
    description="Production API for mobile.de car scraping",
    version="1.0.0"
)

security = HTTPBearer()
scraper_running = False

class PopulateResponse(BaseModel):
    message: str
    status: str

class StatusResponse(BaseModel):
    status: str
    scraper_running: bool
    database_connected: bool
    timestamp: str

class CarResponse(BaseModel):
    id: int
    url_title: Optional[str]
    price: Optional[str]
    location: Optional[str]
    mileage: Optional[str]

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != Config.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

def scraper_task():
    """Run scraper in background thread"""
    global scraper_running
    try:
        scraper_running = True
        logger.info("Starting scraper task")
        
        # Import here to avoid circular imports
        from scraper import main as run_scraper
        run_scraper()
        
        logger.info("Scraper task completed")
    except Exception as e:
        logger.error(f"Scraper error: {e}")
    finally:
        scraper_running = False

@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint with database status"""
    db_connected = db_manager.health_check()
    
    return StatusResponse(
        status="running",
        scraper_running=scraper_running,
        database_connected=db_connected,
        timestamp=datetime.utcnow().isoformat()
    )

@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/populate", response_model=PopulateResponse)
async def populate_database(background_tasks: BackgroundTasks, token: str = Depends(verify_token)):
    """Start scraping and populate database"""
    global scraper_running
    
    if scraper_running:
        return PopulateResponse(
            message="Scraper is already running",
            status="running"
        )
    
    background_tasks.add_task(scraper_task)
    
    return PopulateResponse(
        message="Scraping started in background",
        status="started"
    )

@app.get("/status")
async def get_status():
    """Get current scraper status"""
    return {
        "scraper_running": scraper_running,
        "database_connected": db_manager.health_check(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/stats")
async def get_stats():
    """Get database statistics"""
    return get_database_stats()

@app.get("/cars", response_model=List[CarResponse])
async def get_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """List cars with pagination"""
    try:
        with db_manager.get_session() as session:
            cars = session.query(Car).offset(skip).limit(limit).all()
            return [
                CarResponse(
                    id=car.id,
                    url_title=car.url_title,
                    price=car.price,
                    location=car.location,
                    mileage=car.mileage
                ) for car in cars
            ]
    except Exception as e:
        logger.error(f"Error fetching cars: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/cars/{car_id}")
async def get_car(car_id: int, token: str = Depends(verify_token)):
    """Get single car by ID"""
    try:
        with db_manager.get_session() as session:
            car = session.query(Car).filter(Car.id == car_id).first()
            if not car:
                raise HTTPException(status_code=404, detail="Car not found")
            
            # Convert to dict
            car_dict = {c.name: getattr(car, c.name) for c in car.__table__.columns}
            return car_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching car {car_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/search")
async def search_cars(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    token: str = Depends(verify_token)
):
    """Search cars by title"""
    try:
        with db_manager.get_session() as session:
            cars = session.query(Car).filter(
                Car.url_title.ilike(f"%{q}%")
            ).limit(limit).all()
            return [
                {
                    "id": car.id,
                    "url_title": car.url_title,
                    "price": car.price,
                    "location": car.location
                } for car in cars
            ]
    except Exception as e:
        logger.error(f"Error searching cars: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
