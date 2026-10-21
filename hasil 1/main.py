import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Mengimpor seluruh layanan yang sudah dibangun
from app.services.apify_service import fetch_raw_social_data
from app.utils.text_cleaner import process_raw_data
from app.services.gemini_service import process_all_clean_data
from app.services.maps_service import process_geocoding_for_ai_data
from app.services.qdrant_service import process_and_store_to_qdrant

def run_pipeline():
    print("="*60)
    print("🚀 MEMULAI PIPELINE SISTEM PEMETAAN ISU PUBLIK BALI")
    print("="*60)
    
    waktu_mulai = time.time()

    # ---------------------------------------------------------
    # FASE 1: Scraping Data Instagram (Apify)
    # ---------------------------------------------------------
    print("\n[FASE 1] Menarik data 24 jam terakhir dari media sosial...")
    # hasil_scraping = fetch_raw_social_data(["punapibalinews"])
    hasil_scraping = fetch_raw_social_data(["infodenpasar"])
    
    if hasil_scraping["status"] != "Success" or hasil_scraping["total_postingan_valid"] == 0:
        print("⚠️ Scraping dihentikan. Tidak ada data baru atau terjadi error.")
        print(f"Detail: {hasil_scraping.get('message', 'Data kosong')}")
        return # Menghentikan pipeline jika tidak ada berita baru
        
    # Menyimpan hasil mentah (opsional, untuk backup)
    with open("data_mentah_sementara.json", "w", encoding="utf-8") as f:
        json.dump(hasil_scraping["data"], f, ensure_ascii=False, indent=4)
        
    print(f"✅ Berhasil mengumpulkan {hasil_scraping['total_postingan_valid']} postingan valid.")

    # ---------------------------------------------------------
    # FASE 2: Pembersihan Teks (Text Preprocessing)
    # ---------------------------------------------------------
    print("\n[FASE 2] Membersihkan teks dan menghapus noise...")
    process_raw_data("data_mentah_sementara.json", "data_bersih_siap_ai.json")
    print("✅ Teks berhasil dibersihkan dan disiapkan untuk AI.")

    # ---------------------------------------------------------
    # FASE 3: Analisis Kecerdasan Buatan (Gemini 1.5 Flash)
    # ---------------------------------------------------------
    print("\n[FASE 3] Menganalisis Kategori, Lokasi, dan Validitas via Gemini AI...")
    hasil_ai = process_all_clean_data("data_bersih_siap_ai.json", "data_hasil_ai.json")
    
    if hasil_ai["status"] != "Success":
        print(f"❌ Pipeline terhenti di Fase AI: {hasil_ai['message']}")
        return
        
    print(f"✅ Analisis selesai. Data lolos (Accept): {hasil_ai.get('total_diterima', 0)}")

    # ---------------------------------------------------------
    # FASE 4: Pencarian Titik Koordinat (Mapbox Geocoding)
    # ---------------------------------------------------------
    print("\n[FASE 4] Mengonversi nama lokasi menjadi titik koordinat...")
    hasil_geocoding = process_geocoding_for_ai_data("data_hasil_ai.json", "data_final_siap_qdrant.json")
    
    if hasil_geocoding["status"] != "Success":
        print(f"❌ Pipeline terhenti di Fase Geocoding: {hasil_geocoding['message']}")
        return
        
    print(f"✅ Berhasil menemukan {hasil_geocoding['total_berhasil']} titik koordinat.")

    # ---------------------------------------------------------
    # FASE 5: Vektorisasi & Penyimpanan Semantik (Qdrant Cloud)
    # ---------------------------------------------------------
    print("\n[FASE 5] Mengolah vektor (Ollama) dan menyimpan ke Qdrant Cloud...")
    # Pastikan file yang dikirim ke Qdrant adalah file final yang sudah memiliki koordinat!
    hasil_qdrant = process_and_store_to_qdrant("data_final_siap_qdrant.json")
    
    if hasil_qdrant["status"] != "Success":
        print(f"❌ Pipeline terhenti di Fase Database: {hasil_qdrant['message']}")
        return

    # ---------------------------------------------------------
    # REKAPITULASI AKHIR
    # ---------------------------------------------------------
    durasi = round(time.time() - waktu_mulai, 2)
    print("\n" + "="*60)
    print("🎉 PIPELINE SELESAI DIEKSEKUSI!")
    print("="*60)
    print(f"⏱️ Total Waktu Eksekusi : {durasi} detik")
    print(f"📥 Isu Baru Masuk DB    : {hasil_qdrant['total_dimasukkan']}")
    print(f"🔄 Isu Diperbarui (Freq): {hasil_qdrant['total_duplikat']}")
    print("="*60)

if __name__ == "__main__":
    run_pipeline()