from .token import Token, TokenData
from .school import SchoolBase, SchoolCreate, SchoolUpdate, SchoolInDBBase, School, SchoolWithDetails
from .user import UserRole, UserBase, UserCreate, UserUpdate, UserPasswordChange, UserInDBBase, User, UserWithStudents
from .student import StudentBase, StudentCreateNoSchoolId, StudentCreate, StudentUpdate, StudentInDBBase, Student
from .teacher import TeacherBase, TeacherCreateNoSchoolId, TeacherCreate, TeacherUpdate, TeacherInDBBase, Teacher
from .class_ import ClassBase, ClassCreateNoSchoolId, ClassCreate, ClassUpdate, ClassInDBBase, Class
from .notification import (
    NotificationBase, NotificationCreateNoSchoolId, NotificationCreate, 
    NotificationInDBBase, Notification, NotificationWithReadInfo,
    NotificationReadStatusBase, NotificationReadStatusCreate, 
    NotificationReadStatusInDBBase, NotificationReadStatus
)
from .app_settings import (
    SchoolAppSettingsBase, SchoolAppSettingsCreate, 
    SchoolAppSettingsInDBBase, SchoolAppSettings
)
from .location import LocationConfig

from .legacy_schemas import (
    LegacyVeliBase, LegacyVeliCreate, LegacyVeliInDBBase, LegacyVeli, LegacyVeliUpdate, LegacyVeliWithOgrenciler,
    LegacyOgrenciBase, LegacyOgrenciCreate, LegacyOgrenci, LegacyOgrenciUpdate,
    LegacyCagriBase, LegacyCagriCreate, LegacyCagri, LegacyCagriUpdate
)

from .call import CallStatusEnum, CallBase, CallCreate, CallStatusUpdate, CallInDBBase, Call

__all__ = [
    "Token", "TokenData",
    "SchoolBase", "SchoolCreate", "SchoolUpdate", "SchoolInDBBase", "School", "SchoolWithDetails",
    "UserRole", "UserBase", "UserCreate", "UserUpdate", "UserPasswordChange", "UserInDBBase", "User", "UserWithStudents",
    "StudentBase", "StudentCreateNoSchoolId", "StudentCreate", "StudentUpdate", "StudentInDBBase", "Student",
    "TeacherBase", "TeacherCreateNoSchoolId", "TeacherCreate", "TeacherUpdate", "TeacherInDBBase", "Teacher",
    "ClassBase", "ClassCreateNoSchoolId", "ClassCreate", "ClassUpdate", "ClassInDBBase", "Class",
    "NotificationBase", "NotificationCreateNoSchoolId", "NotificationCreate",
    "NotificationInDBBase", "Notification", "NotificationWithReadInfo",
    "NotificationReadStatusBase", "NotificationReadStatusCreate",
    "NotificationReadStatusInDBBase", "NotificationReadStatus",
    "SchoolAppSettingsBase", "SchoolAppSettingsCreate",
    "SchoolAppSettingsInDBBase", "SchoolAppSettings",
    "LocationConfig",
    "CallStatusEnum", "CallBase", "CallCreate", "CallStatusUpdate", "CallInDBBase", "Call",
    "LegacyVeliBase", "LegacyVeliCreate", "LegacyVeliInDBBase", "LegacyVeli", "LegacyVeliUpdate", "LegacyVeliWithOgrenciler",
    "LegacyOgrenciBase", "LegacyOgrenciCreate", "LegacyOgrenci", "LegacyOgrenciUpdate",
    "LegacyCagriBase", "LegacyCagriCreate", "LegacyCagri", "LegacyCagriUpdate",
] 