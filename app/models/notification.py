from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..db.base_class import Base # Updated import

class Notification(Base):
    __tablename__ = "notifications"  # Tablo adını açıkça belirtiyoruz

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False) # Düzeltildi
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Düzeltildi
    recipient_class_id = Column(Integer, ForeignKey("classes.id"), nullable=True) # Düzeltildi
    is_general = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    creator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Sütun adı created_by_user_id yerine creator_user_id olarak değiştirildi

    school = relationship("School", back_populates="notifications_in_school")
    recipient_user = relationship("User", foreign_keys=[recipient_user_id], backref="received_notifications")
    recipient_class = relationship("Class", foreign_keys=[recipient_class_id], backref="class_notifications")
    creator_user = relationship("User", foreign_keys=[creator_user_id], back_populates="notifications_created")
    read_statuses = relationship("NotificationReadStatus", back_populates="notification_details")

class NotificationReadStatus(Base):
    __tablename__ = "notification_read_statuses"  # Tablo adını açıkça belirtiyoruz

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False) # Düzeltildi
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Düzeltildi
    read_at = Column(DateTime(timezone=True), server_default=func.now())

    notification_details = relationship("Notification", back_populates="read_statuses")
    reader_user = relationship("User", back_populates="notification_read_statuses") 