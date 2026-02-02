#!/usr/bin/env python3

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import asyncio
import threading
import logging
import os
from mobile_scraper_linux_headless import main as run_scraper

# API Token
API_TOKEN = os.getenv('API_TOKEN', 'mobile-scraper-2026-secure-token')
security = HTTPBearer()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mobile.de Scraper API",
    description="Production API for mobile.de car scraping",
    version="1.0.0"
)

class PopulateResponse(BaseModel):
    message: str
    status: str

class StatusResponse(BaseModel):
    status: str
    scraper_running: bool
    database_connected: bool

scraper_running = False

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

def scraper_task():
    """Run scraper in background thread"""
    global scraper_running
    try:
        scraper_running = True
        logger.info("Starting scraper task")
        run_scraper()
        logger.info("Scraper task completed")
    except Exception as e:
        logger.error(f"Scraper error: {e}")
    finally:
        scraper_running = False

@app.get("/", response_model=StatusResponse)
async def root():
    """Health check endpoint"""
    try:
        from database import engine
        db_connected = True
        try:
            with engine.connect() as conn:
                conn.execute("SELECT 1")
        except:
            db_connected = False
    except:
        db_connected = False
    
    return StatusResponse(
        status="running",
        scraper_running=scraper_running,
        database_connected=db_connected
    )

@app.get("/health")
async def health():
    """Simple health check"""
    return {"status": "healthy"}

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
        "timestamp": "2026-02-02T02:46:14.212+05:00"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
