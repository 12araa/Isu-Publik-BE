import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from dotenv import load_dotenv

from app.controllers import auth_controller, isu_controller
from app.services.firebase_service import init_firebase
from app.controllers import scrap_controller
from app.controllers import edit_controller

load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

app = FastAPI(title="API Analisis Isu Bali")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_firebase()

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
COLLECTION_NAME = "isu_publik_bali"

app.include_router(auth_controller.router)
app.include_router(isu_controller.router)  
app.include_router(scrap_controller.router)
app.include_router(edit_controller.router) 


@app.get("/")
def root():
    return {"message": "Server API Analisis Isu Bali Berjalan Normal!"}