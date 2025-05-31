from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

class Teacher(Base):
    __tablename__ = "teachers"  # Tablo adını açıkça belirtiyoruz

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)  # School tablo adına göre düzeltildi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # User ile ilişki için
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School", back_populates="teachers_in_school")
    assigned_classes = relationship("Class", back_populates="teacher")
    user_account = relationship("User", back_populates="teacher_info")  # User ile ilişki