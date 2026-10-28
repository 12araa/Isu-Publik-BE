import os
import sys
import json
import uuid
import ollama
from datetime import datetime 
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

# 1. Panggil fungsi rumus dari file calculator
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.utils.virality_calculator import hitung_skor_viralitas

# Memuat variabel rahasia
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# INISIALISASI QDRANT CLOUD
client = QdrantClient(
    url=QDRANT_URL, 
    api_key=QDRANT_API_KEY
)
COLLECTION_NAME = "isu_publik_bali"

def setup_qdrant():
    """Fungsi untuk membuat koleksi di Qdrant Cloud jika belum ada"""
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=768, 
                distance=models.Distance.COSINE
            )
        )
        print(f"✅ Koleksi '{COLLECTION_NAME}' berhasil dibuat di Qdrant Cloud.")

def get_embedding(text):
    """Fungsi untuk mengubah teks menjadi vektor menggunakan Ollama lokal"""
    try:
        response = ollama.embeddings(model='nomic-embed-text', prompt=text)
        return response['embedding']
    except Exception as e:
        print(f"⚠️ Error Ollama: {str(e)}")
        return None

def process_and_store_to_qdrant(data_final_list):
    setup_qdrant()

    total_dimasukkan = 0
    total_duplikat_makna = 0

    for index, item in enumerate(data_final_list, start=1):
        ringkasan = item["hasil_ai"].get("ringkasan_ai", item["hasil_ai"].get("ringkasan_kasus", ""))
        kategori = item["hasil_ai"].get("kategori", "")
        topik_baru = item["hasil_ai"].get("topik", "Tanpa Judul")
        lokasi = item["hasil_ai"].get("lokasi_terdeteksi", "")
        
        # Ambil data statistik dari item
        jumlah_like = item.get("jumlah_like", 0)
        jumlah_komentar = item.get("jumlah_komentar", 0)
        
        # PERBAIKAN 1: Tambahkan topik dan lokasi ke teks vektor agar tidak salah cocok (False Positive)
        teks_untuk_vektor = f"Topik: {topik_baru}. Kategori: {kategori}. Lokasi: {lokasi}. {ringkasan}"
        print(f"\n[{index}/{len(data_final_list)}] Mengonversi Vektor: {teks_untuk_vektor[:60]}...")
        
        vektor_baru = get_embedding(teks_untuk_vektor)
        if not vektor_baru:
            continue

        response_qdrant = client.query_points(
            collection_name=COLLECTION_NAME,
            query=vektor_baru,
            limit=1,
            score_threshold=0.88 
        )

        search_result = response_qdrant.points

        # LOGIKA SMART INSERTION & UPDATE SKOR
        if search_result:
            data_mirip = search_result[0]
            print(f"   -> ⚠️ Ditemukan isu serupa di Cloud (Skor: {data_mirip.score:.2f})")
            
            ringkasan_lama = data_mirip.payload.get('ringkasan_ai', data_mirip.payload.get('ringkasan_kasus', ''))
            print(f"      [Berita Baru] : {ringkasan[:80]}...")
            print(f"      [Berita Lama] : {ringkasan_lama[:80]}...")
            
            # Akumulasi frekuensi, likes, dan komentar (Lama + Baru)
            frekuensi_sekarang = data_mirip.payload.get('frekuensi_laporan', 1)
            frekuensi_baru = frekuensi_sekarang + 1
            
            like_lama = data_mirip.payload.get('jumlah_like', 0)
            komen_lama = data_mirip.payload.get('jumlah_komentar', 0)
            
            total_like_gabungan = like_lama + jumlah_like
            total_komen_gabungan = komen_lama + jumlah_komentar
            
            # Hitung ulang skor dengan total interaksi gabungan dan frekuensi yang naik
            skor_viralitas_baru = hitung_skor_viralitas(total_like_gabungan, total_komen_gabungan, frekuensi_baru)
            
            # Penggabungan URL Sumber
            url_lama = data_mirip.payload.get('url_postingan', [])
            if isinstance(url_lama, str):
                url_lama = [url_lama] if url_lama else []
                
            url_baru = item.get("url_asli", "")
            if url_baru and url_baru not in url_lama:
                url_lama.append(url_baru)
                
            topik_tersimpan = data_mirip.payload.get('topik') or topik_baru
            
            # Update nilai ke Qdrant
            client.set_payload(
                collection_name=COLLECTION_NAME,
                payload={
                    "topik": topik_tersimpan,
                    "frekuensi_laporan": frekuensi_baru,
                    "jumlah_like": total_like_gabungan,
                    "jumlah_komentar": total_komen_gabungan,
                    "skor_viralitas": skor_viralitas_baru,
                    "url_postingan": url_lama
                },
                points=[data_mirip.id]
            )
            print(f"   -> 📈 Frekuensi laporan di-update menjadi: {frekuensi_baru} | Skor: {skor_viralitas_baru}")
            
            total_duplikat_makna += 1
        else:
            print("   -> ✅ Isu baru! Mengunggah ke Qdrant Cloud...")
            
            frekuensi_awal = 1
            skor_viralitas = hitung_skor_viralitas(jumlah_like, jumlah_komentar, frekuensi_awal)
            
            qdrant_id = str(uuid.uuid4())
            
            payload = {
                "id_isu": item.get("id_postingan"), 
                "teks_asli": item.get("caption_bersih", item.get("teks_bersih", "")),
                "ringkasan_ai": ringkasan, 
                "topik": topik_baru,
                "kategori": kategori,
                "skor_viralitas": skor_viralitas,
                "koordinat": item.get("koordinat"), 
                "timestamp": datetime.now().isoformat(), 
                "is_archived": False,
                "frekuensi_laporan": frekuensi_awal,
                "url_postingan": [item.get("url_asli", "")], 
                "url_gambar": item.get("url_gambar", ""),
                "jumlah_like": jumlah_like,
                "jumlah_komentar": jumlah_komentar,
                "lokasi_teks": lokasi
            }
            
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    models.PointStruct(
                        id=qdrant_id,
                        vector=vektor_baru,
                        payload=payload
                    )
                ]
            )
            total_dimasukkan += 1

    return {
        "status": "Success",
        "total_dimasukkan": total_dimasukkan,
        "total_duplikat": total_duplikat_makna,
        "total_diproses": len(data_final_list)
    }

