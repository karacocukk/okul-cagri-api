from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from app import crud, models, schemas
from app.api.deps import get_db, get_current_active_user

router = APIRouter(
    tags=["School Administration - Schools"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.School, status_code=status.HTTP_201_CREATED)
def create_school(
    *,
    db: Session = Depends(get_db),
    school_in: schemas.SchoolCreate,
    # current_user: models.User = Depends(get_current_active_user) # Yetkilendirme (örn: süper admin)
) -> Any:
    """
    Create new school. 
    Yetkilendirme: Genellikle sadece süper adminler.
    """
    # if not current_user or current_user.role != schemas.UserRole.SUPER_ADMIN:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    existing_school = crud.school.get_school_by_unique_code(db, unique_code=school_in.unique_code)
    if existing_school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"School with unique_code '{school_in.unique_code}' already exists.",
        )
    school = crud.school.create(db=db, obj_in=school_in)
    return school

@router.get("/", response_model=List[schemas.School])
def read_schools(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    # current_user: models.User = Depends(get_current_active_user) # Yetkilendirme
) -> Any:
    """
    Retrieve schools.
    Yetkilendirme: Genellikle sadece süper adminler veya okul yöneticileri (kendi okullarını).
    """
    # if current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id:
    #     # Okul admini sadece kendi okulunu görebilir (liste yerine tek obje döner)
    #     school = crud.school.get(db, id=current_user.school_id)
    #     return [school] if school else []
    # elif current_user.role == schemas.UserRole.SUPER_ADMIN:
    #     schools = crud.school.get_multi(db, skip=skip, limit=limit)
    # else:
    #     return [] # Diğer roller için boş liste veya yetki hatası
    schools = crud.school.get_multi(db, skip=skip, limit=limit) # Şimdilik tüm okulları listele
    return schools

@router.get("/{school_id}", response_model=schemas.School)
def read_school(
    *,
    db: Session = Depends(get_db),
    school_id: int,
    # current_user: models.User = Depends(get_current_active_user)
) -> Any:
    """
    Get school by ID.
    Yetkilendirme: Süper admin veya ilgili okulun yöneticisi/öğretmeni/velisi.
    """
    school = crud.school.get(db=db, id=school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    
    # if current_user.role != schemas.UserRole.SUPER_ADMIN and current_user.school_id != school_id:
    #     # Daha detaylı rol bazlı kontrol (öğretmen, veli o okula erişebilir mi?)
    #     is_related = False
    #     if current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id:
    #         is_related = True
    #     # Diğer roller için (teacher, parent) kontrol eklenebilir.
    #     if not is_related:
    #         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return school

@router.put("/{school_id}", response_model=schemas.School)
def update_school(
    *,
    db: Session = Depends(get_db),
    school_id: int,
    school_in: schemas.SchoolUpdate,
    # current_user: models.User = Depends(get_current_active_user) # Yetkilendirme
) -> Any:
    """
    Update a school.
    Yetkilendirme: Süper admin veya ilgili okulun yöneticisi.
    """
    school = crud.school.get(db=db, id=school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    
    # if current_user.role != schemas.UserRole.SUPER_ADMIN and 
    #    not (current_user.role == schemas.UserRole.SCHOOL_ADMIN and current_user.school_id == school_id):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    if school_in.unique_code and school_in.unique_code != school.unique_code:
        existing_school = crud.school.get_school_by_unique_code(db, unique_code=school_in.unique_code)
        if existing_school and existing_school.id != school_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another school with unique_code '{school_in.unique_code}' already exists.",
            )
            
    school = crud.school.update(db=db, db_obj=school, obj_in=school_in)
    return school

@router.delete("/{school_id}", response_model=schemas.School)
def delete_school(
    *,
    db: Session = Depends(get_db),
    school_id: int,
    # current_user: models.User = Depends(get_current_active_user) # Yetkilendirme (Süper admin)
) -> Any:
    """
    Delete a school.
    Yetkilendirme: Sadece süper adminler.
    """
    # if not current_user or current_user.role != schemas.UserRole.SUPER_ADMIN:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        
    school = crud.school.get(db=db, id=school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    
    deleted_school = crud.school.remove(db=db, id=school_id)
    return deleted_school

# Yorum satırına alınan /by_code/{unique_code} ve /{school_id}/classes/ endpointleri
# Eğer public bir API olacaksa ayrı bir public_router.py dosyasına taşınabilir
# veya yetkilendirmeleri ayarlanarak burada kalabilir.
# Şimdilik okul yönetimi kapsamında olmadıkları için kaldırıyorum.

# @router.get("/by_code/{unique_code}", response_model=schemas.School) # public_router.py'e taşındı
# async def get_school_by_unique_code_endpoint(
#     unique_code: str,
#     db: Session = Depends(get_db)
#     # current_user: models.User = Depends(get_current_active_superuser) # Yetkilendirme gerekirse
# ):
#     """Fetch a school by its unique_code."""#
#     db_school = crud.get_school_by_unique_code(db, unique_code=unique_code)
#     if db_school is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"School with unique code '{unique_code}' not found")
#     return db_school

# @router.get("/{school_id}/classes/", response_model=List[schemas.Class]) # public_router.py'e taşındı
# def read_school_classes(
#     school_id: int,
#     db: Session = Depends(get_db),
#     skip: int = 0,
#     limit: int = 100,
#     dependencies: List = Depends(lambda: []) # Router seviyesindeki dependency'leri override et
#     # current_user: models.User = Depends(get_current_active_user) # Şimdilik yetkilendirmesiz
# ):
#     """Retrieve all classes for a specific school. This endpoint is public."""#
#     db_school = crud.get_school(db, school_id=school_id)
#     if db_school is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
#     
#     classes = crud.get_classes(db=db, school_id=school_id, skip=skip, limit=limit)
#     return classes 