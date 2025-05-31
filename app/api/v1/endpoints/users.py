from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas, models
from app.api import deps
from app.core.config import settings
from app.models import User

router = APIRouter()

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/me/children", response_model=list[schemas.Student])
async def get_my_children(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get children of the current user (if the user is a parent).
    Returns a list of students associated with the current parent user.
    """
    if current_user.role != schemas.UserRole.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only users with the PARENT role can access their children's information."
        )
    
    children = crud.student.get_students_by_parent_user_id(db, parent_user_id=current_user.id)
    if not children:
        return []
    return children 