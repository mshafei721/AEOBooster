#!/usr/bin/env python3
"""
Script to create database tables
"""
from src.models.database import engine, Base
from src.models.project import User, Project

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()