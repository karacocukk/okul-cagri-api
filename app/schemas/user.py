from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, ForwardRef, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .school import SchoolBase
    from .student import Student

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    PARENT = "parent"

class UserBase(BaseModel):
    username: str = Field(..., description="Kullanıcı adı (örn: telefon no veya email)")
    full_name: str
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = Field(None, description="Profil resmi URL'si")
    birth_date: Optional[str] = Field(None, description="Doğum tarihi (YYYY-MM-DD veya YYYY)")
    role: UserRole = Field(UserRole.PARENT, description="Kullanıcı rolü")
    school_id: Optional[int] = Field(None, description="Kullanıcının ilişkili olduğu okul ID'si (Yönetici/Öğretmen için zorunlu olabilir)")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Şifre en az 6 karakter olmalı")

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    profile_image_url: Optional[str] = Field(None, description="Profil resmi URL'si")
    birth_date: Optional[str] = Field(None, description="Doğum tarihi (YYYY-MM-DD veya YYYY)")

class UserPasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, description="Yeni şifre en az 6 karakter olmalı")

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    initial_password_changed: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class User(UserInDBBase):
    school: Optional[ForwardRef("SchoolBase")] = None

class UserWithStudents(User):
    students: List[ForwardRef("Student")] = []

# UserWithStudents'ın ForwardRef'lerini çözmek için GEREKLİ importlar ve çağrı
from .school import SchoolBase
from .student import Student
UserWithStudents.update_forward_refs()
User.update_forward_refs() 