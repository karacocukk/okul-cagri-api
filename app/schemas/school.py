from pydantic import BaseModel, Field
from typing import Optional, List, ForwardRef, TYPE_CHECKING
from datetime import datetime
# from .class_ import ClassBase # Bu satır kaldırıldı
# Diğer şema importları (ClassBase gibi) forward reference veya tam import ile çözülecek

if TYPE_CHECKING:
    from .class_ import ClassBase

class SchoolBase(BaseModel):
    name: str = Field(..., description="Okulun adı")
    unique_code: str = Field(..., description="Okulu benzersiz şekilde tanımlayan kod")
    address: Optional[str] = None

class SchoolCreate(SchoolBase):
    pass

class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    unique_code: Optional[str] = None
    address: Optional[str] = None

class SchoolInDBBase(SchoolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class School(SchoolInDBBase):
    pass

# Forward declaration için ClassBase (veya tam import)
# Bu, SchoolWithDetails gibi şemalarda ClassBase'e ihtiyaç duyulduğunda gerekecek.
# Eğer ClassBase başka bir dosyada (class_schema.py gibi) tanımlanacaksa,
# import .class_schema import ClassBase veya from . import class_schema şeklinde yapılabilir.
# Ya da string olarak 'ClassBase' kullanılabilir ve Pydantic bunu çözer.

class SchoolWithDetails(School):
    classes_in_school: List[ForwardRef('ClassBase')] = [] # Güncellendi, ForwardRef kullanıldı
    # Diğer detaylar (öğretmenler, öğrenciler) eklenebilir
    pass

# SchoolWithDetails'in ForwardRef'lerini çözmek için GEREKLİ importlar ve çağrı
from .class_ import ClassBase
SchoolWithDetails.update_forward_refs()

# Döngüsel importu çözmek için ForwardRef'leri güncelle
# Bu, tüm ilgili modeller import edildikten sonra yapılmalı.
# Genellikle __init__.py içinde veya her modülün sonunda yapılır.
# from .class_ import ClassBase # Buraya taşıdık

# SchoolWithDetails.update_forward_refs() # KALDIRILDI 