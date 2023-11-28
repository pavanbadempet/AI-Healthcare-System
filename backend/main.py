import sys
import os

# Add root directory to path to ensure modules can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress Warnings
import app_warnings

from fastapi import FastAPI
from . import models, database, auth, chat, explanation, prediction, report

from sqlalchemy import text  # Required for raw SQL execution

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

# Optimize: Add Indices & Schema Migration
try:
    with database.engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_health_records_timestamp ON health_records (timestamp)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_chat_logs_timestamp ON chat_logs (timestamp)"))
        
        # Schema Migration (Add Lifestyle Columns if missing)
        # Schema Migration (Add Lifestyle Columns if missing)
        # We must try each one independently. If one fails (already exists), the others must still run.
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN about_me TEXT"))
        except Exception: pass

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN diet TEXT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN activity_level TEXT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN sleep_hours FLOAT"))
        except Exception: pass
        
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN stress_level TEXT"))
        except Exception: pass
            
        conn.commit()
except Exception as e:
    print(f"Index/Schema Creation Warning: {e}")

app = FastAPI(title="AIO Healthcare System API")

# Enable Gzip Compression for Performance
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(chat.router, tags=["Chat & Records"])
app.include_router(prediction.router, tags=["AI Prediction"])
app.include_router(explanation.router) # New GenAI Explainer
app.include_router(report.router, tags=["Smart Lab Analyzer"])

@app.get("/")
def read_root():
    return {"message": "Healthcare System API is running"}
