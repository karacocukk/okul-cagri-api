from typing import List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.Student)
def create_ogrenci_for_current_veli(
    *, 
    db: Session = Depends(deps.get_db),
    ogrenci_in: schemas.StudentCreateNoSchoolId, # school_id parent'ın school_id'sinden alınacak
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create new student for the current logged-in parent.
    The student will be associated with the parent's school.
    """
    if not current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parent user is not associated with a school. Cannot create student."
        )
    
    # StudentCreate şemasına school_id'yi ekleyerek tam bir StudentCreate objesi oluşturuyoruz
    student_create_data = schemas.StudentCreate(**ogrenci_in.model_dump(), school_id=current_user.school_id)

    #TODO: crud.student.create_with_parent(db=db, obj_in=student_create_data, parent_id=current_user.id) gibi bir şey olacak
    # Şimdilik eski CRUD'u bırakalım, sadece şema ve User modeli güncellendi.
    # Ogrenci modeli artık Student, veli_id yerine parent ilişkisi (association table üzerinden)
    # Bu nedenle crud_ogrenci.create_veli_ogrenci doğrudan çalışmayacak.
    # Bu endpoint'in mantığı yeni Student ve User ilişkisine göre tamamen yeniden yazılmalı.
    
    # crud.student.create_with_parent metodunu çağır
    try:
        created_student = crud.student.create_with_parent(
            db=db, 
            obj_in=student_create_data, 
            parent_user=current_user
        )
        return created_student
    except Exception as e:
        # Hata durumunda loglama yapılabilir ve uygun HTTP hatası döndürülebilir.
        # Örneğin, veritabanı hatası veya benzersizlik kısıtlaması ihlali olabilir.
        # import logging
        # logging.error(f"Error creating student for parent {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the student."
        )

@router.get("/", response_model=List[schemas.Student])
def read_ogrenciler_for_current_veli(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Retrieve students for the current logged-in parent.
    """
    # User modelinde students ilişkisi var, doğrudan onu kullanabiliriz.
    # SQLAlchemy bu ilişkiyi (eager/lazy loading ayarına göre) halledecektir.
    # CRUD katmanında parent_id'ye göre öğrenci getiren bir fonksiyona gerek kalmayabilir.
    # Ancak pagination (skip, limit) için bu yaklaşım yetersiz olabilir eğer User.students
    # doğrudan bir liste ise ve veritabanından kesit alınmıyorsa.
    # Şimdilik direkt current_user.students dönüyoruz, Pydantic bunu List[schemas.Student]'e çevirecektir.
    # Eğer current_user.students lazy load ediliyorsa ve session kapandıysa sorun olabilir.
    # Bu nedenle db session içinde student'ları almak daha güvenli olabilir.
    
    # Güvenli yol (özellikle pagination için):
    # students = crud.student.get_multi_by_parent_id(db, parent_id=current_user.id, skip=skip, limit=limit)
    # return students
    
    # Basit yol (eğer User.students eager load ediliyorsa ve pagination önemsizse veya şemada handle ediliyorsa):
    # Bu, User modelindeki students ilişkisinin doğru ayarlandığını varsayar (secondary table vs.)
    if current_user.role == models.UserRoleEnum.PARENT:
        # Student objelerini döndürmeden önce, Pydantic'in bunları Student şemasına dönüştürebilmesi için
        # gerekli alanların yüklendiğinden emin olmalıyız (örn: school, assigned_class detayları).
        # Eğer User.students ilişkisi sadece Student ID'lerini değil, tam Student objelerini tutuyorsa bu çalışır.
        # TODO: Test etmek lazım, User.students ne döndürüyor? selectinload(User.students) gerekli olabilir get_current_user içinde.
        # Şimdilik User modelindeki `students` ilişkisine güveniyoruz.
        # return current_user.students 
        
        # crud.student.get_multi_by_parent metodunu kullanarak öğrencileri al
        try:
            students = crud.student.get_multi_by_parent(
                db=db, 
                parent_id=current_user.id, 
                skip=skip, 
                limit=limit
            )
            return students
        except Exception as e:
            # import logging
            # logging.error(f"Error fetching students for parent {current_user.id}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while fetching students."
            )

    return [] # Eğer kullanıcı parent değilse boş liste dönsün

