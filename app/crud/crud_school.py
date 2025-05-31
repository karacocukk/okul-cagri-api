from sqlalchemy.orm import Session
import logging
from typing import Optional

from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolUpdate
from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)

class CRUDSchool(CRUDBase[School, SchoolCreate, SchoolUpdate]):
    def get_school_by_name(self, db: Session, name: str) -> Optional[School]:
        return db.query(self.model).filter(self.model.name == name).first()

    def get_school_by_unique_code(self, db: Session, unique_code: str) -> Optional[School]:
        logger.debug(f"Searching for school with unique_code: {unique_code}")
        school = db.query(self.model).filter(self.model.unique_code == unique_code).first()
        if school:
            logger.debug(f"Found school: {school.name}, ID: {school.id}, Code: {school.unique_code}")
        else:
            logger.debug(f"School with unique_code '{unique_code}' not found in database.")
        return school

# crud_school objesi __init__.py içinde oluşturulacak veya direkt sınıf kullanılacak.
# Şimdilik tekil obje tanımını kaldırıyorum, __init__.py'de nasıl export edileceğine karar veririz.
# crud_school = CRUDSchool(School) 