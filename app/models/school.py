from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base_class import Base

class School(Base):
    __tablename__ = "schools"  # Tablo adını açıkça belirtiyoruz

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    unique_code = Column(String(100), unique=True, index=True, nullable=False, comment="Okulu benzersiz şekilde tanımlayan kod (setup için)")
    address = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships (will be defined in other models referencing School via ForeignKey)
    # and then back_populates will link them here automatically if named correctly in the other model,
    # or we can define them explicitly here like in okul_yonetim_api/models.py if preferred.

    # Explicit back-relations (as in okul_yonetim_api/models.py)
    users_in_school = relationship("User", back_populates="school")
    classes_in_school = relationship("Class", back_populates="school")
    students_in_school = relationship("Student", back_populates="school")
    teachers_in_school = relationship("Teacher", back_populates="school")
    notifications_in_school = relationship("Notification", back_populates="school")
    calls = relationship("Call", back_populates="school") 