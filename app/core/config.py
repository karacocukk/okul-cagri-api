from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from typing import Optional, List, Union
from pydantic import AnyHttpUrl, validator

# Proje kök dizinini bul
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# .env dosyasını yükle
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path, verbose=False)

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Öğrenci Çağırma Sistemi"
    SECRET_KEY: str # .env dosyasından okunacak
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # İlk Süper Kullanıcı Bilgileri (.env'den okunacak)
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "admin123"
    FIRST_SUPERUSER_USERNAME: str = "admin"

    # Okul Konumu (.env'den okunacak)
    SCHOOL_LATITUDE: float
    SCHOOL_LONGITUDE: float
    MAX_DISTANCE_METERS: int

    # WebSocket için Sınıf PC Doğrulama Tokenı (.env'den okunacak)
    CLASSROOM_PC_TOKEN: str

    # Veritabanı (MySQL, .env'den okunacak - ZORUNLU ALANLAR)
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: Union[int, str] # Port int veya str olabilir
    DB_NAME: str
    
    SQLALCHEMY_DATABASE_URL: Optional[str] = None # Bu hala Optional kalabilir, çünkü aşağıda dinamik olarak atanıyor.

    @validator("SQLALCHEMY_DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str) and v: # Eğer doğrudan verilmişse onu kullan
            return v
        
        db_user = values.get("DB_USER")
        db_password = values.get("DB_PASSWORD")
        db_host = values.get("DB_HOST")
        db_port = values.get("DB_PORT")
        db_name = values.get("DB_NAME")

        # Tüm MySQL bağlantı bilgilerinin .env'de tanımlı olduğundan emin ol.
        # Pydantic zaten DB_USER vb. alanlar Optional olmadığı için eksikse hata verecektir.
        if not all([db_user, db_password, db_host, db_port, db_name]):
            # Bu hata mesajı aslında Pydantic'in kendi alan doğrulama hatalarından önce gelmeyebilir
            # veya gereksiz olabilir, çünkü DB_USER vb. zorunlu.
            # Ama ek bir kontrol olarak kalabilir veya kaldırılabilir.
            # Şimdilik Pydantic'in zorunlu alan kontrolüne güvenelim.
            # Eğer buraya gelinirse (ki gelmemeli), boş bir URL döndürmek yerine hata fırlatmak daha iyi.
             missing_vars = [key for key, value in values.items() if key.startswith("DB_") and not value]
             if missing_vars:
                 raise ValueError(f"Missing MySQL environment variables: {', '.join(missing_vars)}. Please check your .env file.")
        
        # MySQL bağlantı string'ini oluştur
        mysql_url = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        return mysql_url

    PROJECT_VERSION: str = "1.0.0"

    # Mobil uygulama için API URL'si (.env dosyasından okunacak)
    MOBILE_API_URL: Optional[AnyHttpUrl] = None

    # Loglama Ayarları
    LOG_LEVEL: str = "INFO" # Varsayılan, .env'den override edilebilir

    class Config:
        case_sensitive = True
        env_file = ".env" # Proje kök dizinindeki .env dosyasını kullanır
        env_file_encoding = 'utf-8'

settings = Settings() 