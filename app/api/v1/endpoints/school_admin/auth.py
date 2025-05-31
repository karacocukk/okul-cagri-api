from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app import crud, schemas, models # app yerine okul_yonetim_api.app
from app.core import security # app yerine okul_yonetim_api.app
from app.core.config import settings
from app.dependencies import get_db, get_current_active_user # app yerine okul_yonetim_api.app

router = APIRouter(prefix="/auth")

@router.post("/login", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Kullanıcı adı ve şifre ile giriş yaparak access token alır.
    OAuth2PasswordRequestForm, 'username' ve 'password' alanlarını içerir.
    """
    # Kullanıcıyı kullanıcı adı ile doğrula
    # Not: crud.authenticate_user, username ve school_id alacak şekilde güncellenmeli
    # Şimdilik school_id olmadan, sadece username ile deniyoruz.
    # Okul kodu giriş ekranına eklendiğinde, o bilgi buraya da aktarılmalı.
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role, "school_id": user.school_id }, # role ve school_id eklendi
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "user_role": user.role, "school_id": user.school_id} # role ve school_id yanıta eklendi

@router.post("/login/test-token", response_model=schemas.User)
def test_token(current_user: models.User = Depends(get_current_active_user)):
    """
    Test token endpoint.
    """
    return current_user

# Mevcut login fonksiyonunu yorum satırına alalım veya silelim (bu geçici bir değişiklik)
# @router.post("/login", response_model=schemas.Token)
# async def login_for_access_token_original(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = crud.get_user_by_username(db, username=form_data.username)
#     if not user or not security.verify_password(form_data.password, user.password_hash): # security import edilmeli
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Geçersiz kullanıcı adı veya şifre",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"} 