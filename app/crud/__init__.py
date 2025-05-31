from app.models import User, School, Class as ModelClass, Student, Teacher, ParentStudentRelation, Notification, Call, CallStatusEnum
from app.crud.crud_user import CRUDUser
from app.crud.crud_school import CRUDSchool
from app.crud.crud_class import CRUDClass
from app.crud.crud_student import CRUDStudent
from app.crud.crud_teacher import CRUDTeacher
from app.crud.crud_parent_student_relation import CRUDParentStudentRelation
from app.crud.crud_notification import CRUDNotification
from app.crud.crud_call import CRUDCall
from app.crud.base import CRUDBase

# CRUD sınıflarından örnekler oluşturuluyor
user = CRUDUser(User)
school = CRUDSchool(School)
class_ = CRUDClass(ModelClass) # ModelClass aliasını kullandık çünkü class Python'da keyword
student = CRUDStudent(Student)
teacher = CRUDTeacher(Teacher)
parent_student_relation = CRUDParentStudentRelation()
notification = CRUDNotification(Notification)
call = CRUDCall(Call)

# crud_school, crud_class vs. importları artık gerekli değil, örnekler yukarıda oluşturuldu.
# from app.crud.crud_school import crud_school 
# from app.crud.crud_class import crud_class
# from app.crud.crud_student import crud_student
# from app.crud.crud_teacher import crud_teacher
# from app.crud.crud_parent_student_relation import crud_parent_student_relation
# from app.crud.crud_notification import crud_notification

class CRUD:
    def __init__(self):
        self.user = user
        self.school = school
        self.class_ = class_
        self.student = student
        self.teacher = teacher
        self.parent_student_relation = parent_student_relation
        self.notification = notification
        self.call = call

crud = CRUD()

__all__ = [
    "crud", # Ana CRUD sarmalayıcı
    "CRUDBase",
    "user",
    "school",
    "class_",
    "student",
    "teacher",
    "parent_student_relation",
    "notification",
    "call",
]