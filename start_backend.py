#!/usr/bin/env python3
"""
Script to start the FastAPI backend server
"""
import uvicorn
import os

if __name__ == "__main__":
    # Create database tables if they don't exist
    print("Creating database tables...")
    from create_db import create_tables
    create_tables()
    
    print("Starting FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )