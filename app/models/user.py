from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLAlchemyEnum, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from ..db.base_class import Base # Updated import
from app.models.parent_student_relation import parent_student_association_table # Doğrudan import

class UserRoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    SCHOOL_ADMIN = "school_admin"
    TEACHER = "teacher"
    PARENT = "parent"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False) # Telefon no veya email olabilir
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    phone_number = Column(String(50), unique=True, index=True, nullable=True)
    profile_image_url = Column(String(512), nullable=True)
    birth_date = Column(String(20), nullable=True) # YYYY-MM-DD veya YYYY olabilir
    
    role = Column(SQLAlchemyEnum(UserRoleEnum), nullable=False, default=UserRoleEnum.PARENT)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True, index=True) # Yönetici/Öğretmen için zorunlu, Veli için opsiyonel
    
    is_active = Column(Boolean(), default=True)
    initial_password_changed = Column(Boolean(), default=False) # İlk şifrenin değiştirilip değiştirilmediği

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School", back_populates="users_in_school") # Bir kullanıcı bir okula ait olabilir (yönetici, öğretmen)
    students = relationship(
        "Student", 
        secondary=parent_student_association_table,
        back_populates="parents"
    ) # Veli ise ilişkili öğrenciler
    teacher_info = relationship("Teacher", uselist=False, back_populates="user_account") # Eğer kullanıcı öğretmen ise, öğretmen detayları
    notifications_created = relationship("Notification", back_populates="creator_user", foreign_keys="[Notification.creator_user_id]")
    notification_read_statuses = relationship("NotificationReadStatus", back_populates="reader_user")
    sent_calls = relationship("Call", back_populates="parent") # YENİ İLİŞKİ (Veli olarak gönderdiği çağrılar)

    # For notification read statuses - Artık notification_read_statuses adıyla yukarıda tanımlandı
    # Bu satır tamamen kaldırılacak
    # read_statuses = relationship("NotificationReadStatus", back_populates="reader_user")