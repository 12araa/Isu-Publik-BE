import os
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
# Dapatkan kunci ini dari Project Settings di Firebase Console milikmu
FIREBASE_WEB_API_KEY = os.getenv("FIREBASE_WEB_API_KEY")

# Inisialisasi APIRouter (Pengganti Controller MVC)
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

# Skema data yang diharapkan dari Vue.js
class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login")
def login_admin(kredensial: LoginRequest):
    if not FIREBASE_WEB_API_KEY:
        raise HTTPException(status_code=500, detail="Firebase Web API Key belum diatur di file .env")

    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"
        payload = {
            "email": kredensial.email,
            "password": kredensial.password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        data = response.json()

        if "error" in data:
            pesan_error = data["error"]["message"]
            raise HTTPException(status_code=401, detail=f"Kredensial tidak valid: {pesan_error}")

        return {
            "status": "success",
            "message": "Login berhasil",
            "session_token": data["idToken"],
            "admin_id": data["localId"]
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Gagal terhubung ke Firebase: {str(e)}")