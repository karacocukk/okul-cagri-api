from fastapi import APIRouter
import logging # Loglama için eklendi

# Ana uygulama endpoint'leri
from app.api.v1.endpoints.login import router as login_router
from app.api.v1.endpoints.veliler import router as veliler_router
from app.api.v1.endpoints.ogrenciler import router as ogrenciler_router
from app.api.v1.endpoints.cagrilar import router as cagrilar_router
from app.api.v1.endpoints.ws import router as ws_router
from app.api.v1.endpoints.users import router as main_app_users_router
from app.api.v1.endpoints.schools import router as main_app_schools_router
from app.api.v1.endpoints.public import router as main_app_public_router

# Okul Yönetim API endpoint'leri
from app.api.v1.endpoints.school_admin.auth import router as school_admin_auth_router
from app.api.v1.endpoints.school_admin.users import users_router as school_admin_users_router # users_router olarak export edilmiş olabilir
from app.api.v1.endpoints.school_admin.students import router as school_admin_students_router
from app.api.v1.endpoints.school_admin.teachers import router as school_admin_teachers_router
from app.api.v1.endpoints.school_admin.classes import router as school_admin_classes_router
from app.api.v1.endpoints.school_admin.notifications import router as school_admin_notifications_router
from app.api.v1.endpoints.school_admin.settings import router as school_admin_settings_router
from app.api.v1.endpoints.school_admin.schools import router as school_admin_schools_router
from app.api.v1.endpoints.school_admin.public_router import router as school_admin_public_router # public_router olarak export edilmiş olabilir

api_router = APIRouter()

# TEST ENDPOINT for api_router itself
# @api_router.get("/ping-api-v1", status_code=200)
# async def ping_api_v1_router():
#     logging.info("[API_V1] /ping-api-v1 endpoint called!") 
#     return {"message": "pong from api_router in api_v1.py"}

# --- School Admin Router'larını Doğrudan Ana api_router'a Ekleme Başlangıç ---
# school_admin_base_router katmanı kaldırıldı.

api_router.include_router(school_admin_auth_router, prefix="/school-admin/auth", tags=["School Admin - Auth"])
api_router.include_router(school_admin_users_router, prefix="/school-admin/users", tags=["School Admin - Users"])

# /school-admin/schools path'i için school_admin_schools_module.router
# Bu router içinde muhtemelen "/" ve "/{school_id}" gibi pathler var.
api_router.include_router(school_admin_schools_router, prefix="/school-admin/schools", tags=["School Admin - Schools"])

# {school_id} içeren pathler için ayrı include_router çağrıları (önceki yapıya benzer)
# Bu modüllerin kendi içindeki pathler artık "/" (root) veya "/{student_id}" gibi olmalı,
# çünkü "/schools/{school_id}/students" prefix'i burada veriliyor.
api_router.include_router(school_admin_students_router, prefix="/school-admin/schools/{school_id}/students", tags=["School Admin - School Students"])
api_router.include_router(school_admin_teachers_router, prefix="/school-admin/schools/{school_id}/teachers", tags=["School Admin - School Teachers"])
api_router.include_router(school_admin_classes_router, prefix="/school-admin/schools/{school_id}/classes", tags=["School Admin - School Classes"])
api_router.include_router(school_admin_notifications_router, prefix="/school-admin/schools/{school_id}/notifications", tags=["School Admin - School Notifications"])

api_router.include_router(school_admin_settings_router, prefix="/school-admin/settings", tags=["School Admin - Application Settings"])
api_router.include_router(school_admin_public_router, prefix="/school-admin/public", tags=["School Admin - Public"])

# --- School Admin Router Yapılandırması Bitiş ---

# Diğer ana uygulama router'ları
api_router.include_router(login_router, tags=["login"])
api_router.include_router(main_app_users_router, prefix="/users", tags=["Main App - Users"])
api_router.include_router(main_app_schools_router, prefix="/schools", tags=["Main App - Schools"])
api_router.include_router(main_app_public_router, prefix="/public", tags=["Main App - Public"])
api_router.include_router(veliler_router, prefix="/veliler", tags=["Veliler"])
api_router.include_router(ogrenciler_router, prefix="/ogrenciler", tags=["Ogrenciler"])
api_router.include_router(cagrilar_router, prefix="/cagrilar", tags=["Cagrilar"])
api_router.include_router(ws_router, prefix="/ws", tags=["websocket"]) # Websocket için prefix /ws 