from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# Bu dosyadaki şemalar, app.models.legacy_models.py içindeki modellere karşılık gelir.

# Veli Şemaları (Legacy)
class LegacyVeliBase(BaseModel):
    email: EmailStr
    ad: Optional[str] = None
    # Diğer alanlar legacy modelden (Veli) eklenebilir: soyad, telefon, adres
    soyad: Optional[str] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None

class LegacyVeliCreate(LegacyVeliBase):
    password: str # Bu alan yeni User modelinde nasıl ele alınacak?
                  # Belki de UserCreate kullanılmalı ve rolü parent olmalı.

class LegacyVeliInDBBase(LegacyVeliBase):
    id: int
    # is_active: bool # Bu yeni User modelinde var.
    class Config:
        from_attributes = True

class LegacyVeli(LegacyVeliInDBBase):
    pass

class LegacyVeliUpdate(BaseModel):
    email: Optional[EmailStr] = None
    ad: Optional[str] = None
    soyad: Optional[str] = None
    telefon: Optional[str] = None
    adres: Optional[str] = None
    # password: Optional[str] = None
    # is_active: Optional[bool] = None

# Öğrenci Şemaları (Legacy)
class LegacyOgrenciBase(BaseModel):
    ad: str
    soyad: Optional[str] = None # soyad modelde var, buraya da ekleyelim
    numara: str
    sinif: str

class LegacyOgrenciCreate(LegacyOgrenciBase):
    veli_id: int # Bu yeni ParentStudentRelation ile nasıl eşleşecek?

class LegacyOgrenci(LegacyOgrenciBase):
    id: int
    veli_id: int
    class Config:
        from_attributes = True

class LegacyOgrenciUpdate(BaseModel):
    ad: Optional[str] = None
    soyad: Optional[str] = None
    numara: Optional[str] = None
    sinif: Optional[str] = None
    # veli_id: Optional[int] = None

# Veli Detay (Öğrencileriyle birlikte) (Legacy)
class LegacyVeliWithOgrenciler(LegacyVeli):
    ogrenciler: List[LegacyOgrenci] = []

# Çağrı Şemaları (Legacy) - Bunlar yeni Notification sistemiyle entegre edilebilir.
class LegacyCagriBase(BaseModel):
    ogrenci_id: int
    # veli_id de cagri modelinde var, buraya da eklenebilir.
    veli_id: Optional[int] = None 

class LegacyCagriCreate(LegacyCagriBase):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # tarih ve durum create sırasında nasıl ele alınacak?
    # Modeldeki 'tarih' String, belki datetime olmalı.

class LegacyCagri(LegacyCagriBase):
    id: int
    tarih: str # Modelde String, belki datetime olmalı
    durum: str
    # ogrenci: LegacyOgrenci # İlişkili öğrenci detayı
    # veli: LegacyVeli # İlişkili veli detayı (opsiyonel)
    class Config:
        from_attributes = True

class LegacyCagriUpdate(BaseModel):
    durum: Optional[str] = None 