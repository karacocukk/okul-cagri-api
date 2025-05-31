from pydantic import BaseModel, Field
from typing import Optional, List, ForwardRef, TYPE_CHECKING
from datetime import datetime

# TYPE_CHECKING blokları dışındaki doğrudan importları azaltıyoruz
if TYPE_CHECKING:
    from .school import SchoolBase
    from .user import UserBase
    from .class_ import ClassBase

class StudentBase(BaseModel):
    full_name: str
    student_number: Optional[str] = None
    class_id: Optional[int] = None
    school_id: int # Öğrenci oluşturulurken okul ID'si zorunlu
    # Veli ataması için. Öğrenci oluşturulurken/güncellenirken veli ID'leri listesi.
    parent_user_ids: Optional[List[int]] = Field(default_factory=list)

class StudentCreateNoSchoolId(BaseModel):
    full_name: str
    student_number: Optional[str] = None
    class_id: Optional[int] = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    student_number: Optional[str] = None
    class_id: Optional[int] = None
    # Veli ataması için. Öğrenci güncellenirken veli ID'leri listesi.
    parent_user_ids: Optional[List[int]] = Field(default_factory=list)

class StudentInDBBase(StudentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Student(StudentInDBBase):
    school: Optional[ForwardRef("SchoolBase")] = None
    parents: List[ForwardRef("UserBase")] = []
    assigned_class: Optional[ForwardRef("ClassBase")] = None

# Student'ın ForwardRef'lerini çözmek için GEREKLİ importlar ve çağrı
# Bu importlar, update_forward_refs çalışmadan önce ilgili modüllerin yüklenmesini sağlar.
from .school import SchoolBase
from .user import UserBase
from .class_ import ClassBase
Student.update_forward_refs() 