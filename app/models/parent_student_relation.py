from sqlalchemy import Column, Integer, ForeignKey, Table
from app.db.base_class import Base # ..db.base_class yerine app.db.base_class

# Association Table for Parent-Student Many-to-Many relationship
parent_student_association_table = Table(
    "parent_student_association",
    Base.metadata,
    Column("parent_user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("student_id", Integer, ForeignKey("students.id"), primary_key=True)
)

class ParentStudentRelation(Base):
    __tablename__ = "parent_student_relations" # Açık tablo adı

    # Bu model, eğer ilişki tablosuna ek alanlar eklemek istersek kullanılır.
    # Sadece ID'ler içinse, yukarıdaki association_table yeterlidir ve bu modele gerek kalmayabilir.
    # Eğer bu model kullanılacaksa, User ve Student'taki relationship secondary=bu_tablo_adı olmalı.
    # Şimdilik parent_student_association_table kullanıldığı için bu modelin içeriği kritik değil.
    
    id = Column(Integer, primary_key=True, index=True) # Ayrı bir ID'si olabilir
    parent_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    
    # İlişkiye özel ek alanlar buraya eklenebilir, örneğin:
    # relation_type = Column(String, nullable=True) # "mother", "father", "guardian" 