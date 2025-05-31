from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user

router = APIRouter(
    # prefix="/schools/{school_id}/notifications", # api_v1.py'de yönetilecek
    tags=["School Administration - Notifications"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(
    school_id: int, # Path'ten
    notification_in: schemas.NotificationCreate, # NotificationCreate school_id ve created_by_user_id içermeli
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Yeni bir bildirim oluşturur (belirli bir okul için).
    - Yetki: SCHOOL_ADMIN veya SUPER_ADMIN.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create notification in this school")

    db_school = crud.school.get(db, id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")

    # NotificationCreate şemasında school_id ve created_by_user_id olduğunu varsayıyoruz.
    # Path'ten gelen school_id ile body'deki school_id eşleşmeli.
    # created_by_user_id, current_user.id ile atanmalı.
    if notification_in.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School ID in path and body must match.")
    
    # Update obj_in with current_user.id before creating
    # Bunu crud.notification.create_with_creator gibi bir metoda devretmek daha iyi olabilir.
    # obj_to_create = notification_in.copy(update={"created_by_user_id": current_user.id})

    if notification_in.target_user_id:
        target_user = crud.user.get(db, id=notification_in.target_user_id)
        if not target_user or target_user.school_id != school_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Target user {notification_in.target_user_id} not found or not in school {school_id}")
    
    if notification_in.target_class_id:
        target_class = crud.class_.get_by_id_and_school_id(db, class_id=notification_in.target_class_id, school_id=school_id)
        if not target_class:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Target class {notification_in.target_class_id} not found in school {school_id}")

    return crud.notification.create_with_creator(db=db, obj_in=notification_in, creator_id=current_user.id)


@router.get("/user/me", response_model=List[schemas.Notification])
async def get_my_notifications_for_school(
    school_id: int, # Path'ten
    skip: int = 0,
    limit: int = 100,
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Giriş yapmış kullanıcının belirli bir okuldaki bildirimlerini listeler.
    """
    # Okul yetki kontrolü
    user_school_id = getattr(current_user, 'school_id', None)
    can_access_school_notifications = False
    if current_user.role == schemas.UserRole.SUPER_ADMIN:
        can_access_school_notifications = True
    elif user_school_id == school_id:
        can_access_school_notifications = True
    elif current_user.role == schemas.UserRole.PARENT:
        students_of_parent = crud.student.get_students_by_parent_user_id(db, parent_user_id=current_user.id)
        if any(s.school_id == school_id for s in students_of_parent):
            can_access_school_notifications = True

    if not can_access_school_notifications:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access notifications for this school")
    
    # Öğrencinin sınıf ID'lerini al (eğer varsa ve o okuldaysa)
    user_class_ids = []
    if hasattr(current_user, 'students'): # Eğer user objesinde student ilişkisi varsa
        user_class_ids = [s.class_id for s in current_user.students if s.class_id and s.school_id == school_id]
    elif current_user.role == schemas.UserRole.STUDENT and hasattr(current_user, 'student_profile') and current_user.student_profile.school_id == school_id:
        # Eğer user bir öğrenciyse ve student_profile üzerinden class_id'ye erişilebiliyorsa
        user_class_ids = [current_user.student_profile.class_id] if current_user.student_profile.class_id else []
    
    # Öğretmenin sınıf ID'lerini al (eğer varsa ve o okuldaysa)
    if current_user.role == schemas.UserRole.TEACHER and hasattr(current_user, 'teacher_profile') and current_user.teacher_profile.school_id == school_id:
        # Öğretmenin sorumlu olduğu sınıflar (Class modelinde teacher_id üzerinden)
        teacher_classes = crud.class_.get_multi_by_teacher_id(db, teacher_id=current_user.teacher_profile.id, school_id=school_id)
        user_class_ids.extend([c.id for c in teacher_classes])

    notifications = crud.notification.get_for_user(
        db, 
        user_id=current_user.id, 
        school_id=school_id, 
        user_role=current_user.role, 
        user_class_ids=list(set(user_class_ids)), # Benzersiz sınıf ID'leri
        skip=skip, 
        limit=limit,
        unread_only=unread_only
    )
    return notifications

# Bu path'i /notifications/{notification_id}/mark-as-read olarak ana api_v1.py'de handle etmek daha uygun olabilir.
# Şimdilik /school-admin prefix'i altında kalacak şekilde güncelliyorum.
@router.post("/{notification_id}/mark-as-read", response_model=schemas.NotificationReadStatus)
async def mark_notification_as_read(
    school_id: int, # school_id path'ten geliyor, bu endpoint için gerekliliği tartışılabilir.
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir bildirimi giriş yapmış kullanıcı için okundu olarak işaretler.
    """
    db_notification = crud.notification.get(db, id=notification_id)
    if not db_notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    # Yetkilendirme: Kullanıcı bu bildirimi almalı.
    # crud.notification.get_for_user içinde bu kontrol yapılabilir veya burada ayrıca yapılır.
    # Şimdilik basitçe, bildirimin okulunun kullanıcının okuluyla eşleşip eşleşmediğini kontrol edebiliriz (SUPER_ADMIN hariç).
    if current_user.role != schemas.UserRole.SUPER_ADMIN and db_notification.school_id != current_user.school_id:
        # Daha detaylı: Kullanıcı bu bildirimin hedefi mi (user_id, class_id, genel bildirim)?
        # Bu kontrolü crud.notification_read_status.mark_as_read içine taşımak daha iyi olabilir.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to mark this notification as read for this school.")
    
    # school_id parametresi aslında db_notification.school_id'den doğrulanabilir.
    if db_notification.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Notification does not belong to the specified school path.")

    return crud.notification_read_status.mark_as_read(db, notification_id=notification_id, user_id=current_user.id)

@router.get("/all", response_model=List[schemas.Notification])
async def get_all_notifications_for_school_admin(
    school_id: int, # Path'ten
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Bir okuldaki tüm bildirimleri listeler (Okul Admini veya Süper Admin için).
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list all notifications for this school")

    notifications = crud.notification.get_multi_by_school(db, school_id=school_id, skip=skip, limit=limit)
    return notifications

@router.get("/{notification_id}", response_model=schemas.Notification)
async def get_notification_by_id(
    school_id: int, # Path'ten. Bildirimin bu okula ait olup olmadığını kontrol için.
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    notification = crud.notification.get(db, id=notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    
    if notification.school_id != school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Notification {notification_id} not found in school {school_id}")

    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == notification.school_id)):
        # Eğer kullanıcı SUPER_ADMIN veya ilgili okulun SCHOOL_ADMIN'i değilse,
        # kendi bildirimi olup olmadığını kontrol et (get_my_notifications_for_school'daki gibi bir mantıkla)
        # Şimdilik sadece adminlerin ID ile direkt erişebileceğini varsayıyoruz.
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this notification directly by ID")
        
    return notification 