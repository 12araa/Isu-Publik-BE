import os
import re
import json

def clean_text(text):
    if not text:
        return ""
    
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_commercial_ad(text):
    ad_keywords = [
        'promo', 'diskon', 'harga murah', 'tebus murah', 'sale', 'flash sale', 
        'ready stock', 'open po', 'pre order', 'klik link', 'link di bio'
    ]
    loker_keywords = [
        'lowongan kerja', 'info loker', 'dibutuhkan segera', 'posisi yang dibutuhkan'
    ]
    judol_keywords = [
        'slot gacor', 'link gacor', 'pola gacor', 'pinjaman online', 'pinjol', 
        'dana cepat', 'cair hitungan menit'
    ]
    ga_keywords = [
        'giveaway', 'gratis ongkir', 'klaim gratis', 'syarat dan ketentuan', 
        's&k berlaku', 'tag teman', 'tag 3 teman', 'pemenang undian'
    ]

    text_lower = text.lower()
    for word in ad_keywords + loker_keywords + judol_keywords + ga_keywords:
        if re.search(rf'\b{word}\b', text_lower):
            return True
    return False

def process_raw_data(raw_data_list):
    processed_data = []
    id_sementara = set()  
    
    for i, item in enumerate(raw_data_list):
        # 1. Penarikan Kunci Utama yang Benar
        id_postingan = item.get("url_post") or item.get("id") or item.get("url")
        teks_mentah = item.get("teks") or item.get("caption", "")
        
        if not id_postingan:
            continue
        
        if id_postingan in id_sementara:
            continue
        
        # 2. Filter Iklan (Jika ada data valid yang hilang, berarti kata kunci iklanmu terlalu ketat)
        if is_commercial_ad(teks_mentah):
            continue 
            
        # 3. Penarikan Kunci Komentar yang Benar
        komentar_mentah = item.get("komentar_mentah") or item.get("latestComments", [])
        komentar_list = []
        if komentar_mentah:
            for comment in komentar_mentah: 
                teks_komen = comment.get("text", "")
                if teks_komen and not re.match(r'^(@\w+\s*)+$', teks_komen):
                    komentar_list.append(clean_text(teks_komen))
        
        caption_bersih = clean_text(teks_mentah)
        
        if caption_bersih:
            kumpulan_komentar = " | ".join(komentar_list)
            teks_untuk_vector = f"{caption_bersih}\nKomentar netizen: {kumpulan_komentar}" if kumpulan_komentar else caption_bersih

            # 4. Penyimpanan dengan Kunci yang Tepat (Gunakan variabel id_postingan yang sudah ditangkap di atas)
            processed_data.append({
                "id_postingan": id_postingan, 
                "sumber": item.get("sumber", "Unknown"),
                "timestamp": item.get("waktu_post") or item.get("timestamp", ""), 
                "lokasi": item.get("lokasi") or item.get("locationName", ""), 
                "url_asli": id_postingan,
                "url_gambar": item.get("url_gambar") or item.get("displayUrl", ""), 
                "tipe_media": item.get("tipe_media") or item.get("type", "Unknown"),
                "caption_bersih": caption_bersih,
                "komentar_teratas": kumpulan_komentar,
                "teks_vector": teks_untuk_vector,
                "jumlah_like": item.get("jumlah_like") or item.get("likesCount", 0),
                "jumlah_komentar": item.get("jumlah_komentar") or item.get("commentsCount", 0)
            })

            id_sementara.add(id_postingan)

    return {
        "status": "Success", 
        "data": processed_data,
        "total_mentah": len(raw_data_list), 
        "total_bersih": len(processed_data)
    }

if __name__ == "__main__":
    print("Memulai tes lokal Preprocessing Teks...")
    file_input = "data_mentah_sementara.json"
    file_output = "data_bersih_siap_ai.json"

    with open(file_input, "r", encoding="utf-8") as f_in:
        raw_input_data = json.load(f_in)
    hasil = process_raw_data(raw_input_data)
    file_output_path = os.path.join(os.getcwd(), file_output)

    with open(file_output_path, "w", encoding="utf-8") as f_out:
        json.dump(hasil, f_out, ensure_ascii=False, indent=4)
    
    if hasil["status"] == "Success":
        print("✅ Tes Berhasil!")
    else:
        print(f"❌ Error: {hasil['message']}")


