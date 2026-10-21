from fastapi import Header, HTTPException
from firebase_admin import auth

def verifikasi_admin(authorization: str = Header(None)):
    """
    Memvalidasi JWT dari header secara kriptografi ke server Firebase.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Akses ditolak: Header Authorization tidak ditemukan.")
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Akses ditolak: Format token harus 'Bearer <token>'.")
    
    token = parts[1]
    
    try:
        decoded_token = auth.verify_id_token(token)
        
        return decoded_token
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail="Akses ditolak: Sesi telah berakhir. Silakan login ulang.")
    except auth.InvalidIdTokenError:
        raise HTTPException(status_code=401, detail="Akses ditolak: Token tidak valid, rusak, atau palsu.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kesalahan verifikasi otentikasi: {str(e)}")