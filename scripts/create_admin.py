import logging
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy.orm import Session

# Proje kök dizinini sys.path'e ekle
PROJ_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJ_ROOT)

# .env dosyasını yükle (script kökünden bir üstteki .env'yi hedefler)
DOTENV_PATH = os.path.join(PROJ_ROOT, '.env')
load_dotenv(DOTENV_PATH)

# Loglama yapılandırması
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

if os.path.exists(DOTENV_PATH):
    logger.debug(f"Loaded .env from: {DOTENV_PATH}")
else:
    logger.warning(f".env file NOT found at {DOTENV_PATH}. Will rely on environment variables or defaults in config.py.")

# Proje kök dizinini sys.path\'e ekle ki app modüllerini import edebilelim
# Bu, app modülleri import edilmeden önce yapılmalı.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Şimdi app modüllerini (ve dolayısıyla config.py'yi ve settings objesini) import edebiliriz:
from sqlalchemy import create_engine # YENİ IMPORT
from sqlalchemy.orm import sessionmaker, Session # Session'ı da import edelim
# from app.db.database import SessionLocal, engine, Base # BUNLARI ARTIK KULLANMAYACAĞIZ
from app.db.database import Base # Sadece Base'i alalım
from app.models import models
from app.core.config import settings # settings'i import edelim

# Sadece gerekli CRUD fonksiyonlarını ve Şemaları import et
from app.crud import (
    get_school_by_name, create_school,
    get_user_by_username, create_user
)
from app.schemas import SchoolCreate, UserCreate, UserRole
from app.models import User # User modeli, crud.user.create dönüş tipini kontrol için veya direkt sorgu için

# --- MANUEL SETTINGS OVERRIDE FOR DB URL ---
db_user_env = os.getenv("DB_USER")
db_password_env = os.getenv("DB_PASSWORD")
db_host_env = os.getenv("DB_HOST")
db_port_env = os.getenv("DB_PORT")
db_name_env = os.getenv("DB_NAME")

# Default to SQLite if .env vars for MySQL are not fully set
# This logic is similar to config.py but explicit for this script
if all([db_user_env, db_password_env, db_host_env, db_port_env, db_name_env]):
    effective_db_url = f"mysql+mysqlconnector://{db_user_env}:{db_password_env}@{db_host_env}:{db_port_env}/{db_name_env}?charset=utf8mb4"
    logger.debug(f"[create_admin.py]: Using MySQL URL for script: {effective_db_url}")
else:
    effective_db_url = "sqlite:///./default.db" # Fallback to local SQLite
    logger.debug(f"[create_admin.py]: Using SQLite URL for script: {effective_db_url}")
    # Eğer SQLite kullanıyorsak, settings'i de güncelleyelim ki tutarlı olsun (gerçi engine'i direkt kullanacağız)
    if settings.SQLALCHEMY_DATABASE_URL != effective_db_url:
        settings.SQLALCHEMY_DATABASE_URL = effective_db_url

# Script'e özel engine ve SessionLocal oluştur
engine_script = create_engine(effective_db_url)
SessionLocal_script = sessionmaker(autocommit=False, autoflush=False, bind=engine_script)
# --- END MANUEL SETTINGS OVERRIDE & LOCAL ENGINE --- 

def create_first_superuser(db: Session) -> None:
    logger.info("İlk süper kullanıcı oluşturuluyor...")
    email = settings.FIRST_SUPERUSER_EMAIL
    password = settings.FIRST_SUPERUSER_PASSWORD
    username = settings.FIRST_SUPERUSER_USERNAME or email.split('@')[0]

    user = get_user_by_username(db, username=username)
    if not user:
        if db_school:  # Okul var olmalı
            user_in = UserCreate(
                username=username,
                email=email,
                password=password,
                full_name="Süper Admin",
                role=UserRole.SUPER_ADMIN,
                school_id=db_school.id,  # Süper adminin belirli bir okulu olmalı
                is_active=True,
                initial_password_changed=True # İlk kurulumda şifre değişmiş kabul edilebilir
            )
            user = create_user(db, user=user_in)
            logger.info(f"Süper kullanıcı '{user.username}' (Email: {user.email}) başarıyla oluşturuldu.")
        else:
            logger.error(f"HATA: '{settings.FIRST_SUPERUSER_EMAIL}' bulunamadığı için süper kullanıcı oluşturulamadı.")
            return
    else:
        logger.info(f"Süper kullanıcı '{user.username}' (Email: {user.email}) zaten mevcut.")

def main():
    logger.info("Veritabanı bağlantısı kuruluyor ve ilk süper kullanıcı oluşturuluyor...")
    logger.debug(f"Kullanılacak veritabanı URL'si (script engine): {engine_script.url}") 
    
    db_script = SessionLocal_script() # Lokal session kullan
    try:
        logger.debug("models.Base.metadata.create_all(bind=engine_script) ÇAĞIRILMADAN ÖNCE")
        Base.metadata.create_all(bind=engine_script) # Lokal engine kullan
        logger.debug("models.Base.metadata.create_all(bind=engine_script) ÇAĞIRILDIKTAN SONRA - Hata yoksa tablolar oluşturulmuş/kontrol edilmiş olmalı.")
        create_first_superuser(db_script) # Lokal session'ı geçir
        db_script.commit() # Eğer create_first_superuser içinde commit yapılmıyorsa burada yapılmalı.
    except Exception as e:
        logger.error(f"İlk süper kullanıcı oluşturma sırasında bir hata oluştu: {e}", exc_info=True)
        db_script.rollback() # Hata durumunda yapılan işlemleri geri al
    finally:
        logger.info("Veritabanı bağlantısı kapatıldı.")
        db_script.close()

if __name__ == "__main__":
    main() 