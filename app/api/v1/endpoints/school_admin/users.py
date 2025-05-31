from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
import logging

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user
from app.core import security

users_router = APIRouter()

logger = logging.getLogger(__name__)

@users_router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_new_user_admin(
    user_in: schemas.UserCreate, 
    db: Session = Depends(get_db),
):
    db_user_by_username = crud.user.get_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail=f"'{user_in.username}' kullanıcı adı zaten mevcut.")
    if user_in.email:
        db_user_by_email = crud.user.get_by_email(db, email=user_in.email)
        if db_user_by_email:
            raise HTTPException(status_code=400, detail=f"'{user_in.email}' e-posta adresi zaten kayıtlı.")
    
    created_user = crud.user.create(db=db, obj_in=user_in)
    return created_user

@users_router.get("/me", response_model=schemas.User)
async def read_current_user_me_admin(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@users_router.put("/me", response_model=schemas.User)
async def update_current_user_me_admin(
    user_in: schemas.UserUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı veya güncelleme başarısız.")
    return updated_user

@users_router.post("/me/change-password", response_model=schemas.User)
async def change_current_user_password_me_admin(
    password_data: schemas.UserPasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if not security.verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış.")
    if password_data.current_password == password_data.new_password:
        raise HTTPException(status_code=400, detail="Yeni şifre mevcut şifre ile aynı olamaz.")
    
    updated_user = crud.user.update_password(db, db_obj=current_user, new_password=password_data.new_password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Şifre güncelleme sırasında bir hata oluştu.")
    return updated_user

@users_router.get("/list-all", response_model=List[schemas.User])
async def read_all_users_admin(
    skip: int = 0, 
    limit: int = 100, 
    school_id: Optional[int] = None,
    role: Optional[schemas.UserRole] = None,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    logger.info(f"[API] read_all_users_admin çağrıldı. school_id: {school_id}, role: {role.value if role else 'None'}")
    users = crud.user.get_multi_filtered(
        db, skip=skip, limit=limit, school_id=school_id, role=role.value if role else None
    )
    logger.info(f"[API] get_multi_filtered {len(users)} kullanıcı döndürdü.")
    return users

@users_router.post("/list-all", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_user_admin(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    """
    Create a new user (admin context).
    """
    logger.info(f"[API] create_user_admin çağrıldı. username: {user_in.username}, role: {user_in.role}")
    
    # Check if username exists
    db_user_by_username = crud.user.get_by_username(db, username=user_in.username)
    if db_user_by_username:
        raise HTTPException(status_code=400, detail=f"'{user_in.username}' kullanıcı adı zaten mevcut.")
    
    # Check if email exists (if provided)
    if user_in.email:
        db_user_by_email = crud.user.get_by_email(db, email=user_in.email)
        if db_user_by_email:
            raise HTTPException(status_code=400, detail=f"'{user_in.email}' e-posta adresi zaten kayıtlı.")
    
    # Create user
    created_user = crud.user.create(db=db, obj_in=user_in)
    logger.info(f"[API] User created with ID: {created_user.id}")
    return created_user

@users_router.get("/{user_id}", response_model=schemas.User)
async def read_user_by_id_admin(
    user_id: int, 
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    db_user = crud.user.get(db, id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return db_user

@users_router.put("/{user_id}", response_model=schemas.User)
async def update_user_by_id_admin(
    user_id: int,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    db_user = crud.user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    updated_user = crud.user.update(db, db_obj=db_user, obj_in=user_in)
    return updated_user

@users_router.get("/me/students", response_model=List[schemas.Student])
async def get_my_students_admin_context(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != schemas.UserRole.PARENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlem sadece veliler için geçerlidir.")
    students = crud.parent_student_relation.get_students_of_parent(db, parent_user_id=current_user.id)
    return students if students else []

@users_router.get("/{user_id}/students", response_model=List[schemas.Student])
async def get_students_for_specific_user_admin_context(
    user_id: int,
    db: Session = Depends(get_db),
):
    target_user = crud.user.get(db, id=user_id)
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hedef kullanıcı bulunamadı.")
    if target_user.role != schemas.UserRole.PARENT:
        return [] 
    students = crud.parent_student_relation.get_students_of_parent(db, parent_user_id=user_id)
    return students if students else []

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
UPLOAD_PROFILE_PICS_DIR = STATIC_DIR / "profile_pics"

def ensure_upload_dirs_exist():
    if not STATIC_DIR.exists(): STATIC_DIR.mkdir(parents=True, exist_ok=True)
    if not UPLOAD_PROFILE_PICS_DIR.exists(): UPLOAD_PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)

@users_router.post("/me/profile-picture", response_model=schemas.User)
async def upload_profile_picture_for_current_user_admin(
    file: UploadFile = File(..., description="Yüklenecek profil resmi (JPEG, PNG)"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    ensure_upload_dirs_exist()
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya türü. Sadece JPG veya PNG.")
    
    if current_user.profile_image_url:
        try:
            old_file_path_relative = current_user.profile_image_url.replace("/static/", "", 1)
            old_file_path_absolute = STATIC_DIR / old_file_path_relative
            if old_file_path_absolute.exists() and old_file_path_absolute.is_file():
                old_file_path_absolute.unlink()
        except Exception as e:
            logger.error(f"Eski profil resmi silinirken hata: {e}", exc_info=True)

    new_filename = f"user_{current_user.id}_{Path(file.filename).stem}_{os.urandom(4).hex()}{file_extension}"
    file_path = UPLOAD_PROFILE_PICS_DIR / new_filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Dosya kaydedilirken bir hata oluştu: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Dosya kaydedilemedi.")
    finally:
        file.file.close()

    profile_image_url_for_db = f"/static/profile_pics/{new_filename}"
    user_update_schema = schemas.UserUpdate(profile_image_url=profile_image_url_for_db)
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=user_update_schema)
    return updated_user

@users_router.post("/{user_id}/profile-picture", response_model=schemas.User)
async def upload_profile_picture_for_user_admin(
    user_id: int,
    file: UploadFile = File(..., description="Yüklenecek profil resmi (JPEG, PNG)"),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    target_user = crud.user.get(db, id=user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Hedef kullanıcı bulunamadı.")

    ensure_upload_dirs_exist()
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Desteklenmeyen dosya türü. Sadece JPG veya PNG.")

    if target_user.profile_image_url:
        try:
            old_file_path_relative = target_user.profile_image_url.replace("/static/", "", 1)
            old_file_path_absolute = STATIC_DIR / old_file_path_relative
            if old_file_path_absolute.exists() and old_file_path_absolute.is_file():
                old_file_path_absolute.unlink()
        except Exception as e:
            logger.error(f"Eski profil resmi silinirken hata: {e}", exc_info=True)

    new_filename = f"user_{target_user.id}_{Path(file.filename).stem}_{os.urandom(4).hex()}{file_extension}"
    file_path = UPLOAD_PROFILE_PICS_DIR / new_filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Dosya kaydedilirken bir hata oluştu: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Dosya kaydedilemedi.")
    finally:
        file.file.close()

    profile_image_url_for_db = f"/static/profile_pics/{new_filename}"
    user_update_schema = schemas.UserUpdate(profile_image_url=profile_image_url_for_db)
    updated_user = crud.user.update(db, db_obj=target_user, obj_in=user_update_schema)
    return updated_user

@users_router.delete("/{user_id}", response_model=schemas.User)
async def delete_user_by_id_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_active_user)
):
    db_user = crud.user.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    if db_user.id == current_admin.id:
        raise HTTPException(status_code=403, detail="Aktif admin kendini silemez.")
    # İsteğe bağlı: Kullanıcıya bağlı verilerin silinmesi veya anonimleştirilmesi burada ele alınabilir.
    # Örneğin, eğer bu kullanıcı bir öğretmense ve sınıfları varsa ne yapılmalı?
    # Ya da bir veli ise ve öğrencileri varsa?
    # Şimdilik sadece kullanıcıyı siliyoruz.
    deleted_user = crud.user.remove(db, id=user_id)
    if not deleted_user:
        # Bu durum normalde crud.user.remove bir istisna fırlatmazsa pek yaşanmaz
        # ama id bulunamazsa None dönebilir (gerçi yukarıda kontrol ettik)
        raise HTTPException(status_code=500, detail="Kullanıcı silinirken bir hata oluştu.")
    return deleted_user

# TEST ENDPOINT
@users_router.get("/ping-users", status_code=200)
async def ping_users_router():
    logger.info("[API] /ping-users endpoint in school_admin.users called!")
    return {"message": "pong from school_admin users router specific ping"}

@users_router.get("/test-ping", status_code=200)
async def test_ping_endpoint():
    logger.info("[API] /test-ping endpoint called!")
    return {"message": "pong from school_admin users router"}

@users_router.post("/create-test-admin", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_test_admin(
    db: Session = Depends(get_db)
):
    """
    Test için bir admin kullanıcısı oluşturur.
    """
    test_user = schemas.UserCreate(
        username="testadmin",
        password="test123",
        full_name="Test Admin",
        email="test@example.com",
        role=schemas.UserRole.SCHOOL_ADMIN,
        school_id=1
    )
    
    # Kullanıcı zaten var mı kontrol et
    existing_user = crud.user.get_by_username(db, username=test_user.username)
    if existing_user:
        return existing_user
        
    # Yeni kullanıcı oluştur
    created_user = crud.user.create(db=db, obj_in=test_user)
    return created_user

@users_router.post("/create-test-parent", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def create_test_parent(
    db: Session = Depends(get_db)
):
    """
    Test için bir veli kullanıcısı oluşturur.
    """
    test_user = schemas.UserCreate(
        username="testparent",
        password="test123",
        full_name="Test Parent",
        email="parent@example.com",
        role=schemas.UserRole.PARENT,
        school_id=1
    )
    
    # Kullanıcı zaten var mı kontrol et
    existing_user = crud.user.get_by_username(db, username=test_user.username)
    if existing_user:
        return existing_user
        
    # Yeni kullanıcı oluştur
    created_user = crud.user.create(db=db, obj_in=test_user)
    return created_user