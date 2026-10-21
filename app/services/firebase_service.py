import firebase_admin
from firebase_admin import credentials
import os

# Sesuaikan dengan nama file JSON yang kamu simpan di root folder
CREDENTIAL_PATH = "firebase-service-account.json"

def init_firebase():
    """Menghubungkan FastAPI dengan server Firebase menggunakan Service Account Key."""
    # Mencegah inisialisasi ganda jika server di-reload
    if not firebase_admin._apps:
        try:
            if not os.path.exists(CREDENTIAL_PATH):
                print(f"⚠️ PERINGATAN: File kunci {CREDENTIAL_PATH} tidak ditemukan!")
                return
                
            cred = credentials.Certificate(CREDENTIAL_PATH)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK berhasil diinisialisasi dan siap memverifikasi token.")
        except Exception as e:
            print(f"⚠️ Gagal inisialisasi Firebase: {e}")