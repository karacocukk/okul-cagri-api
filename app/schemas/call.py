from pydantic import BaseModel, Field
from typing import Optional, ForwardRef, TYPE_CHECKING
from datetime import datetime

from app.models.call import CallStatusEnum # Modeldeki Enum'ı import ediyoruz

if TYPE_CHECKING:
    from .student import Student as StudentSchema # Çakışmayı önlemek için alias
    from .user import User as UserSchema
    from .school import School as SchoolSchema
    from .class_ import Class as ClassSchema

# Temel Şema
class CallBase(BaseModel):
    student_id: int = Field(..., description="Çağrının yapıldığı öğrencinin ID'si")
    # parent_user_id, school_id, class_id backend'de eklenecek veya token'dan/öğrenciden alınacak

class CallCreate(BaseModel):
    student_id: int = Field(..., description="Çağrının yapıldığı öğrencinin ID'si")
    # Veli kendi ID'sini göndermeyecek, token'dan alınacak.
    # Okul ve sınıf ID'si öğrenci üzerinden belirlenecek.

class CallStatusUpdate(BaseModel):
    status: CallStatusEnum = Field(..., description="Çağrının yeni durumu")

# DB'den okunan temel şema (ID ve timestamp'ler dahil)
class CallInDBBase(CallBase):
    id: int
    parent_user_id: int # DB'den okurken bu alanlar dolu olacak
    school_id: int
    class_id: int
    status: CallStatusEnum
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# API yanıtları için tam şema (ilişkilerle birlikte)
class Call(CallInDBBase):
    student: Optional[ForwardRef("StudentSchema")] = None
    parent: Optional[ForwardRef("UserSchema")] = None
    school: Optional[ForwardRef("SchoolSchema")] = None
    class_: Optional[ForwardRef("ClassSchema")] = Field(None, alias="class_info") # 'class' Python keyword'ü olduğu için alias

# ForwardRef'leri çözmek için
# Bu importlar, update_forward_refs çalışmadan önce ilgili modüllerin yüklenmesini sağlar.
from .student import Student as StudentSchema
from .user import User as UserSchema
from .school import School as SchoolSchema
from .class_ import Class as ClassSchema

Call.update_forward_refs() 