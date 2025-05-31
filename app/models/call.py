from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.base_class import Base

class CallStatusEnum(str, enum.Enum):
    PENDING = "pending"        # Veli tarafından çağrı yapıldı, öğretmen/sistem tarafından henüz görülmedi/onaylanmadı
    ACKNOWLEDGED = "acknowledged" # Öğretmen/sistem çağrıyı gördü/onayladı, öğrenci hazırlanıyor
    COMPLETED = "completed"      # Öğrenci veliye teslim edildi
    CANCELLED_BY_PARENT = "cancelled_by_parent" # Veli iptal etti
    CANCELLED_BY_SCHOOL = "cancelled_by_school" # Okul (öğretmen/admin) iptal etti (örn: öğrenci o gün yok)
    EXPIRED = "expired"          # Çağrı belirli bir süre içinde tamamlanmadı

class Call(Base):
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, index=True)
    
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True) # Veli olan User
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, index=True) # Öğrencinin çağrı anındaki sınıfı

    status = Column(SQLAlchemyEnum(CallStatusEnum), nullable=False, default=CallStatusEnum.PENDING, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    student = relationship("Student", back_populates="calls")
    parent = relationship("User", back_populates="sent_calls") # User modelinde 'sent_calls' tanımlanacak
    school = relationship("School", back_populates="calls")   # School modelinde 'calls' tanımlanacak
    class_ = relationship("Class", back_populates="calls")    # Class modelinde 'calls' tanımlanacak 