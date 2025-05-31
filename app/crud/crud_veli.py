from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.security import get_password_hash
from app.models.models import Veli
from app.schemas.schemas import VeliCreate, VeliUpdate # VeliUpdate'ı sonra ekleyeceğiz

def get_veli(db: Session, veli_id: int) -> Optional[Veli]:
    return db.query(Veli).filter(Veli.id == veli_id).first()

def get_veli_by_email(db: Session, email: str) -> Optional[Veli]:
    return db.query(Veli).filter(Veli.email == email).first()

def get_veliler(db: Session, skip: int = 0, limit: int = 100) -> List[Veli]:
    return db.query(Veli).offset(skip).limit(limit).all()

def create_veli(db: Session, veli: VeliCreate) -> Veli:
    hashed_password = get_password_hash(veli.password)
    db_veli = Veli(
        email=veli.email,
        ad=veli.ad,
        hashed_password=hashed_password
    )
    db.add(db_veli)
    db.commit()
    db.refresh(db_veli)
    return db_veli

# VeliUpdate ve ilgili update fonksiyonunu daha sonra ihtiyaca göre ekleyebiliriz.
# def update_veli(db: Session, veli_id: int, veli_in: VeliUpdate) -> Optional[Veli]:
#     db_veli = get_veli(db, veli_id)
#     if not db_veli:
#         return None
#     update_data = veli_in.model_dump(exclude_unset=True)
#     if "password" in update_data and update_data["password"]:
#         hashed_password = get_password_hash(update_data["password"])
#         del update_data["password"]
#         update_data["hashed_password"] = hashed_password
#     for field, value in update_data.items():
#         setattr(db_veli, field, value)
#     db.commit()
#     db.refresh(db_veli)
#     return db_veli

# def delete_veli(db: Session, veli_id: int) -> Optional[Veli]:
#     db_veli = get_veli(db, veli_id)
#     if not db_veli:
#         return None
#     db.delete(db_veli)
#     db.commit()
#     return db_veli 