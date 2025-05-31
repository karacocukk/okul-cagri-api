from typing import List, Optional
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase # CRUDBase'den direkt miras almayabilir, daha spesifik fonksiyonlar.
from app.models.parent_student_relation import ParentStudentRelation
from app.models.user import User
from app.models.student import Student
# Şema olarak ParentStudentRelation için özel bir Create/Update şemasına ihtiyaç olmayabilir,
# genelde sadece parent_user_id ve student_id üzerinden işlem yapılır.

class CRUDParentStudentRelation:
    def add_parent_to_student(self, db: Session, student_id: int, parent_user_id: int, school_id: int) -> Optional[Student]:
        # Öğrencinin ve velinin varlığını ve öğrencinin doğru okulda olduğunu kontrol et
        student = db.query(Student).filter(Student.id == student_id, Student.school_id == school_id).first()
        parent = db.query(User).filter(User.id == parent_user_id, User.role == 'parent').first() # User.school_id kontrolü de eklenebilir

        if not student or not parent:
            return None

        # Zaten var mı kontrolü
        existing_relation = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.student_id == student_id,
            ParentStudentRelation.parent_user_id == parent_user_id
        ).first()

        if existing_relation:
            # Belki hata döndürmek veya öğrenciyi direkt döndürmek daha iyi olabilir.
            return student # Veya mevcut ilişkiyi döndür

        db_relation = ParentStudentRelation(student_id=student_id, parent_user_id=parent_user_id)
        db.add(db_relation)
        db.commit()
        # db.refresh(db_relation) # Gerekirse
        db.refresh(student) # Öğrencinin parents listesinin güncellenmesi için
        return student

    def remove_parent_from_student(self, db: Session, student_id: int, parent_user_id: int, school_id: int) -> Optional[Student]:
        student = db.query(Student).filter(Student.id == student_id, Student.school_id == school_id).first()
        if not student:
            return None
            
        relation = db.query(ParentStudentRelation).filter(
            ParentStudentRelation.student_id == student_id,
            ParentStudentRelation.parent_user_id == parent_user_id
        ).first()

        if relation:
            db.delete(relation)
            db.commit()
            db.refresh(student) # Öğrencinin parents listesinin güncellenmesi için
            return student
        return None # İlişki bulunamadıysa

    def get_parents_of_student(self, db: Session, student_id: int, school_id: int) -> Optional[List[User]]:
        student = db.query(Student).options(selectinload(Student.parents)).filter(
            Student.id == student_id, 
            Student.school_id == school_id
        ).first()
        return student.parents if student else None

    def get_students_of_parent(self, db: Session, parent_user_id: int) -> Optional[List[Student]]:
        # Bu fonksiyon parent'ın tüm okullardaki öğrencilerini getirir.
        # Okul bazlı filtreleme gerekirse, parent'ın school_id'si veya student.school_id ile join gerekebilir.
        parent = db.query(User).options(selectinload(User.students).selectinload(Student.school)).filter(
            User.id == parent_user_id,
            User.role == 'parent'
        ).first()
        return parent.students if parent else None 