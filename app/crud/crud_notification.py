from typing import List, Optional
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func, and_

from app.crud.base import CRUDBase
from app.models.notification import Notification, NotificationReadStatus
from app.models.user import User
from app.models.class_ import Class
from app.models.school import School
from app.schemas.notification import NotificationCreate, NotificationReadStatusCreate # NotificationUpdate gerekirse eklenebilir

class CRUDNotification(CRUDBase[Notification, NotificationCreate, None]): # NotificationUpdate şimdilik None
    def create_with_creator(self, db: Session, obj_in: NotificationCreate, created_by_user_id: int) -> Notification:
        db_obj = self.model(
            **obj_in.dict(), 
            created_by_user_id=created_by_user_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_notification_by_id_and_school(self, db: Session, notification_id: int, school_id: int) -> Optional[Notification]:
        return db.query(self.model).options(
            selectinload(Notification.school),
            selectinload(Notification.recipient_user),
            selectinload(Notification.recipient_class),
            selectinload(Notification.creator_user)
        ).filter(self.model.id == notification_id, self.model.school_id == school_id).first()
    
    def get_user_notifications_with_read_status(
        self, db: Session, user_id: int, school_id: int, skip: int = 0, limit: int = 100
    ) -> List[dict]: # NotificationWithReadInfo gibi bir şema kullanılabilir
        """ Kullanıcının okuldaki genel ve kendisine/sınıfına özel bildirimleri okundu bilgisiyle getirir."""
        
        # Kullanıcının sınıfını bul (eğer varsa)
        user_class_id = db.query(User.class_id).filter(User.id == user_id).scalar_one_or_none()

        # Bildirimleri ve okundu durumlarını join ile çek
        # SQLAlchemy Core kullanarak daha optimize bir sorgu yazılabilir.
        # Şimdilik ORM ile devam edelim.
        
        # Sol join NotificationReadStatus (bu kullanıcı için)
        # Genel bildirimler (is_general=True, school_id=school_id)
        # Kullanıcıya özel bildirimler (recipient_user_id=user_id, school_id=school_id)
        # Sınıfa özel bildirimler (recipient_class_id=user_class_id, school_id=school_id)

        query = db.query(
            Notification,
            NotificationReadStatus.read_at
        ).outerjoin(
            NotificationReadStatus, 
            and_(
                NotificationReadStatus.notification_id == Notification.id,
                NotificationReadStatus.user_id == user_id
            )
        ).filter(Notification.school_id == school_id)
        
        conditions = []
        conditions.append(Notification.is_general == True)
        conditions.append(Notification.recipient_user_id == user_id)
        if user_class_id:
            conditions.append(Notification.recipient_class_id == user_class_id)
        
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
        
        query = query.order_by(Notification.sent_at.desc()).offset(skip).limit(limit)
        
        results = query.all()
        
        notifications_with_read_info = []
        for notif, read_at in results:
            notif_dict = notif.__dict__ # Veya şema kullanarak serialize et
            notif_dict['is_read'] = read_at is not None
            # İlişkili objeleri de şemaya uygun hale getirmek gerekebilir
            # notif_dict['school'] = schemas.School.from_orm(notif.school).dict() if notif.school else None 
            notifications_with_read_info.append(notif_dict)
            
        return notifications_with_read_info

    def mark_notification_as_read(self, db: Session, notification_id: int, user_id: int, school_id: int) -> Optional[NotificationReadStatus]:
        # Bildirimin varlığını ve okula ait olduğunu kontrol et
        notification = self.get_notification_by_id_and_school(db, notification_id, school_id)
        if not notification:
            return None # Veya hata fırlat

        existing_read_status = db.query(NotificationReadStatus).filter(
            NotificationReadStatus.notification_id == notification_id,
            NotificationReadStatus.user_id == user_id
        ).first()

        if existing_read_status:
            return existing_read_status
        
        db_read_status = NotificationReadStatus(notification_id=notification_id, user_id=user_id)
        db.add(db_read_status)
        db.commit()
        db.refresh(db_read_status)
        return db_read_status

    def get_unread_notification_count(self, db: Session, user_id: int, school_id: int) -> int:
        user_class_id = db.query(User.class_id).filter(User.id == user_id).scalar_one_or_none()

        # Okunmamış bildirimleri say
        # Notification tablosundan başlayıp, NotificationReadStatus'ta karşılığı olmayanları say.
        query = db.query(func.count(Notification.id)).outerjoin(
            NotificationReadStatus,
            and_(
                NotificationReadStatus.notification_id == Notification.id,
                NotificationReadStatus.user_id == user_id
            )
        ).filter(Notification.school_id == school_id, NotificationReadStatus.id == None) # Okunmamış olanlar

        conditions = []
        conditions.append(Notification.is_general == True)
        conditions.append(Notification.recipient_user_id == user_id)
        if user_class_id:
            conditions.append(Notification.recipient_class_id == user_class_id)
        
        from sqlalchemy import or_
        query = query.filter(or_(*conditions))
        
        count = query.scalar_one_or_none() or 0
        return count

    def get_notification_read_status(self, db: Session, notification_id: int, user_id: int, school_id: int) -> Optional[NotificationReadStatus]:
        # Önce notification'ın o school'a ait olduğunu doğrula (opsiyonel ama iyi bir pratik)
        notification = db.query(Notification.id).filter(Notification.id == notification_id, Notification.school_id == school_id).first()
        if not notification:
            return None
        return db.query(NotificationReadStatus).filter(
            NotificationReadStatus.notification_id == notification_id,
            NotificationReadStatus.user_id == user_id
        ).first() 