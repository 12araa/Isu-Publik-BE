import os
from dotenv import load_dotenv
from google import genai

# Memuat API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inisialisasi Client
client = genai.Client(api_key=GEMINI_API_KEY)

print("Mencari model Gemini yang tersedia untuk API Key ini...\n")

# Mengambil dan mencetak daftar model
try:
    for model in client.models.list():
        # Kita filter agar hanya menampilkan model yang mendukung fungsi "generateContent" (teks)
        if 'generateContent' in model.supported_actions:
            print(f"- {model.name}")
            
    print("\n✅ Pengecekan selesai!")
except Exception as e:
    print(f"❌ Terjadi kesalahan: {e}")