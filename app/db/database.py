from sqlalchemy import create_engine
# from sqlalchemy.ext.declarative import declarative_base # Kaldırıldı
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base_class import Base # YENİ IMPORT

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,   # Bağlantı kopmuşsa otomatik yenile
    pool_size=10,         # Aynı anda açık tutulacak max bağlantı
    max_overflow=20,      # Havuz dolunca açılacak ek bağlantı
    pool_timeout=30,      # Bağlantı bekleme süresi (saniye)
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base() # KALDIRILDI, ARTIK base_class.py'DAN GELİYOR

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 