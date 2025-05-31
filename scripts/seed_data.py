import logging
import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Proje kök dizinini sys.path'e ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Bu script ana API'nin (app) veritabanını ve ayarlarını kullanacak şekilde ayarlandı.
# Eğer okul_yonetim_api'yi hedeflemesi gerekiyorsa importlar düzenlenmeli.
from app.core.config import settings
from app.db.database import SessionLocal, engine, Base # Ana API'nin database modülü
from app.models import models as app_models # Ana API'nin modelleri (User, Veli, Ogrenci, Cagri)
from app.schemas import schemas as app_schemas # Ana API'nin şemaları
from app.core.security import get_password_hash
from app import crud

# Loglama yapılandırması
log_level_str = os.getenv("LOG_LEVEL", "INFO")
log_level = getattr(logging, log_level_str.upper(), logging.INFO)
logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Veritabanı tablolarını oluştur (eğer yoksa)
# Normalde init_db.py ile yapılır ama script tek başına çalışsın diye eklenebilir
# models.Base.metadata.create_all(bind=engine) 

def create_school(db: Session, name: str, unique_code: str) -> app_models.Okul:
    db_school = db.query(app_models.Okul).filter(app_models.Okul.unique_code == unique_code).first()
    if not db_school:
        db_school = app_models.Okul(name=name, unique_code=unique_code)
        db.add(db_school)
        db.commit()
        db.refresh(db_school)
        logger.info(f"Okul oluşturuldu: {db_school.name} (ID: {db_school.id})")
    else:
        logger.info(f"Okul zaten var: {db_school.name} (ID: {db_school.id})")
    return db_school

def create_admin(db: Session, school_id: int, username: str, password_plain: str) -> app_models.User:
    db_user = db.query(app_models.User).filter(app_models.User.username == username, app_models.User.school_id == school_id).first()
    if not db_user:
        hashed_password = get_password_hash(password_plain)
        db_user = app_models.User(
            username=username,
            password_hash=hashed_password,
            email=f"{username}@example.com", # Örnek e-posta
            full_name=f"{username.capitalize()} Admin",
            role=app_schemas.UserRole.ADMIN, 
            school_id=school_id,
            is_active=True,
            initial_password_changed = False # Admin için şifre değiştirme zorunluluğu olabilir
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"Admin kullanıcısı oluşturuldu: {db_user.username} (Okul ID: {school_id})")
    else:
        logger.info(f"Admin kullanıcısı zaten var: {db_user.username}")
    return db_user

def create_veli(db: Session, email: str, password_plain: str, full_name: str, school_id: int) -> app_models.Veli:
    db_veli = db.query(app_models.Veli).filter(app_models.Veli.email == email, app_models.Veli.school_id == school_id).first()
    if not db_veli:
        hashed_password = get_password_hash(password_plain)
        db_veli = app_models.Veli(
            email=email, 
            password_hash=hashed_password, 
            full_name=full_name, 
            school_id=school_id,
            is_active=True
        )
        db.add(db_veli)
        db.commit()
        db.refresh(db_veli)
        logger.info(f"Veli oluşturuldu: {db_veli.email}")
    else:
        logger.info(f"Veli zaten var: {db_veli.email}")
    return db_veli

def create_ogrenci(db: Session, veli_id: int, okul_id: int, ad: str, soyad: str, numara: str, sinif: str) -> app_models.Ogrenci:
    db_ogrenci = db.query(app_models.Ogrenci).filter(app_models.Ogrenci.numara == numara, app_models.Ogrenci.okul_id == okul_id).first()
    if not db_ogrenci:
        db_ogrenci = app_models.Ogrenci(
            ad=ad, 
            soyad=soyad, 
            numara=numara, 
            sinif=sinif, 
            veli_id=veli_id, 
            okul_id=okul_id
        )
        db.add(db_ogrenci)
        db.commit()
        db.refresh(db_ogrenci)
        logger.info(f"Öğrenci eklendi: {ad} (Veli ID: {veli_id}, Okul ID: {okul_id})")
    else:
        logger.info(f"Öğrenci zaten var: {numara}")
    return db_ogrenci    

