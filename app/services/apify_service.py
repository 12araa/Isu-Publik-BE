import os
import json
from dotenv import load_dotenv
from apify_client import ApifyClient

# Memuat variabel rahasia
load_dotenv()
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
client = ApifyClient(APIFY_TOKEN)

def fetch_raw_social_data(target_akun: list):
    """Fungsi menarik data Instagram dan menyeragamkan formatnya."""
    if not APIFY_TOKEN:
        return {"status": "Error", "message": "API Token Apify tidak ditemukan di file .env!"}
    
    if not target_akun:
        return {"status": "Error", "message": "Target akun tidak boleh kosong!"}

    print(f"Memicu robot Apify IG untuk target: {', '.join(target_akun)}...")
    url_lengkap = [f"https://www.instagram.com/{akun}/" for akun in target_akun]
    
    run_input = {
        "directUrls": url_lengkap,
        "onlyPostsNewerThan": "1 day",
        "resultsLimit": 25,
        "resultsType": "posts"
    }
    
    try:
        run = client.actor("apify/instagram-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        postingan_valid = []
        for item in dataset_items:
            # Pastikan caption ada dan tidak kosong
            if "caption" in item and item.get("caption"):
                # PENYERAGAMAN FORMAT (Sama dengan FB)
                postingan_valid.append({
                    "id_postingan": item.get("id"),
                    "sumber": f"Instagram @{item.get('ownerUsername', 'unknown')}",
                    "url_post": item.get("url", ""),
                    "caption": item.get("caption", ""),
                    "waktu_post": item.get("timestamp", ""),
                    "lokasi": item.get("locationName", ""),
                    "url_gambar": item.get("displayUrl", ""),
                    "tipe_media": item.get("type", "Unknown"),
                    "jumlah_like": item.get("likesCount", 0),
                    "jumlah_komentar": item.get("commentsCount", 0),
                    "latestComments": item.get("latestComments", [])
                })
        
        return {
            "status": "Success",
            "total_data_mentah": len(dataset_items),
            "total_postingan_valid": len(postingan_valid),
            "data": postingan_valid
        }
        
    except Exception as e:
        return {"status": "Error", "message": str(e)}


def scrape_facebook_groups(urls: list):
    """Fungsi menarik data Facebook dan menyeragamkan formatnya."""
    if not APIFY_TOKEN:
        return {"status": "Error", "message": "API Token Apify tidak ditemukan di file .env!"}

    print(f"Memicu robot Apify FB untuk {len(urls)} grup...")
    
    run_input = {
        "startUrls": [{"url": url} for url in urls],
        "resultsLimit": 10, 
    }

    try:
        run = client.actor("apify/facebook-groups-scraper").call(run_input=run_input)
        
        hasil_fb = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if "text" in item and item.get("text"):
                # PENYERAGAMAN FORMAT (Sama dengan IG)
                hasil_fb.append({
                    "id_postingan": item.get("id"),
                    "sumber": "Facebook",
                    "url_post": item.get("postUrl", ""),
                    "caption": item.get("text", ""),
                    "waktu_post": item.get("date", ""),
                    "lokasi": "", 
                    "url_gambar": item.get("media", [{"url": ""}])[0].get("url", "") if item.get("media") else "",
                    "tipe_media": "Post",
                    "jumlah_like": item.get("likes", 0), 
                    "jumlah_komentar": item.get("comments", 0),
                    "latestComments": []
                })

        return {
            "status": "Success",
            "total_postingan_valid": len(hasil_fb),
            "data": hasil_fb
        }
    
    except Exception as e:
        return {"status": "Error", "message": str(e)}


# Blok pengujian (White Box)
if __name__ == "__main__":
    print("Memulai tes ekstraksi Apify...")
    
    # Tes Instagram
    akun_test = ["punapibalinews"]
    hasil_ig = fetch_raw_social_data(target_akun=akun_test)
    
    if hasil_ig["status"] == "Success":
        print(f"✅ Berhasil menarik {hasil_ig['total_postingan_valid']} data IG yang seragam.")
        
        if hasil_ig["total_postingan_valid"] > 0:
            with open("data_mentah_sementara.json", "w", encoding="utf-8") as file:
                json.dump(hasil_ig["data"], file, ensure_ascii=False, indent=4)
            print("💾 File JSON berhasil diperbarui.")
    else:
        print(f"❌ Gagal IG: {hasil_ig['message']}")