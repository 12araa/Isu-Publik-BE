from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from app.utils.auth_middleware import verifikasi_admin
from app.services import qdrant_service

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)

# 1. SKEMA DATA YANG DITERIMA DARI VUE.JS
class UpdateIsuRequest(BaseModel):
    id_qdrant: str = Field(..., description="ID unik dari Qdrant")
    topik: str = Field(..., description="Topik isu yang dipilih")
    ringkasan: str = Field(..., description="Teks ringkasan/caption hasil editan")
    kategori: str = Field(..., description="Kategori isu yang dipilih")
    is_archived: bool = Field(..., description="Status apakah diarsipkan (True) atau ditampilkan (False)")

# 2. ENDPOINT UNTUK MENERIMA UPDATE (PUT)
@router.put("/isu-publik/{id_qdrant}", dependencies=[Depends(verifikasi_admin)])
def update_isu_publik(id_qdrant: str, payload: UpdateIsuRequest):
    if id_qdrant != payload.id_qdrant:
        raise HTTPException(status_code=400, detail="ID pada URL dan Payload tidak cocok")

    try:
        print(f"Menerima permintaan update untuk ID: {id_qdrant}")
        
        hasil_update = qdrant_service.update_payload_isu(
            id_vektor=id_qdrant,
            topik_baru=payload.topik,
            teks_baru=payload.ringkasan,
            kategori_baru=payload.kategori,
            status_arsip=payload.is_archived
        )

        if not hasil_update:
             raise HTTPException(status_code=404, detail="Isu tidak ditemukan di database")

        return {
            "status": "success",
            "message": f"Isu dengan ID {id_qdrant[:8]}... berhasil diperbarui."
        }

    except Exception as e:
        print(f"Error saat update isu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gagal memperbarui data: {str(e)}")