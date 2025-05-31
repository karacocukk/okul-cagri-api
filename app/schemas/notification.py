from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .school import SchoolBase
from .user import UserBase
from .class_ import ClassBase

class NotificationBase(BaseModel):
    title: str = Field(..., max_length=255)
    message: str
    recipient_user_id: Optional[int] = None
    recipient_class_id: Optional[int] = None
    is_general: Optional[bool] = False
    school_id: int

class NotificationCreateNoSchoolId(BaseModel):
    title: str = Field(..., max_length=255)
    message: str
    recipient_user_id: Optional[int] = None
    recipient_class_id: Optional[int] = None
    is_general: Optional[bool] = False

class NotificationCreate(NotificationBase):
    pass

class NotificationInDBBase(NotificationBase):
    id: int
    sent_at: datetime
    created_by_user_id: Optional[int] = None

    class Config:
        from_attributes = True

class Notification(NotificationInDBBase):
    school: Optional[SchoolBase] = None
    recipient_user: Optional[UserBase] = None
    recipient_class: Optional[ClassBase] = None
    creator_user: Optional[UserBase] = None

class NotificationReadStatusBase(BaseModel):
    notification_id: int
    user_id: int

class NotificationReadStatusCreate(BaseModel):
    pass # Belki burada user_id gerekmez, path'ten alınır?

class NotificationReadStatusInDBBase(NotificationReadStatusBase):
    id: int
    read_at: datetime

    class Config:
        from_attributes = True

class NotificationReadStatus(NotificationReadStatusInDBBase):
    pass

class NotificationWithReadInfo(Notification):
    is_read: bool 