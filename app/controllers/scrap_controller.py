from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List

from app.utils.auth_middleware import verifikasi_admin

# Import semua service (Pastikan fungsi-fungsi di dalam file ini sudah 
# menggunakan perintah "return data", bukan "json.dump(file)")
from app.services import apify_service
from app.services import gemini_service
from app.services import qdrant_service
from app.utils import text_cleaner

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

status_sinkronisasi = {"pesan": "Memulai inisialisasi..."}

@router.get("/sumber-akun")
def daftar_sumber_akun():
    return {
        "status": "success",
        "data": {
            "instagram": [
                {"id": "infobadung_id", "nama": "infobadung_id"},
                {"id": "badungpunyacerita", "nama": "badungpunyacerita"},
                {"id": "infobadungbali", "nama": "infobadungbali"},
                {"id": "infobadungcom", "nama": "infobadungcom"},
                {"id": "tabanan_update", "nama": "tabanan_update"},
                {"id": "info_baturiti", "nama": "info_baturiti"},
                {"id": "tabanan.viral", "nama": "tabanan.viral"},
                {"id": "tabananinfo_", "nama": "tabananinfo_"},
                {"id": "pvnapitabanan", "nama": "pvnapitabanan"},
                {"id": "jembrana.now", "nama": "jembrana.now"},
                {"id": "infojembrana", "nama": "infojembrana"},
                {"id": "mediajembrana", "nama": "mediajembrana"},
                {"id": "hellojembrana", "nama": "hellojembrana"},
                {"id": "infosingaraja_news", "nama": "infosingaraja_news"},
                {"id": "bulelengtoday", "nama": "bulelengtoday"},
                {"id": "bulelengterkini", "nama": "bulelengterkini"},
                {"id": "radarbuleleng", "nama": "radarbuleleng"},
                {"id": "bulelengsatu", "nama": "bulelengsatu"},
                {"id": "bangliterkini", "nama": "bangliterkini"},
                {"id": "infobatur", "nama": "infobatur"},
                {"id": "banglidaily", "nama": "banglidaily"},
                {"id": "bangliupdate", "nama": "bangliupdate"},
                {"id": "gianyardaily", "nama": "gianyardaily"},
                {"id": "info_tegallalang", "nama": "info_tegallalang"},
                {"id": "helloubud", "nama": "helloubud"},
                {"id": "punapigianyar", "nama": "punapigianyar"},
                {"id": "infoklungkung_", "nama": "infoklungkung_"},
                {"id": "kabarklungkung", "nama": "kabarklungkung"},
                {"id": "klungkungnews", "nama": "klungkungnews"},
                {"id": "klungklung.info", "nama": "klungklung.info"},
                {"id": "kabarkarangasem", "nama": "kabarkarangasem"},
                {"id": "karangasemcerita", "nama": "karangasemcerita"},
                {"id": "infoamlapura", "nama": "infoamlapura"},
                {"id": "karangasemterkini", "nama": "karangasemterkini"},
                {"id": "denpasar.viral", "nama": "denpasar.viral"},
                {"id": "denpasar.now", "nama": "denpasar.now"},
                {"id": "denpasarterkini.id", "nama": "denpasarterkini.id"},
                {"id": "denpasarcerita", "nama": "denpasarcerita"},
                {"id": "punapibalinews", "nama": "punapibalinews"},
                {"id": "infobali.viral", "nama": "infobali.viral"},
                {"id": "balitoday_", "nama": "balitoday_"},
                {"id": "therakyatbali", "nama": "therakyatbali"}
            ],
            "facebook": [
                {"id": "https://www.facebook.com/share/g/1DVvcuXGXz/", "nama": "Grup Bali Sharing Information"},
                {"id": "https://www.facebook.com/share/g/1McS231CHA/", "nama": "Grup Info Bali Terkini"},
                {"id": "https://www.facebook.com/share/g/1DqUHgWLWE/", "nama": "Grup Info Seputar Bali"},
                {"id": "https://www.facebook.com/share/g/1FMRyqUdGq/", "nama": "Grup Suara Denpasar"}
            ]
        }
    }

class PermintaanScraping(BaseModel):
    target_akun: List[str] 

@router.get("/status-fetch", tags=["Admin"])
def cek_status_sinkronisasi():
    return status_sinkronisasi