def seed_data(db: Session):
    logger.info("Başlangıç verileri ekleniyor...")

    # 1. Süper Admin Kullanıcısı Oluştur
    super_admin_email = settings.FIRST_SUPERUSER_EMAIL
    super_admin_password = settings.FIRST_SUPERUSER_PASSWORD
    user_in_create = app_schemas.UserCreate(
        username=super_admin_email.split("@")[0], # veya settings.FIRST_SUPERUSER_USERNAME
        email=super_admin_email,
        password=super_admin_password,
        full_name="Süper Admin",
        role=app_schemas.UserRole.SUPER_ADMIN,
        school_id=None, # Süper adminin okulu olmaz
        is_active=True,
        initial_password_changed=True # Süper admin için True varsayalım
    )
    super_admin_user = crud.user.get_by_email(db, email=super_admin_email)
    if not super_admin_user:
        super_admin_user = crud.user.create(db, obj_in=user_in_create)
        logger.info(f"Süper admin kullanıcısı oluşturuldu: {super_admin_user.email}")
    else:
        logger.info(f"Süper admin kullanıcısı zaten var: {super_admin_user.email}")

    # 2. Okul Oluştur
    school1_in = app_schemas.SchoolCreate(name="Gazi İlkokulu", unique_code="GAZIILK001", address="Ankara")
    school1 = crud.school.get_school_by_unique_code(db, unique_code=school1_in.unique_code)
    if not school1:
        school1 = crud.school.create(db, obj_in=school1_in)
        logger.info(f"Okul oluşturuldu: {school1.name}")
    else:
        logger.info(f"Okul zaten var: {school1.name}")

    school2_in = app_schemas.SchoolCreate(name="Atatürk Lisesi", unique_code="ATALIS002", address="İstanbul")
    school2 = crud.school.get_school_by_unique_code(db, unique_code=school2_in.unique_code)
    if not school2:
        school2 = crud.school.create(db, obj_in=school2_in)
        logger.info(f"Okul oluşturuldu: {school2.name}")
    else:
        logger.info(f"Okul zaten var: {school2.name}")

    if not school1: # Eğer okul oluşturulamadıysa devam etme
        logger.error("Gazi İlkokulu oluşturulamadığı için diğer veriler eklenemiyor.")
        return

    # 3. Gazi İlkokulu için Okul Yöneticisi Oluştur
    school1_admin_email = "admin_gazi@example.com"
    school1_admin_in = app_schemas.UserCreate(
        username="admin_gazi", email=school1_admin_email, password="admin123", 
        full_name="Gazi Okul Yöneticisi", role=app_schemas.UserRole.SCHOOL_ADMIN, school_id=school1.id
    )
    school1_admin = crud.user.get_by_email_and_school_id(db, email=school1_admin_email, school_id=school1.id)
    if not school1_admin:
        school1_admin = crud.user.create(db, obj_in=school1_admin_in)
        logger.info(f"Okul yöneticisi oluşturuldu: {school1_admin.email} (Okul: {school1.name})")
    else:
        logger.info(f"Okul yöneticisi zaten var: {school1_admin.email} (Okul: {school1.name})")

    # 4. Gazi İlkokulu için Öğretmenler Oluştur
    teacher1_s1_email = "hoca1_gazi@example.com"
    teacher1_s1_user_in = app_schemas.UserCreate(username="hoca1_gazi", email=teacher1_s1_email, password="hoca123", full_name="Ayşe Öğretmen", role=app_schemas.UserRole.TEACHER, school_id=school1.id)
    teacher1_s1_user = crud.user.get_by_email_and_school_id(db, email=teacher1_s1_email, school_id=school1.id)
    if not teacher1_s1_user:
        teacher1_s1_user = crud.user.create(db, obj_in=teacher1_s1_user_in)
        logger.info(f"Öğretmen kullanıcısı oluşturuldu: {teacher1_s1_user.email}")
        # Öğretmen profili oluştur
        teacher1_s1_profile_in = app_schemas.TeacherCreate(user_id=teacher1_s1_user.id, school_id=school1.id, department="Sınıf Öğretmeni")
        crud.teacher.create_with_user(db, obj_in=teacher1_s1_profile_in) # create_with_user gibi bir metod olmalı
        logger.info(f"Öğretmen profili oluşturuldu: {teacher1_s1_user.full_name}")
    else:
        logger.info(f"Öğretmen kullanıcısı zaten var: {teacher1_s1_user.email}")
        # Profil var mı kontrol et, yoksa oluştur
        db_teacher_profile = crud.teacher.get_by_user_id(db, user_id=teacher1_s1_user.id)
        if not db_teacher_profile:
            teacher1_s1_profile_in = app_schemas.TeacherCreate(user_id=teacher1_s1_user.id, school_id=school1.id, department="Sınıf Öğretmeni")
            crud.teacher.create_with_user(db, obj_in=teacher1_s1_profile_in)
            logger.info(f"Varolan kullanıcı için öğretmen profili oluşturuldu: {teacher1_s1_user.full_name}")

    # 5. Gazi İlkokulu için Sınıflar Oluştur
    class1_s1_in = app_schemas.ClassCreate(class_name="1-A", school_id=school1.id, teacher_id=teacher1_s1_user.teacher_profile.id if teacher1_s1_user and hasattr(teacher1_s1_user, 'teacher_profile') and teacher1_s1_user.teacher_profile else None)
    class1_s1 = crud.class_.get_by_name_and_school_id(db, class_name=class1_s1_in.class_name, school_id=school1.id)
    if not class1_s1:
        class1_s1 = crud.class_.create(db, obj_in=class1_s1_in)
        logger.info(f"Sınıf oluşturuldu: {class1_s1.class_name} (Okul: {school1.name})")
    else:
        logger.info(f"Sınıf zaten var: {class1_s1.class_name}")

    # 6. Gazi İlkokulu için Veliler ve Öğrenciler Oluştur
    parent1_s1_email = "veli1_gazi@example.com"
    parent1_s1_user_in = app_schemas.UserCreate(username="veli1_gazi", email=parent1_s1_email, password="veli123", full_name="Ahmet Yılmaz", role=app_schemas.UserRole.PARENT, school_id=school1.id)
    parent1_s1_user = crud.user.get_by_email_and_school_id(db, email=parent1_s1_email, school_id=school1.id)
    if not parent1_s1_user:
        parent1_s1_user = crud.user.create(db, obj_in=parent1_s1_user_in)
        logger.info(f"Veli kullanıcısı oluşturuldu: {parent1_s1_user.email}")
    else:
        logger.info(f"Veli kullanıcısı zaten var: {parent1_s1_user.email}")

    if parent1_s1_user and class1_s1:
        student1_s1_in = app_schemas.StudentCreate(student_number="101", first_name="Can", last_name="Yılmaz", school_id=school1.id, class_id=class1_s1.id)
        student1_s1 = crud.student.get_by_student_number_and_school_id(db, student_number=student1_s1_in.student_number, school_id=school1.id)
        if not student1_s1:
            student1_s1 = crud.student.create(db, obj_in=student1_s1_in)
            logger.info(f"Öğrenci oluşturuldu: {student1_s1.first_name} {student1_s1.last_name}")
            # Veli-Öğrenci ilişkisi
            crud.parent_student_relation.add_parent_to_student(db, student_id=student1_s1.id, parent_user_id=parent1_s1_user.id, school_id=school1.id)
            logger.info(f"Veli ({parent1_s1_user.full_name}) öğrenciye ({student1_s1.first_name}) atandı.")
        else:
            logger.info(f"Öğrenci zaten var: {student1_s1.student_number}")
            # İlişki var mı kontrol et, yoksa ekle
            is_linked = crud.parent_student_relation.is_parent_linked_to_student(db, parent_user_id=parent1_s1_user.id, student_id=student1_s1.id)
            if not is_linked:
                crud.parent_student_relation.add_parent_to_student(db, student_id=student1_s1.id, parent_user_id=parent1_s1_user.id, school_id=school1.id)
                logger.info(f"Varolan öğrenciye veli atandı: {student1_s1.first_name} -> {parent1_s1_user.full_name}")

    logger.info("Başlangıç verileri ekleme tamamlandı.")

def main():
    logger.info("Veritabanı bağlantısı kuruluyor ve test verileri ekleniyor...")
    db: Session = SessionLocal()
    try:
        seed_data(db)
    except IntegrityError as e:
        logger.error(f"Veri ekleme sırasında IntegrityError (örn: benzersiz kısıtlama ihlali): {e}", exc_info=False) # exc_info=False kısa hata için
        db.rollback() # Hata durumunda rollback yap
    except Exception as e:
        logger.error(f"Beklenmedik bir hata oluştu: {e}", exc_info=True)
        db.rollback()
    finally:
        logger.info("Veritabanı bağlantısı kapatılıyor.")
        db.close()

if __name__ == "__main__":
    main() 