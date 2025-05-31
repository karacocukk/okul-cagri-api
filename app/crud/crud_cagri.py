from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import func # Zaman damgası için

from app.models.models import Cagri, Ogrenci
from app.schemas.schemas import CagriCreate, CagriUpdate # CagriUpdate'ı sonra ekleyeceğiz
from app.core.location import is_within_school_area
from app.core.config import settings # MAX_DISTANCE_METERS için

def get_cagri(db: Session, cagri_id: int) -> Optional[Cagri]:
    return db.query(Cagri).options(joinedload(Cagri.ogrenci)).filter(Cagri.id == cagri_id).first()

def get_cagrilar(db: Session, skip: int = 0, limit: int = 100) -> List[Cagri]:
    return db.query(Cagri).options(joinedload(Cagri.ogrenci).joinedload(Ogrenci.veli)).order_by(Cagri.cagri_saati.desc()).offset(skip).limit(limit).all()

def get_cagrilar_by_sinif(
    db: Session, sinif: str, skip: int = 0, limit: int = 100, aktif: bool = True
) -> List[Cagri]:
    query = db.query(Cagri).join(Cagri.ogrenci).filter(Ogrenci.sinif == sinif)
    if aktif:
        query = query.filter(Cagri.durum == "beklemede") # Sadece aktif çağrıları getir
    return query.options(joinedload(Cagri.ogrenci)).order_by(Cagri.cagri_saati.asc()).offset(skip).limit(limit).all()

def create_cagri(db: Session, cagri: CagriCreate, ogrenci_id: int, veli_id: int) -> Optional[Cagri]:
    # Öğrencinin varlığını ve veliye ait olduğunu kontrol et
    ogrenci = db.query(Ogrenci).filter(Ogrenci.id == ogrenci_id, Ogrenci.veli_id == veli_id).first()
    if not ogrenci:
        return None # Öğrenci bulunamadı veya veliye ait değil

    # Konum kontrolü (eğer çağrı oluşturma şemasında konum bilgisi varsa)
    if cagri.latitude is not None and cagri.longitude is not None:
        if not is_within_school_area(cagri.latitude, cagri.longitude):
            # Okul alanında değilse None dönebiliriz veya bir exception raise edebiliriz.
            # API katmanında bu durum daha iyi yönetilebilir.
            # Şimdilik None dönüyoruz, API katmanı bunu 400 Bad Request olarak yorumlayabilir.
            return "OUT_OF_AREA" # Özel bir string dönebiliriz bu durum için
            
    db_cagri = Cagri(
        ogrenci_id=ogrenci_id,
        veli_id=veli_id,
        # cagri_saati varsayılan olarak modelde server_default=func.now() ile ayarlı
        # durum da varsayılan olarak "beklemede"
    )
    db.add(db_cagri)
    db.commit()
    db.refresh(db_cagri)
    # Yeni oluşturulan çağrıyı öğrenci bilgisiyle birlikte yükleyerek dönelim
    return db.query(Cagri).options(joinedload(Cagri.ogrenci)).filter(Cagri.id == db_cagri.id).first()

def update_cagri_durum(db: Session, cagri_id: int, durum: str) -> Optional[Cagri]:
    db_cagri = get_cagri(db, cagri_id=cagri_id)
    if not db_cagri:
        return None
    db_cagri.durum = durum
    db.commit()
    db.refresh(db_cagri)
    return db_cagri

# CagriUpdate şeması ve tam update fonksiyonu daha sonra eklenebilir
# def update_cagri(db: Session, cagri_id: int, cagri_in: CagriUpdate) -> Optional[Cagri]:
#     db_cagri = get_cagri(db, cagri_id)
#     if not db_cagri:
#         return None
#     update_data = cagri_in.model_dump(exclude_unset=True)
#     for field, value in update_data.items():
#         setattr(db_cagri, field, value)
#     db.commit()
#     db.refresh(db_cagri)
#     return db_cagri 