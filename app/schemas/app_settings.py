from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Okul veya Uygulama Ayarları için Şemalar
# Bu şemalar, okul bazlı veya genel uygulama ayarlarını yönetmek için kullanılabilir.

class SchoolAppSettingsBase(BaseModel):
    setting_key: str = Field(..., description="Ayarın anahtarı (örn: 'pickup_procedure')")
    setting_value: str = Field(..., description="Ayarın değeri (örn: 'gate_a_only')")
    # school_id, bu ayarın hangi okula ait olduğunu belirtir. Endpoint'ten gelebilir.

class SchoolAppSettingsCreate(SchoolAppSettingsBase):
    # school_id create sırasında path/body'den gelebilir veya router'da atanabilir.
    pass

class SchoolAppSettingsInDBBase(SchoolAppSettingsBase):
    id: int
    school_id: int # Bu ayarın hangi okula ait olduğu
    last_updated_by_user_id: Optional[int] = None # Ayarı son güncelleyen kullanıcı ID'si
    updated_at: datetime

    class Config:
        from_attributes = True

class SchoolAppSettings(SchoolAppSettingsInDBBase):
    pass

# Genel Uygulama Ayarları (Opsiyonel, eğer varsa)
# class GlobalSettingBase(BaseModel):
# key: str
# value: str

# class GlobalSettingCreate(GlobalSettingBase):
# pass

# class GlobalSetting(GlobalSettingBase):
# id: int
# class Config:
# from_attributes = True 