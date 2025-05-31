from typing import List, Any
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.models.call import CallStatusEnum
from app.api import deps
from app.core.connection_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Yeni bağımlılık: Aktif ve rolü PARENT olan kullanıcıyı getirir
async def get_current_active_parent(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> models.User:
    if current_user.role != models.UserRoleEnum.PARENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlemi yapmak için veli olmalısınız."
        )
    return current_user

@router.post("/", response_model=schemas.call.Call, status_code=status.HTTP_201_CREATED)
async def create_new_call(
    *,
    db: Session = Depends(deps.get_db),
    call_in: schemas.call.CallCreate, # Yeni şema
    current_parent: models.User = Depends(get_current_active_parent) # Yeni bağımlılık
) -> Any:
    """
    Create a new call for a student by the logged-in parent.
    """
    created_call_db = crud.call.create_call_for_parent(db=db, obj_in=call_in, parent_user=current_parent)
    
    if not created_call_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Çağrı oluşturulamadı. Öğrenci bilgileri geçersiz veya eksik."
        )

    call_with_details = crud.call.get_call_with_details(db, call_id=created_call_db.id)
    if not call_with_details or not call_with_details.student or not call_with_details.class_:
         logger.error(f"Call {created_call_db.id} için detaylar veya sınıf bilgisi yüklenemedi.")
         return call_with_details 

    call_schema_for_ws = schemas.call.Call.model_validate(call_with_details)
    call_dict_for_ws = call_schema_for_ws.model_dump(mode="json")
    message_payload = {"type": "new_call", "data": call_dict_for_ws}
    
    try:
        class_identifier_for_ws = call_with_details.class_.class_name if call_with_details.class_ else f"class_id_{call_with_details.class_id}"
        await manager.broadcast_to_sinif(json.dumps(message_payload), class_identifier_for_ws)
        logger.info(f"New call notification sent to class: {class_identifier_for_ws}, Call ID {created_call_db.id}")
    except Exception as e:
        logger.error(f"Error broadcasting new call to WebSocket for class {class_identifier_for_ws}: {e}")

    return call_with_details

@router.get("/class/{class_id}", response_model=List[schemas.call.Call])
async def read_calls_by_class(
    class_id: int,
    db: Session = Depends(deps.get_db),
    active_only: bool = Query(True, description="Sadece aktif (pending, acknowledged) çağrıları getir"),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    target_class = crud.class_.get(db, id=class_id)
    if not target_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sınıf bulunamadı")

    if not current_user.school_id or current_user.school_id != target_class.school_id:
        if current_user.role != models.UserRoleEnum.SUPER_ADMIN:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu sınıftaki çağrıları görme yetkiniz yok.")

    calls = crud.call.get_calls_by_class_id(
        db, 
        class_id=class_id, 
        school_id=target_class.school_id, 
        active_only=active_only
    )
    return calls

@router.get("/{call_id}", response_model=schemas.call.Call)
async def read_call_by_id(
    call_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    db_call = crud.call.get_call_with_details(db, call_id=call_id)
    if not db_call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Çağrı bulunamadı")

    if current_user.role == models.UserRoleEnum.PARENT:
        if db_call.parent_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu çağrıyı görme yetkiniz yok.")
    elif current_user.role in [models.UserRoleEnum.TEACHER, models.UserRoleEnum.SCHOOL_ADMIN]:
        if not current_user.school_id or db_call.school_id != current_user.school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu çağrıyı görme yetkiniz yok (farklı okul).")
    
    return db_call

@router.patch("/{call_id}/status", response_model=schemas.call.Call)
async def update_call_status(
    call_id: int,
    call_status_in: schemas.call.CallStatusUpdate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    db_call = crud.call.get(db, id=call_id)
    if not db_call:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Çağrı bulunamadı")

    new_status = call_status_in.status

    if current_user.role == models.UserRoleEnum.PARENT:
        if db_call.parent_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu çağrının durumunu değiştirme yetkiniz yok.")
        if db_call.status == CallStatusEnum.PENDING and new_status == CallStatusEnum.CANCELLED_BY_PARENT:
            pass
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Veli olarak çağrı durumu sadece '{CallStatusEnum.PENDING}' iken '{CallStatusEnum.CANCELLED_BY_PARENT}' olarak güncellenebilir.")
    
    elif current_user.role in [models.UserRoleEnum.TEACHER, models.UserRoleEnum.SCHOOL_ADMIN]:
        if not current_user.school_id or db_call.school_id != current_user.school_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu çağrının durumunu değiştirme yetkiniz yok (farklı okul).")
        
        allowed_transitions = {
            CallStatusEnum.PENDING: [CallStatusEnum.ACKNOWLEDGED, CallStatusEnum.CANCELLED_BY_SCHOOL],
            CallStatusEnum.ACKNOWLEDGED: [CallStatusEnum.COMPLETED, CallStatusEnum.CANCELLED_BY_SCHOOL]
        }
        if not (db_call.status in allowed_transitions and new_status in allowed_transitions[db_call.status]):
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Okul personeli olarak izin verilmeyen durum değişikliği: {db_call.status.value} -> {new_status.value}")
            
    elif current_user.role == models.UserRoleEnum.SUPER_ADMIN:
        pass 
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Çağrı durumunu değiştirme yetkiniz yok.")

    updated_call_db = crud.call.update_call_status(db=db, db_call=db_call, new_status=new_status)
    
    call_with_details = crud.call.get_call_with_details(db, call_id=updated_call_db.id)
    if call_with_details and call_with_details.class_:
        call_schema_for_ws = schemas.call.Call.model_validate(call_with_details)
        call_dict_for_ws = call_schema_for_ws.model_dump(mode="json")
        message_payload = {"type": "call_updated", "data": call_dict_for_ws}
        
        class_identifier_for_ws = call_with_details.class_.class_name if call_with_details.class_ else f"class_id_{call_with_details.class_id}"
        try:
            await manager.broadcast_to_sinif(json.dumps(message_payload), class_identifier_for_ws)
            logger.info(f"Call update notification sent to class: {class_identifier_for_ws}, Call ID {updated_call_db.id}, Status {new_status}")
        except Exception as e:
            logger.error(f"Error broadcasting call update to WebSocket for class {class_identifier_for_ws}: {e}")

    return updated_call_db

@router.get("/", response_model=List[schemas.call.Call])
async def read_all_calls_for_school_admin_or_superuser(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = Query(False, description="Sadece aktif (pending, acknowledged) çağrıları getir"),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    if current_user.role == models.UserRoleEnum.SUPER_ADMIN:
        query = db.query(models.Call)
        if active_only:
            query = query.filter(models.Call.status.in_([CallStatusEnum.PENDING, CallStatusEnum.ACKNOWLEDGED]))
        calls = query.order_by(models.Call.created_at.desc()).offset(skip).limit(limit).all()

    elif current_user.role == models.UserRoleEnum.SCHOOL_ADMIN and current_user.school_id:
        calls = crud.call.get_multi_by_school(
            db, school_id=current_user.school_id, active_only=active_only, skip=skip, limit=limit
        )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bu işlemi yapma yetkiniz yok.")
    return calls