@router.get("/{ogrenci_id}", response_model=schemas.Student)
def read_ogrenci_by_id_for_current_veli(
    ogrenci_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get a specific student by id, ensuring it belongs to the current logged-in parent.
    """
    student_found: Optional[models.Student] = None
    if current_user.role == models.UserRoleEnum.PARENT:
        # Eskiden current_user.students listesinde arama yapıyorduk.
        # Şimdi doğrudan CRUD operasyonunu kullanacağız.
        # for s in current_user.students:
        #     if s.id == ogrenci_id:
        #         student_found = s
        #         break
        try:
            student_found = crud.student.get_by_id_and_parent_id(
                db=db, 
                student_id=ogrenci_id, 
                parent_id=current_user.id
            )
        except Exception as e:
            # import logging
            # logging.error(f"Error fetching student {ogrenci_id} for parent {current_user.id}: {e}", exc_info=True)
            # Bu durumda da 404 dönmek daha mantıklı olabilir, çünkü temelde öğrenci bulunamadı.
            # Ancak beklenmedik bir veritabanı hatasıysa 500 de düşünülebilir.
            # Şimdilik hata durumunda genel bir 500 yerine, bulunamadı hatasına yönlendirelim.
            pass # Hata olsa bile student_found None kalacak ve aşağıdaki 404 çalışacak

    if not student_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found or does not belong to this parent.")
    return student_found

@router.put("/{ogrenci_id}", response_model=schemas.Student)
def update_ogrenci_for_current_veli(
    ogrenci_id: int,
    *, 
    db: Session = Depends(deps.get_db),
    ogrenci_in: schemas.StudentUpdate,
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update a student for the current logged-in parent.
    """
    student_to_update: Optional[models.Student] = None
    if current_user.role == models.UserRoleEnum.PARENT:
        for s in current_user.students:
            if s.id == ogrenci_id:
                student_to_update = s
                break

    if not student_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found or does not belong to this parent for update.")
    
    #TODO: crud.student.update çağrılacak, ama sadece parent'a aitse
    # updated_student = crud.student.update(db=db, db_obj=student_to_update, obj_in=ogrenci_in)
    # return updated_student
    # raise HTTPException(status_code=501, detail="Student update for parent not yet fully implemented with new models.")

    try:
        # student_to_update zaten doğru öğrenci objesi, doğrudan onu güncelleyebiliriz.
        updated_student = crud.student.update(db=db, db_obj=student_to_update, obj_in=ogrenci_in)
        return updated_student
    except Exception as e:
        # import logging
        # logging.error(f"Error updating student {ogrenci_id} for parent {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the student."
        )

@router.delete("/{ogrenci_id}", response_model=schemas.Student) # Başarılı silmede öğrenci bilgisi dönebilir veya sadece status 204
def delete_ogrenci_for_current_veli(
    ogrenci_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Delete a student for the current logged-in parent.
    """
    student_to_delete: Optional[models.Student] = None
    if current_user.role == models.UserRoleEnum.PARENT:
        for s in current_user.students:
            if s.id == ogrenci_id:
                student_to_delete = s
                break
    
    if not student_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found or does not belong to this parent for deletion.")

    #TODO: crud.student.remove çağrılacak, ama sadece parent'a aitse
    # crud.student.remove(db=db, id=student_to_delete.id)
    # return student_to_delete # veya status.HTTP_204_NO_CONTENT ile boş yanıt
    # raise HTTPException(status_code=501, detail="Student deletion for parent not yet fully implemented with new models.") 

    try:
        # student_to_delete zaten doğru öğrenci objesi
        deleted_student = crud.student.remove(db=db, id=student_to_delete.id)
        # Başarılı silme durumunda silinen öğrenciyi veya 204 No Content döndürebiliriz.
        # response_model schemas.Student olduğu için silinen öğrenciyi döndürmek daha tutarlı.
        return deleted_student 
    except Exception as e:
        # import logging
        # logging.error(f"Error deleting student {ogrenci_id} for parent {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the student."
        ) 