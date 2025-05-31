from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas, crud # crud'u direkt import edelim
from app.api import deps

router = APIRouter()

@router.get("/me", response_model=schemas.UserWithStudents) # response_model'i UserWithStudents olarak güncelledik
def read_kullanici_me(
    current_user: models.User = Depends(deps.get_current_active_user), # models.Veli yerine models.User
):
    """
    Get current logged-in user's details.
    If the user is a parent, student details will be included.
    """
    return current_user

# Veli oluşturma (Sadece admin yetkisiyle olmalı, şimdilik eklemiyoruz)
# @router.post("/", response_model=schemas.Veli)
# def create_yeni_veli(
#     *, 
#     db: Session = Depends(deps.get_db),
#     veli_in: schemas.VeliCreate,
#     # current_user: models.User = Depends(deps.get_current_superuser) # Admin kontrolü için
# ):
#     veli = crud.veli.get_veli_by_email(db, email=veli_in.email)
#     if veli:
#         raise HTTPException(
#             status_code=400,
#             detail="The user with this email already exists in the system.",
#         )
#     veli = crud.veli.create_veli(db, veli=veli_in)
#     return veli 