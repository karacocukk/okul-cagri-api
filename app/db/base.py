from app.db.base_class import Base

# Import all the models, so that Base has them before being imported by Alembic
from app.models.user import User
from app.models.school import School
from app.models.class_ import Class
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.notification import Notification, NotificationReadStatus
from app.models.call import Call 