# --- 2. CONTROLLER UTAMA ---
@router.post("/manual-fetch", dependencies=[Depends(verifikasi_admin)])
def jalankan_manual_fetch(payload: PermintaanScraping):
    global status_sinkronisasi

    # Validasi awal: Cegah Admin menekan tombol jika tidak ada URL yang dipilih
    if not payload.target_akun:
        raise HTTPException(status_code=400, detail="Pilih minimal 1 sumber target media sosial!")

    try:
        print(f"Memulai pemilahan untuk {len(payload.target_akun)} target akun...")
        status_sinkronisasi["pesan"] = "Menghubungi Apify & menarik data dari Sosmed..."
        # 1. PISAHKAN TARGET INSTAGRAM DAN FACEBOOK
        target_ig = []
        target_fb = []
        for akun in payload.target_akun:
            if "facebook.com" in akun:
                target_fb.append(akun)
            else:
                target_ig.append(akun)

        list_postingan_gabungan = []

        # 2. TARIK DATA INSTAGRAM (Jika ada yang dicentang)
        if target_ig:
            status_sinkronisasi["pesan"] = f"Menarik data dari {len(target_ig)} akun Instagram..."
            print(f"Menjalankan scraper untuk {len(target_ig)} akun Instagram...")
            # Menggunakan nama fungsi yang sesuai dengan apify_service.py
            hasil_ig = apify_service.fetch_raw_social_data(target_akun=target_ig)
            
            if hasil_ig.get("status") == "Success":
                list_postingan_gabungan.extend(hasil_ig.get("data", []))
            else:
                print(f"⚠️ Gagal menarik IG: {hasil_ig.get('message')}")

        # 3. TARIK DATA FACEBOOK (Jika ada yang dicentang)
        if target_fb:
            status_sinkronisasi["pesan"] = f"Menarik data dari {len(target_fb)} grup Facebook..."
            print(f"Menjalankan scraper untuk {len(target_fb)} grup Facebook...")
            # Buat fungsi baru ini di apify_service milikmu khusus untuk Actor FB
            hasil_fb = apify_service.scrape_facebook_groups(urls=target_fb)

            if hasil_fb.get("status") == "Success":
                list_postingan_gabungan.extend(hasil_fb.get("data", []))
            else:
                print(f"⚠️ Gagal menarik FB: {hasil_fb.get('message')}")

        # 4. PASTIKAN ADA DATA YANG DITARIK
        if not list_postingan_gabungan:
            return {"status": "warning", "message": "Tidak ada berita baru yang ditemukan di akun target."}

        print(f"Total postingan mentah terkumpul: {len(list_postingan_gabungan)}")

        print("🧹 Memulai proses pembersihan teks (Text Cleaner)...")
        status_sinkronisasi["pesan"] = f"Menyaring dan membersihkan {len(list_postingan_gabungan)} data dari Iklan/Spam..."
        hasil_cleaner = text_cleaner.process_raw_data(list_postingan_gabungan)
        data_bersih = hasil_cleaner.get("data", [])
        print(f"📊 Hasil pembersihan: {len(data_bersih)} dari {len(list_postingan_gabungan)} postingan lolos seleksi.")

        if not data_bersih:
            print("⚠️ Semua postingan dibuang oleh cleaner (terdeteksi iklan/spam).")
            return {"status": "warning", "message": "Berhasil ditarik, tapi semua postingan dibuang karena terdeteksi sebagai Iklan/Spam/Tanpa Teks."}

        # TAHAP PENGECEKAN DUPLIKAT (QDRANT)
        print("🔍 Memeriksa duplikasi ID di Qdrant Database...")
        status_sinkronisasi["pesan"] = "Mengecek duplikasi data di Qdrant Vector DB..."
        data_siap_ai = []
        for item in data_bersih:
            id_post = item.get("id_postingan")
            
            if qdrant_service.cek_id_sudah_ada(id_post):
                print(f"⏭️ ID {id_post} sudah ada di Qdrant. Melewati proses AI.")
            else:
                data_siap_ai.append(item)
                
        if not data_siap_ai:
            print("✅ Semua data yang ditarik sudah ada di database.")
            return {"status": "success", "message": "Semua data yang ditarik sudah ada di database."}
        
        # TAHAP 3: Analisis Semantik dengan Gemini AI
        print(f"🤖 Mengirim {len(data_siap_ai)} data ke Gemini AI...")
        status_sinkronisasi["pesan"] = "Menganalisis topik dan sentimen menggunakan Gemini AI..."
        data_hasil_ai = gemini_service.process_all_clean_data(data_siap_ai)
        
        # TAHAP 4: Vektorisasi (Ollama) & Penyimpanan ke Qdrant
        print("📦 Memproses embedding Ollama dan menyimpan ke Qdrant Cloud...")
        status_sinkronisasi["pesan"] = "Menyimpan hasil ke database Qdrant..."
        hasil_qdrant = qdrant_service.process_and_store_to_qdrant(data_hasil_ai)

        return {
            "status": "success",
            "message": "Sinkronisasi berhasil!",
            "detail_statistik": hasil_qdrant
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Terjadi kesalahan pada Pipeline: {str(e)}")