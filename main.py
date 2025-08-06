from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.projects import router as projects_router
from src.api.crawl import router as crawl_router

app = FastAPI(title="AEO Booster API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects_router, prefix="/api")
app.include_router(crawl_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "AEO Booster API"}