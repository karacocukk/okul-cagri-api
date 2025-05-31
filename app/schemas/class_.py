from pydantic import BaseModel, Field
from typing import Optional, List, ForwardRef, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .student import StudentBase
    from .school import SchoolBase
    from .teacher import TeacherBase

class ClassBase(BaseModel):
    class_name: str
    teacher_id: Optional[int] = None
    school_id: int

class ClassCreateNoSchoolId(BaseModel):
    class_name: str
    teacher_id: Optional[int] = None

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    teacher_id: Optional[int] = None

class ClassInDBBase(ClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Class(ClassInDBBase):
    school: Optional[ForwardRef('SchoolBase')] = None
    teacher: Optional[ForwardRef("TeacherBase")] = None
    students_in_class: List[ForwardRef("StudentBase")] = []

# from .school import SchoolBase # KALDIRILDI
# from .teacher import TeacherBase # KALDIRILDI

# Class'ın ForwardRef'lerini çözmek için GEREKLİ importlar ve çağrı
from .school import SchoolBase
from .teacher import TeacherBase
from .student import StudentBase
Class.update_forward_refs() 