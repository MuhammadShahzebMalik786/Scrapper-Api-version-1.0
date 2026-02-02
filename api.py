#!/usr/bin/env python3
"""
Production-ready Mobile.de Scraper API
Secure, optimized FastAPI with streaming support
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator
import asyncio
import logging
import os
import json
from datetime import datetime

from config_manager import Config
from database import db_manager, Car
from db_operations import get_database_stats
from scraper_unified import MobileDeScraperUnified

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create logs directory
os.makedirs(Config.LOG_DIR, exist_ok=True)

# Configuration validation
config_issues = Config.validate_production()
if config_issues:
    for issue in config_issues:
        logger.warning(f"Configuration issue: {issue}")

app = FastAPI(
    title="Mobile.de Scraper API",
    description="Production API for mobile.de car scraping",
    version="2.0.0"
)

security = HTTPBearer()
scraper_running = False


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
    """Verify API token"""
    if credentials.credentials != Config.API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

@app.get("/", response_model=StatusResponse)
async def root():
    """Health check with system status"""
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


@app.post("/populate")
async def populate_database_stream(token: str = Depends(verify_token)):
    """
    Start streaming scraper with real-time updates
    
    Usage:
    ```
    curl -H "Authorization: Bearer <token>" http://localhost:8000/populate
    ```
    """
    global scraper_running
    
    if scraper_running:
        raise HTTPException(status_code=409, detail="Scraper already running")
    
    async def stream_scraper():
        global scraper_running
        scraper_running = True
        total_cars = 0
        
        try:
            scraper = MobileDeScraperUnified()
            url = "https://www.mobile.de/?lang=en"
            
            async for event in scraper.scrape_streaming(url):
                if event.get("status") == "scraping":
                    cars = event.get("cars", [])
                    total_cars += len(cars)
                    yield f"data: {json.dumps({'type': 'progress', 'page': event['page'], 'cars': len(cars), 'total': total_cars})}\n\n"
                elif event.get("status") == "completed":
                    yield f"data: {json.dumps({'type': 'complete', 'total_pages': event['total_pages'], 'total_cars': total_cars})}\n\n"
                elif event.get("status") == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': event.get('error', 'Unknown error')})}\n\n"
                
                await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        finally:
            scraper_running = False
    
    return StreamingResponse(
        stream_scraper(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/status")
async def get_status():
    """Get scraper status"""
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
async def list_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """List cars with pagination"""
    try:
        with db_manager.get_session() as session:
            cars = session.query(Car).offset(skip).limit(limit).all()
            if not cars:
                raise HTTPException(
                    status_code=404, 
                    detail="No cars found in database. Scraper may still be collecting data."
                )
            return [
                CarResponse(
                    id=car.id,
                    url_title=car.url_title,
                    price=car.price,
                    location=car.location,
                    mileage=car.mileage
                ) for car in cars
            ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing cars: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/cars/{car_id}")
async def get_car(car_id: int, token: str = Depends(verify_token)):
    """Get single car by ID"""
    try:
        with db_manager.get_session() as session:
            car = session.query(Car).filter(Car.id == car_id).first()
            if not car:
                raise HTTPException(status_code=404, detail="Car not found")
            
            return {c.name: getattr(car, c.name) for c in car.__table__.columns}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting car {car_id}: {e}")
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
            if not cars:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No cars found matching '{q}'. Try different search terms."
                )
            return [
                {
                    "id": car.id,
                    "url_title": car.url_title,
                    "price": car.price,
                    "location": car.location
                } for car in cars
            ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
