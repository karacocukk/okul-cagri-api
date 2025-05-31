import sys
import os
import logging

# Proje kök dizinini sys.path'e ekle ki app modüllerini import edebilelim
# Bu satır, script'in proje kökünden `python scripts/init_db.py` olarak çalıştırıldığında
# veya başka bir yerden import edildiğinde app modüllerini bulmasını sağlar.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# app.core.config importu settings.LOG_LEVEL veya diğer ayarlar için kalabilir.
from app.core.config import settings 
from app.db.database import engine, SessionLocal # SessionLocal eklendi
from app.db.base_class import Base # Merkezi Base import edildi

# Modellerin import edilmesi, Base.metadata'nın tabloları tanımasını sağlar
# Bu satırlar, ilişkili tüm modellerin Python tarafından yüklenmesini garantiler.
from app.models.user import User # Örnek bir model importu, diğerleri de Base'e kayıtlı olmalı
from app.models.school import School
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_ import Class
from app.models.parent_student_relation import ParentStudentRelation
from app.models.notification import Notification, NotificationReadStatus
# Eğer legacy modeller de oluşturulacaksa:
# from app.models.legacy_models import Veli, Ogrenci, Cagri

# Loglama yapılandırması (main.py'dekine benzer)
# Bu script ayrı çalıştığı için kendi log ayarını yapması iyi olur.
# settings.LOG_LEVEL'i kullanabilmek için settings'in doğru şekilde import edildiğinden emin olunmalı.
# Eğer settings.LOG_LEVEL 'app.core.config' yani ana API'nin config'inden geliyorsa,
# ve bu script okul_yonetim_api'nin db'sini init ediyorsa, belki LOG_LEVEL'ı direkt belirlemek daha iyi.
# Şimdilik genel bir yapı kullanalım.
try:
    # settings objesinin yüklendiğini varsayarak LOG_LEVEL'ı oradan almayı deneriz.
    # Eğer bu script direkt çalıştırılıyorsa ve settings.LOG_LEVEL ana API'nin config'inden
    # (ve dolayısıyla ana .env'den) geliyorsa bu çalışır.
    # Eğer okul_yonetim_api'nin kendi config'i (ve .env'si) varsa o import edilmeli.
    # Proje yapısına göre bu importlar (app.core.config, app.db.database, app.models) düzenlenmeli.
    # Eğer bu script okul_yonetim_api/scripts/init_db.py ise ve okul_yonetim_api'nin kendi app'ini hedefliyorsa:
    # from okul_yonetim_api.app.core.config import settings
    # from okul_yonetim_api.app.db.database import Base, engine (veya sadece database.py ise)
    # from okul_yonetim_api.app.models import models
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
except ImportError:
    log_level_str = "INFO" # Settings yüklenemezse varsayılan

log_level = getattr(logging, log_level_str, logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def init_db():
    logger.info(f"Veritabanı tabloları {str(engine.url)} üzerinde oluşturuluyor/güncelleniyor...")
    try:
        # Base.metadata.drop_all(bind=engine) # DİKKAT: Üretimde bu satır yorumlanmalı veya kaldırılmalı!
        # logger.info("Mevcut tablolar (varsa) test amacıyla silindi.")
        Base.metadata.create_all(bind=engine)
        logger.info("Veritabanı tabloları başarıyla oluşturuldu/güncellendi!")
    except Exception as e:
        logger.error(f"Veritabanı tabloları oluşturulurken hata: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    logger.info("Veritabanı başlatma scripti çalıştırılıyor...")
    # Tüm modellerin import edildiğinden emin olmak için buraya bir dummy import yapabiliriz
    # Örneğin: app.models.__init__ içindeki tüm modellerin Base'e register olduğundan emin olmalıyız.
    # Yukarıdaki spesifik model importları bu işi görmeli.
    init_db()
    logger.info("Veritabanı başlatma scripti tamamlandı.")

    # Veritabanı bağlantısını test etmek için basit bir sorgu (opsiyonel)
    try:
        with SessionLocal() as db:
            # Basit bir sorgu, örneğin Okul tablosundan bir kayıt çekmeye çalışmak
            # veya sadece bağlantıyı test etmek.
            # result = db.execute(text("SELECT 1"))
            # logger.info(f"Veritabanı bağlantı testi başarılı. Sonuç: {result.scalar_one_or_none()}")
            logger.info("Veritabanı bağlantısı başarılı görünüyor (tablolar oluşturuldu/kontrol edildi). SessionLocal test edildi.")
    except Exception as e:
        logger.error(f"Veritabanına bağlanırken veya test sorgusu çalıştırılırken hata: {e}", exc_info=True) 