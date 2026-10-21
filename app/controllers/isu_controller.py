import os
from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# 1. Inisialisasi Environment & Qdrant
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
COLLECTION_NAME = "isu_publik_bali"

# 2. Inisialisasi APIRouter (Pengganti @app)
router = APIRouter(
    prefix="/api",
    tags=["Isu Publik"]
)

@router.get("/isu-publik")
def get_semua_isu():
    try:
        # Menggunakan client.scroll() untuk mengambil semua data
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=200, 
            with_payload=True,
            with_vectors=False 
        )
        
        hasil = []
        for record in records:
            payload = record.payload
            
            # PENYELARASAN ATRIBUT SESUAI CLASS DIAGRAM & QDRANT TERBARU
            hasil.append({
                "id_qdrant": record.id, # ID unik dari Qdrant
                "id_isu": payload.get("id_isu", ""), # ID asli dari Instagram
                "kategori": payload.get("kategori", "Tidak diketahui"),
                "topik": payload.get("topik", "Tidak diketahui"),
                "lokasi_teks": payload.get("lokasi_teks", "Tidak spesifik"),
                "koordinat": payload.get("koordinat", None), 
                "ringkasan_ai": payload.get("ringkasan_ai", ""), # Diubah dari ringkasan_kasus
                "teks_asli": payload.get("teks_asli", ""),
                "skor_viralitas": payload.get("skor_viralitas", 0),
                "timestamp": payload.get("timestamp", ""),
                "is_archived": payload.get("is_archived", False),
                "url_postingan": payload.get("url_postingan", ""),
                "url_gambar": payload.get("url_gambar", ""),
                "interaksi": {
                    "likes": payload.get("jumlah_like", 0),
                    "comments": payload.get("jumlah_komentar", 0),
                    "frekuensi": payload.get("frekuensi_laporan", 1)
                }
            })
        
        # Urutkan data secara otomatis dari skor viralitas tertinggi (darurat) ke terendah
        hasil_diurutkan = sorted(hasil, key=lambda x: x["skor_viralitas"], reverse=True)

        if hasil_diurutkan:
            skor_maksimal = hasil_diurutkan[0]["skor_viralitas"]
            
            for item in hasil_diurutkan:
                if skor_maksimal > 0:
                    persentase = (item["skor_viralitas"] / skor_maksimal) * 100
                    item["skor_viralitas"] = round(persentase, 1)
                else:
                    item["skor_viralitas"] = 0.0
        
        return {
            "status": "success",
            "total_titik": len(hasil_diurutkan),
            "data": hasil_diurutkan
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan pada server: {str(e)}")
        