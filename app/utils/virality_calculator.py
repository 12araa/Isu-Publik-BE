# Lokasi file: app/utils/virality_calculator.py

def hitung_skor_viralitas(likes: int, comments: int, frekuensi_laporan: int) -> float:
    """
    Kalkulator terpisah untuk menghitung skor viralitas.
    Semua ubahan bobot/rumus skripsi dilakukan di file ini, bukan di file Qdrant.
    """
    # Mencegah angka negatif dari error scraping
    likes = max(0, likes)
    comments = max(0, comments)
    frekuensi_laporan = max(1, frekuensi_laporan)

    # Bobot variabel (Bisa kamu sesuaikan untuk kebutuhan Bab 3/Bab 4 Skripsi)
    BOBOT_LIKE = 1.0
    BOBOT_KOMENTAR = 3.0
    BOBOT_FREKUENSI = 10.0

    # Eksekusi Rumus
    skor_likes = likes * BOBOT_LIKE
    skor_comments = comments * BOBOT_KOMENTAR
    skor_frekuensi = frekuensi_laporan * BOBOT_FREKUENSI

    return skor_likes + skor_comments + skor_frekuensi