from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, ForwardRef, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .school import SchoolBase
    from .user import UserBase
    from .class_ import ClassBase

class TeacherBase(BaseModel):
    full_name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    branch: Optional[str] = None
    school_id: int # Öğretmen oluşturulurken okul ID'si zorunlu
    user_id: Optional[int] = None # Yeni eklendi: İlişkili kullanıcı ID'si

class TeacherCreateNoSchoolId(BaseModel):
    full_name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    branch: Optional[str] = None

class TeacherCreate(TeacherBase):
    pass

class TeacherUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    branch: Optional[str] = None

class TeacherInDBBase(TeacherBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Teacher(TeacherInDBBase):
    school: Optional[ForwardRef("SchoolBase")] = None
    assigned_classes: List[ForwardRef("ClassBase")] = []
    # user_account: Optional[ForwardRef("UserBase")] = None # UserBase için ForwardRef

# Teacher'ın ForwardRef'lerini çözmek için GEREKLİ importlar ve çağrı
from .school import SchoolBase
from .user import UserBase
from .class_ import ClassBase
Teacher.update_forward_refs() 