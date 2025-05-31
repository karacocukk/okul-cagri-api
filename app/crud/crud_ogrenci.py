from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.models import Ogrenci, Veli
from app.schemas.schemas import OgrenciCreate, OgrenciUpdate # OgrenciUpdate'ı sonra ekleyeceğiz

def get_ogrenci(db: Session, ogrenci_id: int) -> Optional[Ogrenci]:
    return db.query(Ogrenci).filter(Ogrenci.id == ogrenci_id).first()

def get_ogrenci_by_numara(db: Session, numara: str) -> Optional[Ogrenci]:
    return db.query(Ogrenci).filter(Ogrenci.numara == numara).first()

def get_ogrenciler_by_veli(db: Session, veli_id: int, skip: int = 0, limit: int = 100) -> List[Ogrenci]:
    return db.query(Ogrenci).filter(Ogrenci.veli_id == veli_id).offset(skip).limit(limit).all()

def create_veli_ogrenci(db: Session, ogrenci: OgrenciCreate, veli_id: int) -> Ogrenci:
    db_ogrenci = Ogrenci(**ogrenci.model_dump(), veli_id=veli_id)
    db.add(db_ogrenci)
    db.commit()
    db.refresh(db_ogrenci)
    return db_ogrenci

# OgrenciUpdate ve ilgili update/delete fonksiyonlarını daha sonra ihtiyaca göre ekleyebiliriz.
def update_ogrenci(
    db: Session, ogrenci_db_obj: Ogrenci, ogrenci_in: OgrenciUpdate
) -> Ogrenci:
    update_data = ogrenci_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ogrenci_db_obj, field, value)
    db.add(ogrenci_db_obj)
    db.commit()
    db.refresh(ogrenci_db_obj)
    return ogrenci_db_obj

def create_school_student(db: Session, ogrenci: OgrenciCreate, school_id: int) -> Ogrenci:
    # Ogrenci modelinin school_id alanına sahip olduğunu varsayıyoruz.
    # OgrenciCreate şemasından gelen verilerle Ogrenci objesi oluşturulur.
    db_ogrenci = Ogrenci(**ogrenci.model_dump(), school_id=school_id)
    db.add(db_ogrenci)
    db.commit()
    db.refresh(db_ogrenci)
    return db_ogrenci

def delete_ogrenci(db: Session, ogrenci_id: int, veli_id: int) -> Optional[Ogrenci]:
    # Öğrencinin sadece kendi velisi tarafından silinebildiğinden emin olmak için veli_id kontrolü eklenebilir.
    db_ogrenci = db.query(Ogrenci).filter(Ogrenci.id == ogrenci_id, Ogrenci.veli_id == veli_id).first()
    if not db_ogrenci:
        return None
    db.delete(db_ogrenci)
    db.commit()
    return db_ogrenci 