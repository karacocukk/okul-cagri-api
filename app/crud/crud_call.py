from typing import List, Optional
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.call import Call, CallStatusEnum
from app.models.student import Student
from app.models.user import User, UserRoleEnum
from app.schemas.call import CallCreate, CallStatusUpdate # CallUpdate yerine CallStatusUpdate
from app.core.config import settings # Okul bölgesi kontrolü için
import logging # Loglama

logger = logging.getLogger(__name__)

class CRUDCall(CRUDBase[Call, CallCreate, CallStatusUpdate]): # Model, CreateSchema, UpdateSchema (CallStatusUpdate kullandık)
    
    def create_call_for_parent(self, db: Session, *, obj_in: CallCreate, parent_user: User) -> Optional[Call]:
        """
        Creates a call initiated by a parent for their student.
        Checks if the student belongs to the parent and is in a valid class.
        """
        if parent_user.role != UserRoleEnum.PARENT:
            logger.warning(f"User {parent_user.id} is not a parent, cannot create call.")
            return None # Veya HTTPException yükseltilebilir

        student = db.query(Student).options(joinedload(Student.assigned_class)).filter(Student.id == obj_in.student_id).first()
        if not student:
            logger.warning(f"Student with id {obj_in.student_id} not found for call creation.")
            return None
        
        # Öğrencinin bu veliye ait olup olmadığını kontrol et (ParentStudentRelation üzerinden)
        is_parent_of_student = False
        for p_student in parent_user.students: # User modelindeki 'students' ilişkisi
            if p_student.id == student.id:
                is_parent_of_student = True
                break
        
        if not is_parent_of_student:
            logger.warning(f"User {parent_user.id} is not a parent of student {student.id}.")
            return None

        if not student.assigned_class:
            logger.warning(f"Student {student.id} is not assigned to any class.")
            return None # Veya varsayılan bir durum/hata işleme

        # TODO: Okul bölgesi kontrolü eklenebilir (settings.MAX_DISTANCE_METERS)
        # Bu, velinin konumunu (latitude, longitude) obj_in içinde almayı gerektirir.
        # Şimdilik bu kontrolü atlıyoruz, eski cagrilar.py'de vardı.

        db_call = self.model(
            student_id=student.id,
            parent_user_id=parent_user.id,
            school_id=student.school_id,
            class_id=student.class_id, # Öğrencinin atanmış olduğu sınıfın ID'si
            status=CallStatusEnum.PENDING # Varsayılan durum
        )
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        logger.info(f"Call {db_call.id} created for student {student.id} by parent {parent_user.id}")
        return db_call

    def get_call_with_details(self, db: Session, call_id: int) -> Optional[Call]:
        return db.query(self.model).options(
            selectinload(Call.student),
            selectinload(Call.parent),
            selectinload(Call.school),
            selectinload(Call.class_)
        ).filter(self.model.id == call_id).first()

    def get_calls_by_class_id(
        self, db: Session, *, class_id: int, school_id: int, active_only: bool = True, skip: int = 0, limit: int = 100
    ) -> List[Call]:
        query = db.query(self.model).filter(Call.class_id == class_id, Call.school_id == school_id)
        if active_only:
            query = query.filter(Call.status.in_([CallStatusEnum.PENDING, CallStatusEnum.ACKNOWLEDGED]))
        return query.order_by(Call.created_at.desc()).offset(skip).limit(limit).all()

    def get_calls_by_parent_id(
        self, db: Session, *, parent_user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Call]:
        return db.query(self.model).filter(Call.parent_user_id == parent_user_id)\
            .order_by(Call.created_at.desc()).offset(skip).limit(limit).all()

    def get_calls_by_student_id(
        self, db: Session, *, student_id: int, school_id: int, active_only: bool = False, skip: int = 0, limit: int = 100
    ) -> List[Call]:
        query = db.query(self.model).filter(Call.student_id == student_id, Call.school_id == school_id)
        if active_only:
            query = query.filter(Call.status.in_([CallStatusEnum.PENDING, CallStatusEnum.ACKNOWLEDGED]))
        return query.order_by(Call.created_at.desc()).offset(skip).limit(limit).all()
        
    def update_call_status(self, db: Session, *, db_call: Call, new_status: CallStatusEnum) -> Call:
        db_call.status = new_status
        db.add(db_call)
        db.commit()
        db.refresh(db_call)
        logger.info(f"Call {db_call.id} status updated to {new_status}")
        return db_call

    def get_multi_by_school(
        self, db: Session, *, school_id: int, active_only: bool = False, skip: int = 0, limit: int = 100
    ) -> List[Call]:
        """
        Retrieves multiple calls for a given school.
        Can filter by active status (PENDING or ACKNOWLEDGED).
        """
        query = db.query(self.model).filter(Call.school_id == school_id)
        if active_only:
            query = query.filter(Call.status.in_([CallStatusEnum.PENDING, CallStatusEnum.ACKNOWLEDGED]))
        
        return query.order_by(Call.created_at.desc()).offset(skip).limit(limit).all()

# Örnek oluşturma (app/crud/__init__.py içinde yapılacak)
# call = CRUDCall(Call) 