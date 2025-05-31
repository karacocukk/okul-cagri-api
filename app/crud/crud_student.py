from typing import List, Optional
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase
from app.models.student import Student
from app.models.class_ import Class # Teacher için Class importu
from app.models.user import User # User modelini import et
from app.schemas.student import StudentCreate, StudentUpdate

class CRUDStudent(CRUDBase[Student, StudentCreate, StudentUpdate]):
    def get_by_id_and_school_id(self, db: Session, student_id: int, school_id: int) -> Optional[Student]:
        return db.query(self.model).options(
            selectinload(Student.parents),
            selectinload(Student.assigned_class).selectinload(Class.teacher),
            selectinload(Student.school)
        ).filter(self.model.id == student_id, self.model.school_id == school_id).first()

    def get_by_student_number_and_school_id(self, db: Session, student_number: str, school_id: int) -> Optional[Student]:
        return db.query(self.model).options(
            selectinload(Student.parents),
            selectinload(Student.assigned_class).selectinload(Class.teacher),
            selectinload(Student.school)
        ).filter(self.model.student_number == student_number, self.model.school_id == school_id).first()

    def get_multi_by_school(
        self, db: Session, *, school_id: int, skip: int = 0, limit: int = 100
    ) -> List[Student]: # Mevcut get_students_by_school metodu, ismi standartlaştırıldı
        return (
            db.query(self.model).options(
                selectinload(Student.parents),
                selectinload(Student.assigned_class).selectinload(Class.teacher),
                selectinload(Student.school)
            )
            .filter(Student.school_id == school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    # CRUDBase.create metodu kullanılacak. StudentCreate şemasının 
    # okul_yonetim_api'deki gibi school_id içermesi beklenir.
    # create_with_school metodu kaldırıldı, CRUDBase.create yeterli olmalı.

    def create_with_parent(self, db: Session, *, obj_in: StudentCreate, parent_user: User) -> Student:
        """
        Yeni bir öğrenci oluşturur ve belirtilen veli ile ilişkilendirir.
        """
        # CRUDBase'in create metodunu kullanarak öğrenci objesini oluştur
        # Not: obj_in zaten school_id içeriyor olmalı (endpoint'te ayarlanmıştı)
        db_obj = super().create(db, obj_in=obj_in)
        
        # Öğrenciyi velinin öğrenciler listesine ekle
        # Bu işlem parent_student_association tablosuna kayıt ekleyecektir.
        parent_user.students.append(db_obj)
        db.add(parent_user) # Veli objesini session'a ekleyerek değişikliği takip etmesini sağla
        db.commit()
        db.refresh(db_obj) # Öğrenci objesini, ilişkilerle birlikte yenile
        db.refresh(parent_user) # Veli objesini de yenilemek iyi bir pratik olabilir
        return db_obj

    def get_multi_by_parent(
        self, db: Session, *, parent_id: int, skip: int = 0, limit: int = 100
    ) -> List[Student]:
        """
        Belirli bir veliye ait öğrencileri pagination ile getirir.
        """
        return (
            db.query(self.model)
            .join(self.model.parents)
            .filter(User.id == parent_id)
            .options(
                selectinload(Student.parents),
                selectinload(Student.assigned_class).selectinload(Class.teacher),
                selectinload(Student.school)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id_and_parent_id(self, db: Session, *, student_id: int, parent_id: int) -> Optional[Student]:
        """
        Belirli bir ID'ye sahip öğrenciyi getirir, ancak sadece belirtilen veliye aitse.
        """
        return (
            db.query(self.model)
            .join(self.model.parents)
            .filter(self.model.id == student_id, User.id == parent_id)
            .options(
                selectinload(Student.parents),
                selectinload(Student.assigned_class).selectinload(Class.teacher),
                selectinload(Student.school)
            )
            .first()
        )

    def update_in_school(
        self, db: Session, *, student_id: int, obj_in: StudentUpdate, school_id: int
    ) -> Optional[Student]:
        db_obj = self.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
        if db_obj:
            # Pydantic v2: obj_in.model_dump(exclude_unset=True)
            update_data = {k: v for k, v in obj_in.dict(exclude_unset=True).items() if hasattr(db_obj, k)}
            if 'school_id' in update_data: # school_id'nin bu yolla değiştirilmesini engelle
                del update_data['school_id']
            for field, value in update_data.items():
                setattr(db_obj, field, value)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        return None

    def remove_in_school(self, db: Session, *, student_id: int, school_id: int) -> Optional[Student]:
        db_obj = self.get_by_id_and_school_id(db, student_id=student_id, school_id=school_id)
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return db_obj
        return None

# student = CRUDStudent(Student) # __init__.py'de yönetilecek 