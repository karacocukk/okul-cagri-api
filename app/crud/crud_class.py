from typing import List, Optional
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase
from app.models.class_ import Class
from app.models.teacher import Teacher # Öğretmen bilgisini yüklemek için
from app.models.student import Student # Öğrenci listesini yüklemek için
from app.models.school import School # Okul bilgisini yüklemek için
from app.schemas.class_ import ClassCreate, ClassUpdate

class CRUDClass(CRUDBase[Class, ClassCreate, ClassUpdate]):
    def get_by_id_and_school_id(self, db: Session, class_id: int, school_id: int) -> Optional[Class]:
        return db.query(self.model).options(
            selectinload(Class.teacher),
            selectinload(Class.students_in_class),
            selectinload(Class.school)
        ).filter(self.model.id == class_id, self.model.school_id == school_id).first()

    def get_by_name_and_school_id(self, db: Session, class_name: str, school_id: int) -> Optional[Class]:
        return db.query(self.model).options(
            selectinload(Class.teacher),
            selectinload(Class.students_in_class),
            selectinload(Class.school)
        ).filter(self.model.class_name == class_name, self.model.school_id == school_id).first()

    def get_multi_by_school(
        self, db: Session, *, school_id: int, skip: int = 0, limit: int = 100
    ) -> List[Class]:
        return (
            db.query(self.model).options(
                selectinload(Class.teacher),
                selectinload(Class.students_in_class),
                selectinload(Class.school)
            )
            .filter(Class.school_id == school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    # CRUDBase.create kullanılacak. ClassCreate şeması school_id içermeli.
    # Eski create_school_class metodu kaldırıldı.

    def update_in_school(
        self, db: Session, *, class_id: int, obj_in: ClassUpdate, school_id: int
    ) -> Optional[Class]:
        db_obj = self.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
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

    def remove_in_school(self, db: Session, *, class_id: int, school_id: int) -> Optional[Class]:
        db_obj = self.get_by_id_and_school_id(db, class_id=class_id, school_id=school_id)
        if db_obj:
            # TODO: Sınıf silinmeden önce öğrencilerin ve öğretmenin bu sınıftan çıkarılması gerekir.
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None

# crud_class = CRUDClass(Class) # __init__.py'de yönetilecek 