from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
import logging

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserPasswordChange
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase

logger = logging.getLogger(__name__)

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(self.model).options(selectinload(User.students), selectinload(User.school)).filter(self.model.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(self.model).options(selectinload(User.students), selectinload(User.school)).filter(self.model.email == email).first()

    def create(self, db: Session, obj_in: UserCreate) -> User:
        hashed_password = get_password_hash(obj_in.password)
        db_user = self.model(
            username=obj_in.username,
            password_hash=hashed_password,
            full_name=obj_in.full_name,
            email=obj_in.email,
            phone_number=obj_in.phone_number,
            role=obj_in.role if obj_in.role else 'parent',
            school_id=obj_in.school_id,
            is_active=True, 
            initial_password_changed=False
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def update_password(self, db: Session, db_obj: User, new_password: str) -> User:
        hashed_password = get_password_hash(new_password)
        db_obj.password_hash = hashed_password
        db_obj.initial_password_changed = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_school(
        self, db: Session, school_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return (
            db.query(self.model)
            .options(selectinload(User.students), selectinload(User.school))
            .filter(self.model.school_id == school_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_multi_filtered(
        self, db: Session, *, school_id: Optional[int] = None, role: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[User]:
        query = db.query(self.model).options(selectinload(User.students), selectinload(User.school))
        logger.info(f"[CRUD] get_multi_filtered çağrıldı. school_id: {school_id}, role: {role}, skip: {skip}, limit: {limit}")
        if school_id is not None:
            query = query.filter(self.model.school_id == school_id)
            logger.info(f"[CRUD] school_id ({school_id}) filtresi uygulandı.")
        if role is not None:
            query = query.filter(self.model.role == role)
            logger.info(f"[CRUD] role ({role}) filtresi uygulandı.")
        
        try:
            result = query.offset(skip).limit(limit).all()
            logger.info(f"[CRUD] Sorgu sonucu {len(result)} kullanıcı.")
        except Exception as e:
            logger.error(f"[CRUD] Sorgu sırasında hata: {e}", exc_info=True)
            raise
        return result

    def authenticate(self, db: Session, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

# Eski fonksiyonlar kaldırıldı veya CRUDBase/CRUDUser içine taşındı.
# Alttaki fonksiyonlar tamamen silinecek.