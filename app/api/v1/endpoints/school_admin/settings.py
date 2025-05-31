from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, Optional, List
import logging # Loglama için eklendi

from app import crud, models, schemas
from app.dependencies import get_db, get_current_active_user
from app.core.config import settings as app_global_settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/location-config", response_model=schemas.LocationConfig)
async def get_location_config(
    # Bu endpoint için özel bir yetkilendirme gerekip gerekmediği değerlendirilmeli.
    # Şimdilik açık bırakılabilir veya en azından giriş yapmış kullanıcı gerektirebilir.
    # current_user: models.User = Depends(get_current_active_user) 
):
    """
    Mobil uygulamanın öğrenci çağırma özelliği için 
    okulun konumunu ve maksimum mesafeyi döndürür.
    Bu bilgiler .env dosyasından veya veritabanındaki 
    SchoolSettings tablosundan gelebilir.
    Şu an için config.py (ve dolayısıyla .env) üzerinden alınıyor.
    """
    if not app_global_settings.SCHOOL_LATITUDE or not app_global_settings.SCHOOL_LONGITUDE or app_global_settings.MAX_DISTANCE_METERS is None:
        # Bu değerler .env dosyasında tanımlı değilse veya config'de yüklenemediyse
        # Loglama yapılabilir.
        # Varsayılan değerler döndürmek yerine hata vermek daha doğru olabilir.
        # Ya da veritabanından çekmeye çalışılabilir.
        # Şimdilik, bu değerlerin config'de zorunlu olduğunu varsayıyoruz.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="School location configuration is not available. Please check server settings."
        )
    
    return schemas.LocationConfig(
        school_latitude=app_global_settings.SCHOOL_LATITUDE,
        school_longitude=app_global_settings.SCHOOL_LONGITUDE,
        max_distance_meters=app_global_settings.MAX_DISTANCE_METERS
    )

# --- Okul Bazlı Ayarlar (SchoolSettings) --- #
# Bu endpoint'ler okul bazlı ayarları yönetmek için eklenebilir.
# crud.py ve models.py'de SchoolSettings için yapılar oluşturulmalı.

@router.post("/schools/{school_id}/app-settings", response_model=schemas.SchoolAppSettings, status_code=status.HTTP_201_CREATED)
def create_or_update_school_app_settings(
    school_id: int,
    settings_in: schemas.SchoolAppSettingsCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okul için uygulama ayarlarını oluşturur veya günceller.
    - Yetki: Sadece o okulun SCHOOL_ADMIN'i veya SUPER_ADMIN.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this school's settings")

    db_school = crud.get_school(db, school_id=school_id)
    if not db_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with ID {school_id} not found")
    
    # crud.create_or_update_school_settings fonksiyonu SchoolSettings modelini ve şemasını kullanacak.
    # Bu fonksiyon, mevcut ayar varsa günceller, yoksa yenisini oluşturur.
    # Şimdilik varsayımsal bir crud fonksiyonu çağrılıyor.
    # return crud.create_or_update_school_settings(db, school_id=school_id, settings_in=settings_in)
    
    # Geçici Dummy Yanıt (crud fonksiyonu yazılana kadar)
    dummy_response = schemas.SchoolAppSettings(
        id=1, # Geçici ID
        school_id=school_id,
        setting_key=settings_in.setting_key,
        setting_value=settings_in.setting_value,
        last_updated_by_user_id=current_user.id
    )
    # db.add ... db.commit ... db.refresh ... işlemleri crud'da olacak
    # Bu sadece bir placeholder
    logger.info(f"[INFO] Placeholder: School {school_id} settings for key '{settings_in.setting_key}' would be set to '{settings_in.setting_value}'. User: {current_user.username}")
    # raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="School specific settings CRUD not yet implemented.")
    return dummy_response # DUMMY

@router.get("/schools/{school_id}/app-settings/{setting_key}", response_model=Optional[schemas.SchoolAppSettings])
def get_school_app_setting(
    school_id: int,
    setting_key: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okul için belirli bir uygulama ayarını getirir.
    - Yetki: SUPER_ADMIN, o okulun SCHOOL_ADMIN'i, veya o okulda görevli bir kullanıcı.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or current_user.school_id == school_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this school's settings")

    # db_setting = crud.get_school_setting(db, school_id=school_id, setting_key=setting_key)
    # if not db_setting:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Setting '{setting_key}' not found for school {school_id}")
    # return db_setting
    logger.info(f"[INFO] Placeholder: Reading setting '{setting_key}' for school {school_id}. User: {current_user.username}")
    # raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="School specific settings CRUD not yet implemented.")
    return None # DUMMY

@router.get("/schools/{school_id}/app-settings", response_model=List[schemas.SchoolAppSettings])
def get_all_school_app_settings(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Belirli bir okulun tüm uygulama ayarlarını listeler.
    - Yetki: SUPER_ADMIN veya o okulun SCHOOL_ADMIN'i.
    """
    if not (current_user.role == schemas.UserRole.SUPER_ADMIN or 
            (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to list settings for this school")
    
    # settings_list = crud.get_all_school_settings(db, school_id=school_id)
    # return settings_list
    logger.info(f"[INFO] Placeholder: Listing all settings for school {school_id}. User: {current_user.username}")
    # raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="School specific settings CRUD not yet implemented.")
    return [] # DUMMY 