# import os
# import re
# import json

# def clean_text(text):
#     if not text:
#         return ""
    
#     text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
#     text = re.sub(r'@\w+', '', text)
#     text = re.sub(r'\s+', ' ', text).strip()
#     return text

# def is_commercial_ad(text):
#     ad_keywords = [
#         'promo', 'diskon', 'harga murah', 'tebus murah', 'sale', 'flash sale', 
#         'ready stock', 'open po', 'pre order', 'klik link', 'link di bio'
#     ]
#     loker_keywords = [
#         'lowongan kerja', 'info loker', 'dibutuhkan segera', 'posisi yang dibutuhkan'
#     ]
#     judol_keywords = [
#         'slot gacor', 'link gacor', 'pola gacor', 'pinjaman online', 'pinjol', 
#         'dana cepat', 'cair hitungan menit'
#     ]
#     ga_keywords = [
#         'giveaway', 'gratis ongkir', 'klaim gratis', 'syarat dan ketentuan', 
#         's&k berlaku', 'tag teman', 'tag 3 teman', 'pemenang undian'
#     ]

#     text_lower = text.lower()
#     for word in ad_keywords + loker_keywords + judol_keywords + ga_keywords:
#         if re.search(rf'\b{word}\b', text_lower):
#             return True
#     return False

# def process_raw_data(raw_data_list):
#     processed_data = []
#     id_sementara = set()  
    
#     for i, item in enumerate(raw_data_list):
#         # 1. Penarikan Kunci Utama yang Benar
#         id_postingan = item.get("url_post") or item.get("id") or item.get("url")
#         teks_mentah = item.get("teks") or item.get("caption", "")
        
#         if not id_postingan:
#             continue
        
#         if id_postingan in id_sementara:
#             continue
        
#         # 2. Filter Iklan (Jika ada data valid yang hilang, berarti kata kunci iklanmu terlalu ketat)
#         if is_commercial_ad(teks_mentah):
#             continue 
            
#         # 3. Penarikan Kunci Komentar yang Benar
#         komentar_mentah = item.get("komentar_mentah") or item.get("latestComments", [])
#         komentar_list = []
#         if komentar_mentah:
#             for comment in komentar_mentah: 
#                 teks_komen = comment.get("text", "")
#                 if teks_komen and not re.match(r'^(@\w+\s*)+$', teks_komen):
#                     komentar_list.append(clean_text(teks_komen))
        
#         caption_bersih = clean_text(teks_mentah)
        
#         if caption_bersih:
#             kumpulan_komentar = " | ".join(komentar_list)
#             teks_untuk_vector = f"{caption_bersih}\nKomentar netizen: {kumpulan_komentar}" if kumpulan_komentar else caption_bersih

#             # 4. Penyimpanan dengan Kunci yang Tepat (Gunakan variabel id_postingan yang sudah ditangkap di atas)
#             processed_data.append({
#                 "id_postingan": id_postingan, 
#                 "sumber": item.get("sumber", "Unknown"),
#                 "timestamp": item.get("waktu_post") or item.get("timestamp", ""), 
#                 "lokasi": item.get("lokasi") or item.get("locationName", ""), 
#                 "url_asli": id_postingan,
#                 "url_gambar": item.get("url_gambar") or item.get("displayUrl", ""), 
#                 "tipe_media": item.get("tipe_media") or item.get("type", "Unknown"),
#                 "caption_bersih": caption_bersih,
#                 "komentar_teratas": kumpulan_komentar,
#                 "teks_vector": teks_untuk_vector,
#                 "jumlah_like": item.get("jumlah_like") or item.get("likesCount", 0),
#                 "jumlah_komentar": item.get("jumlah_komentar") or item.get("commentsCount", 0)
#             })

#             id_sementara.add(id_postingan)

#     return {
#         "status": "Success", 
#         "data": processed_data,
#         "total_mentah": len(raw_data_list), 
#         "total_bersih": len(processed_data)
#     }