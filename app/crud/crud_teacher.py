from typing import List, Optional
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase
from app.models.teacher import Teacher
from app.models.school import School # Okul bilgisini de yüklemek için
from app.models.class_ import Class # Sınıf bilgisini de yüklemek için
from app.schemas.teacher import TeacherCreate, TeacherUpdate

class CRUDTeacher(CRUDBase[Teacher, TeacherCreate, TeacherUpdate]):
    def get_by_id_and_school_id(self, db: Session, teacher_id: int, school_id: int) -> Optional[Teacher]:
        return db.query(self.model).options(
            selectinload(Teacher.assigned_classes),
            selectinload(Teacher.school)
        ).filter(self.model.id == teacher_id, self.model.school_id == school_id).first()

    def get_by_email_and_school_id(self, db: Session, email: str, school_id: int) -> Optional[Teacher]:
        return db.query(self.model).options(
            selectinload(Teacher.assigned_classes),
            selectinload(Teacher.school)
        ).filter(self.model.email == email, self.model.school_id == school_id).first()

    def get_by_phone_and_school_id(self, db: Session, phone_number: str, school_id: int) -> Optional[Teacher]:
        return db.query(self.model).options(
            selectinload(Teacher.assigned_classes),
            selectinload(Teacher.school)
        ).filter(self.model.phone_number == phone_number, self.model.school_id == school_id).first()

    def get_multi_by_school(
        self, db: Session, *, school_id: int, skip: int = 0, limit: int = 100
    ) -> List[Teacher]:
        return (
            db.query(self.model).options(
                selectinload(Teacher.assigned_classes),
                selectinload(Teacher.school)
            )
            .filter(Teacher.school_id == school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # CRUDBase.create kullanılacak. TeacherCreate şeması school_id içermeli.
    # CRUDBase.update kullanılacak. school_id güncellemesi genelde yapılmaz.
    # CRUDBase.remove kullanılacak. school_id ile filtreleme router seviyesinde yapılabilir veya 
    # remove_in_school gibi özel bir metod yazılabilir (aşağıdaki gibi).

    def update_in_school(
        self, db: Session, *, teacher_id: int, obj_in: TeacherUpdate, school_id: int
    ) -> Optional[Teacher]:
        db_obj = self.get_by_id_and_school_id(db, teacher_id=teacher_id, school_id=school_id)
        if db_obj:
            update_data = {k: v for k, v in obj_in.dict(exclude_unset=True).items() if hasattr(db_obj, k)}
            if 'school_id' in update_data:
                del update_data['school_id']
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        return None

    def remove_in_school(self, db: Session, *, teacher_id: int, school_id: int) -> Optional[Teacher]:
        db_obj = self.get_by_id_and_school_id(db, teacher_id=teacher_id, school_id=school_id)
        if db_obj:
            # TODO: Öğretmen silinmeden önce atanmış olduğu sınıflardan çıkarılmalı mı?
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None 