def cek_id_sudah_ada(id_postingan: str) -> bool:
    """Mengecek apakah ID asli dari Instagram sudah ada di payload Qdrant."""
    try:
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="id_isu",
                        match=models.MatchValue(value=id_postingan)
                    )
                ]
            ),
            limit=1,
            with_payload=False,
            with_vectors=False
        )
        records, _ = response
        return len(records) > 0
    except Exception:
        return False



def get_semua_isu(limit=100):
    """
    Mengambil data isu terbaru dari Qdrant Cloud untuk ditampilkan di Frontend.
    """
    try:
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=limit,
            with_payload=True,
            with_vectors=False 
        )
        
        records, next_page_offset = response
        
        data_bersih = []
        for record in records:
            payload = record.payload
            payload["qdrant_id"] = record.id 
            data_bersih.append(payload)
            
        return data_bersih
        
    except Exception as e:
        print(f"⚠️ Gagal mengambil data dari Qdrant: {str(e)}")
        raise e

def update_payload_isu(id_vektor: str, topik_baru: str, teks_baru: str, kategori_baru: str, status_arsip: bool):
    try:
        client.set_payload(
            collection_name=COLLECTION_NAME,
            payload={
                "ringkasan_ai": teks_baru,
                "kategori": kategori_baru,
                "is_archived": status_arsip
            },
            points=[id_vektor]
        )
        return True
    except Exception as e:
        print(f"⚠️ Gagal memperbarui payload isu: {str(e)}")
        return False

    
if __name__ == "__main__":
    print("=== Memulai Sinkronisasi Qdrant Cloud ===")
    
    file_input = "data_hasil_ai.json" 
    hasil = process_and_store_to_qdrant(file_input)
    
    if hasil["status"] == "Success":
        print("\n=== Laporan Qdrant Selesai ===")
        print(f"✅ Isu BARU berhasil diunggah   : {hasil['total_dimasukkan']}")
        print(f"🔄 Isu SERUPA (Duplikat)        : {hasil['total_duplikat']}")
        print(f"🌐 Silakan cek Dashboard Qdrant Cloud milikmu!")
    else:
        print(f"\n❌ Terjadi Kesalahan: {hasil['message']}")