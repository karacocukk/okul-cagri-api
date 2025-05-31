import logging
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db import base  # Modellerin düzgün kaydedildiğinden emin olmak için gerekli
from app.db.base_class import Base
from app.models import User # User modelini import et
# School modelini ve şemasını import et
from app.models.school import School 
from app.schemas.school import SchoolCreate

logger = logging.getLogger(__name__)

# Varsayılan okul için sabitler
DEFAULT_SCHOOL_NAME = "Varsayılan Okul"
DEFAULT_SCHOOL_CODE = "DEFAULT_001"

def init_initial_data(db: Session) -> None:
    """
    İlk veritabanı başlatma işlemlerini gerçekleştirir.
    """
    logger.info("Ensuring all tables are created in the database...")
    try:
        Base.metadata.create_all(bind=db.get_bind())
        logger.info("Tables creation check/attempt complete.")
    except Exception as e:
        logger.error(f"Error during table creation: {e}", exc_info=True)
        raise

    logger.info("Starting database initialization with data...")

    # 1. Varsayılan Okul Kontrolü ve Oluşturma
    default_school = crud.school.get_school_by_unique_code(db, unique_code=DEFAULT_SCHOOL_CODE)
    if not default_school:
        logger.info(f"Default school with code '{DEFAULT_SCHOOL_CODE}' not found, creating...")
        school_in = SchoolCreate(name=DEFAULT_SCHOOL_NAME, unique_code=DEFAULT_SCHOOL_CODE, address="Merkez")
        try:
            default_school = crud.school.create(db, obj_in=school_in)
            logger.info(f"Default school '{default_school.name}' created successfully with ID: {default_school.id}")
        except Exception as e:
            logger.error(f"Error creating default school: {e}", exc_info=True)
            # Okul oluşturulamazsa devam etmek sorunlu olabilir, bu yüzden burada durabiliriz.
            raise
    else:
        logger.info(f"Default school '{default_school.name}' (ID: {default_school.id}) already exists.")

    # 2. Admin Kullanıcısı Oluşturma ve Okula Atama
    user_check = crud.user.get_by_username(db, username=settings.FIRST_SUPERUSER_USERNAME)
    
    superuser_school_id = default_school.id if default_school else None
    if not superuser_school_id:
        logger.error("Critical: Default school ID could not be determined. Superuser cannot be assigned to a school.")
        # Bu durumda süper kullanıcı okulsuz kalacak veya işlem durdurulabilir.
        # Şimdilik devam edelim ama bu ciddi bir konfigürasyon sorunudur.

    if not user_check:
        logger.info(f"Super user '{settings.FIRST_SUPERUSER_USERNAME}' not found, creating with school ID: {superuser_school_id}...")
        user_in = schemas.UserCreate(
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            role=schemas.UserRole.SUPER_ADMIN,
            is_active=True,
            username=settings.FIRST_SUPERUSER_USERNAME,
            full_name="Super Admin",
            school_id=superuser_school_id # Okul ID'sini ata
        )
        try:
            created_user = crud.user.create(db, obj_in=user_in)
            logger.info(f"Super user created successfully with ID: {created_user.id}, username: {created_user.username}, school_id: {created_user.school_id}")
        except Exception as e:
            logger.error(f"Error creating super user: {e}", exc_info=True)
            raise # Süper kullanıcı oluşturma kritik, hata varsa devam etme
    else:
        logger.info(f"Super user '{user_check.username}' (ID: {user_check.id}) already exists.")
        if user_check.school_id != superuser_school_id and superuser_school_id is not None:
            logger.info(f"Updating super user '{user_check.username}' school ID from {user_check.school_id} to {superuser_school_id}...")
            # Basit bir update için doğrudan set edip commit edebiliriz.
            # Daha karmaşık durumlar için crud.user.update gerekebilir.
            user_check.school_id = superuser_school_id
            db.add(user_check)
            db.commit()
            db.refresh(user_check)
            logger.info(f"Super user '{user_check.username}' school ID updated to {user_check.school_id}.")
        elif not user_check.school_id and superuser_school_id is not None:
            logger.info(f"Assigning school ID {superuser_school_id} to existing super user '{user_check.username}' who has no school ID...")
            user_check.school_id = superuser_school_id
            db.add(user_check)
            db.commit()
            db.refresh(user_check)
            logger.info(f"Super user '{user_check.username}' school ID set to {user_check.school_id}.")
        else:
            logger.info(f"Super user '{user_check.username}' school ID ({user_check.school_id}) is already consistent or default school not available.")

    logger.info("Database initialization completed.")

# Eğer bu script doğrudan çalıştırılırsa (örn: python -m app.db.init_db)
if __name__ == "__main__":
    from app.db.database import SessionLocal
    logging.basicConfig(level=logging.INFO)
    logger.info("Running init_db script directly...")
    db_session = SessionLocal()
    try:
        init_initial_data(db_session)
    finally:
        db_session.close()
    logger.info("init_db script finished.") 