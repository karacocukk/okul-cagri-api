from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

class Class(Base):
    __tablename__ = "classes"  # Tablo adını açıkça belirtiyoruz

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False) # School tablo adına göre düzeltildi
    class_name = Column(String(255), nullable=False) # Okul bazında unique olmalı (class_name, school_id)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True) # Sınıfın bir öğretmeni olabilir. Tablo adı 'teachers' olmalı (Teacher modeline bakılacak)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    school = relationship("School", back_populates="classes_in_school")
    teacher = relationship("Teacher", back_populates="assigned_classes")
    students_in_class = relationship("Student", back_populates="assigned_class")
    calls = relationship("Call", back_populates="class_") 