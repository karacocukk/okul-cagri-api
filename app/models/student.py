from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base_class import Base
from app.models.parent_student_relation import parent_student_association_table # Doğrudan import

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    student_number = Column(String(50), unique=True, index=True, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True, index=True) # Bir öğrenci bir sınıfa atanmış olabilir
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    school = relationship("School", back_populates="students_in_school")
    parents = relationship(
        "User", 
        secondary=parent_student_association_table,
        back_populates="students"
    )
    assigned_class = relationship("Class", back_populates="students_in_class")
    calls = relationship("Call", back_populates="student") # YENİ İLİŞKİ
    
    # İkinci, eski "parents" ilişkisi tanımı siliniyor.