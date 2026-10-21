import time
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from ratelimit import limits, sleep_and_retry
from tenacity import retry, wait_fixed, wait_random_exponential, stop_after_attempt, retry_if_exception

def should_retry(exception):
    error_message = str(exception).lower()
    return "429" in error_message or "503" in error_message or "unavailable" in error_message or "exhausted" in error_message

# Memuat variabel rahasia
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inisialisasi Client
client = genai.Client(api_key=GEMINI_API_KEY)

# 1. BUAT BLUEPRINT SCHEMA JSON (Diselaraskan dengan Class Diagram)
class AnalisisIsu(BaseModel):
    id_postingan: str = Field(description="Salin persis id_postingan dari teks input")
    kategori: str = Field(description="Pilih satu: Lalu Lintas, Ekonomi dan Bisnis, Bencana Alam, Infrastruktur, Pariwisata, Layanan Publik, Sosial/Budaya, Politik Lokal")
    lokasi_terdeteksi: str = Field(description="Ekstrak nama jalan, desa, kecamatan, atau landmark di Bali. Jika tidak ada, isi 'Tidak Spesifik'")
    ringkasan_ai: str = Field(description="Buat 1-3 kalimat ringkasan padat tentang inti kejadiannya")
    validitas: str = Field(description="Isi 'Accept' jika isu publik valid, atau 'Reject' jika hanya iklan/spam/info wisata biasa/komersial")
    topik: str = Field(description="Judul singkat maksimal 5 kata dari kejadian tersebut")

class BatchAnalisisIsu(BaseModel):
    daftar_analisis: list[AnalisisIsu]

@sleep_and_retry
@limits(calls=3, period=60) 
@retry(
    wait=wait_fixed(35), 
    stop=stop_after_attempt(3),           
    retry=retry_if_exception(should_retry),
    reraise=True
)
def analyze_social_issue(cleaned_text):
    """
    Fungsi mengirim teks ke Gemini AI dengan jaminan 100% JSON Valid (Structured Output).
    """
    if not GEMINI_API_KEY:
        return {"status": "Error", "message": "API Key Gemini tidak ditemukan!"}

    gabungan_teks = ""
    for item in cleaned_text:
        id_post = item.get("id_postingan")
        teks = item.get("teks_vector", item.get("teks_bersih", ""))
        gabungan_teks += f"ID: {id_post} | Teks: {teks}\n---\n"
    
    prompt = f"""
    Kamu adalah asisten analis data berita untuk Sistem Analisis Isu Publik di wilayah Bali.
    Tugasmu adalah menganalisis teks laporan berita atau informasi mengenai isu publik berikut (berisi caption utama dan komentar warga).
    Abaikan kalimat promosi, tagar yang tidak relevan, atau komentar spam. Fokus pada isu berita lokal atau negara yang sedang terjadi, inti suatu kejadian atau keluhan warga.
    
    Teks Analisis: 
    "{gabungan_teks}"
    """

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=BatchAnalisisIsu,
            temperature=0.1 
        ),
    )
    
    hasil_json = json.loads(response.text)
    return {"status": "Success", "data_ai": hasil_json["daftar_analisis"]}
        


def process_all_clean_data(clean_data_list):
    data_akumulasi = []
    total_data = len(clean_data_list)
    data_baru_diterima = 0
    data_baru_ditolak = 0
    BATCH_SIZE = 10

    print(f"\n[FASE AI] Menerima {total_data} data bersih untuk dianalisis Gemini...")

    for i in range(0, total_data, BATCH_SIZE):
        batch_items = clean_data_list[i:i + BATCH_SIZE]
        print(f"\n[Batch {i//BATCH_SIZE + 1}] Meminta AI menganalisis postingan {i+1} sampai {min(i+BATCH_SIZE, total_data)}...")
        try:
            ai_result = analyze_social_issue(batch_items)

            if ai_result["status"] == "Success":
                # AI mengembalikan List. Kita jadikan dictionary berdasarkan ID agar mudah dipasangkan ke data asli
                map_hasil_ai = {str(res["id_postingan"]): res for res in ai_result["data_ai"]}
                
                # Masukkan kembali hasil AI ke variabel asli (seperti kodemu sebelumnya)
                for item in batch_items:
                    id_post = str(item.get("id_postingan"))
                    
                    if id_post in map_hasil_ai:
                        item["hasil_ai"] = map_hasil_ai[id_post]
                        validitas = item["hasil_ai"].get("validitas")
                        
                        print(f"   -> Topik: {item['hasil_ai'].get('topik')} | Lokasi: {item['hasil_ai'].get('lokasi_terdeteksi')} | Validitas: {validitas}")
                        
                        if validitas == "Accept":
                            data_akumulasi.append(item)
                            data_baru_diterima += 1
                            print("   -> ✅ Data lolos seleksi.")
                        else:
                            data_baru_ditolak += 1
                            print("   -> 🚫 Data di-cut (Reject).")
                    else:
                        print(f"   -> ⚠️ AI melewatkan ID {id_post} dalam balasannya.")
            else:
                print(f"   -> ⚠️ Gagal menganalisis batch ini: {ai_result['message']}")
                
        except Exception as e:
            error_msg = str(e).lower()
            print(f"   -> 🚨 Gagal memproses batch ini. Detail: {e}")
            
            # Antisipasi jika limit harian (RPD) habis, program berhenti aman
            if "quota" in error_msg or "429" in error_msg or "exhausted" in error_msg:
                print("\n🛑 [CRITICAL] Limit API harian tercapai!")
                print("🛑 Menghentikan proses AI sisa data agar tidak crash.")
                break
        # time.sleep(15) 


    return data_akumulasi 

if __name__ == "__main__":
    print("Memulai tes mesin AI Gemini...")
    file_input = "data_bersih_siap_ai.json"
    file_output = "data_hasil_ai.json"
    
    # 1. Membaca file JSON mentah
    with open(file_input, "r", encoding="utf-8") as f_in:
        raw_input_payload = json.load(f_in)
        
    # 2. PENTING: Ambil list yang ada di dalam key "data"
    # Menggunakan .get("data", []) agar aman jika key tersebut kosong
    clean_data_list = raw_input_payload.get("data", [])
        
    # 3. Jalankan fungsi utama menggunakan list data yang bersih
    hasil = process_all_clean_data(clean_data_list)
    
    # 4. Menyusun struktur output JSON untuk disimpan
    file_output_path = os.path.join(os.getcwd(), file_output)
    output_payload = {
        "status": "Success",
        "total_diterima": len(hasil),
        "total_ditolak": len(clean_data_list) - len(hasil),
        "total_database": len(hasil),
        "file_output": file_output_path,
        "data_hasil_ai": hasil
    }
    
    # 5. Simpan hasilnya ke file output
    with open(file_output_path, "w", encoding="utf-8") as f_out:
        json.dump(output_payload, f_out, ensure_ascii=False, indent=4)
    
    # 6. Cetak laporan akhir eksekusi
    print("\n=== Laporan Eksekusi Selesai ===")
    print(f"✅ Data baru yang LOLOS seleksi (Accept) : {output_payload['total_diterima']}")
    print(f"🗑️ Data baru yang DIBUANG (Reject)      : {output_payload['total_ditolak']}")
    print(f"📊 Total data valid di file output     : {output_payload['total_database']}")
    print(f"💾 Disimpan di: {output_payload['file_output']}")
