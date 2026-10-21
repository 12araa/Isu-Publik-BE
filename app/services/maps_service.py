import os
import json
import time
import requests
from dotenv import load_dotenv

# Memuat variabel rahasia
load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

def get_coordinates(location_name):
    """
    Mengubah nama lokasi menjadi koordinat Latitude dan Longitude menggunakan Mapbox.
    """
    # Jika AI gagal menemukan lokasi atau isinya hanya kata "Bali", abaikan pencarian
    if not location_name or location_name.lower() in ["tidak spesifik", "none", "", "bali"]:
        return None

    # Trik Cerdas: Tambahkan "Bali, Indonesia" agar Mapbox fokus mencari di area skripsimu
    query = f"{location_name}, Bali, Indonesia"
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{query}.json"
    
    params = {
        "access_token": MAPBOX_TOKEN,
        "limit": 1, # Kita hanya butuh 1 hasil tebakan yang paling relevan
        "types": "place,locality,neighborhood,address,poi"
    }

    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("features") and len(data["features"]) > 0:
                # Mapbox mengembalikan koordinat dalam urutan [Longitude, Latitude]
                koordinat = data["features"][0]["center"]
                
                return {
                    "longitude": koordinat[0],
                    "latitude": koordinat[1],
                    "nama_terdeteksi_mapbox": data["features"][0]["place_name"]
                }
        return None
        
    except Exception as e:
        print(f"⚠️ Error koneksi Mapbox: {str(e)}")
        return None

def process_geocoding_for_ai_data(input_filepath, output_filepath):
    """
    Fungsi untuk membaca data hasil sortir Gemini, lalu menambahkan atribut koordinat dari Mapbox.
    """
    print(f"Membaca data dari {input_filepath}...")
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            data_ai = json.load(f)
    except FileNotFoundError:
        return {"status": "Error", "message": f"File {input_filepath} tidak ditemukan!"}

    total_data = len(data_ai)
    berhasil_geocode = 0

    # Iterasi setiap berita yang sudah lolos filter Gemini
    for index, item in enumerate(data_ai, start=1):
        id_post = item.get("id_postingan")
        
        # Cek apakah objek hasil_ai tersedia
        if "hasil_ai" in item and item["hasil_ai"]:
            lokasi = item["hasil_ai"].get("lokasi_terdeteksi")
            
            print(f"[{index}/{total_data}] Mencari titik mapbox untuk: '{lokasi}'...")
            
            # Jika lokasi valid, cari koordinatnya
            if lokasi and lokasi.lower() != "tidak spesifik":
                koordinat = get_coordinates(lokasi)
                
                if koordinat:
                    item["koordinat"] = koordinat
                    berhasil_geocode += 1
                    print(f"   -> ✅ Titik ditemukan: {koordinat['latitude']}, {koordinat['longitude']}")
                else:
                    item["koordinat"] = None
                    print("   -> ⚠️ Mapbox tidak dapat menemukan titik pastinya (Unmapped).")
            else:
                item["koordinat"] = None
                print("   -> ⏭️ Diabaikan (Lokasi 'Tidak Spesifik').")
        
        # Berbeda dengan Google API, Mapbox sangat cepat dan limitnya besar.
        # Jeda 0.5 detik sudah sangat cukup dan aman.
        time.sleep(0.5)

    # Simpan kembali seluruh data beserta koordinatnya
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(data_ai, f, ensure_ascii=False, indent=4)

    return {
        "status": "Success",
        "total_diproses": total_data,
        "total_berhasil": berhasil_geocode,
        "file_output": output_filepath
    }

# Blok Pengujian Utama (White Box)
if __name__ == "__main__":
    print("=== Memulai Pipeline Geocoding Mapbox ===")
    
    # Path file input (Hasil AI) dan output (Siap Database)
    # Sesuaikan dengan lokasi foldermu jika diperlukan (misal: "../../data_hasil_ai.json")
    file_input = "data_hasil_ai.json"
    file_output = "data_final_siap_qdrant.json"
    
    hasil = process_geocoding_for_ai_data(file_input, file_output)
    
    if hasil["status"] == "Success":
        print("\n=== Laporan Eksekusi Geocoding Selesai ===")
        print(f"📊 Total berita diproses : {hasil['total_diproses']}")
        print(f"📍 Berhasil dapat titik  : {hasil['total_berhasil']}")
        print(f"💾 Disimpan di file      : {hasil['file_output']}")
    else:
        print(f"\n❌ Terjadi Kesalahan: {hasil['message']}")