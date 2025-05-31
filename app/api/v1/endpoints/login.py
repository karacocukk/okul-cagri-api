import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud
from app import schemas
from app.core import security
from app.api.deps import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/login/access-token", response_model=schemas.Token)
def login_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    logger.info(f"Attempting login for username from form: '{form_data.username}', password from form: '{form_data.password}'")
    try:
        user = crud.user.authenticate(db, username=form_data.username, password=form_data.password)
        logger.info(f"Authentication result for '{form_data.username}': User object: {user}")
    except Exception as e:
        logger.error(f"Error during crud.user.authenticate for {form_data.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during authentication process",
        )

    if not user:
        logger.warning(f"Failed login attempt for {form_data.username}: Incorrect username or password (user not found or password mismatch after authenticate call)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        logger.warning(f"Failed login attempt for {form_data.username}: Inactive user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    
    logger.info(f"User {form_data.username} authenticated successfully. Creating token...")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {"sub": user.username, "user_id": user.id}
    if user.school_id:
        token_data["school_id"] = user.school_id
        
    try:
        access_token = security.create_access_token(
            data=token_data, expires_delta=access_token_expires
        )
        logger.info(f"Access token created successfully for {form_data.username}")
    except Exception as e:
        logger.error(f"Error during security.create_access_token for {form_data.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during token creation",
        )
        
    return {"access_token": access_token, "token_type": "bearer"} 