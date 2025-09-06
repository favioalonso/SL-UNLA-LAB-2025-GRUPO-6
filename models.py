
from sqlalchemy import Column, Integer, String, Date, Boolean
from database import Base

class Persona(Base):
    __tablename__ = "personas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    dni = Column(String, unique=True, index=True, nullable=False)
    telefono = Column(String, index=True, nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    habilitado = Column(Boolean, default=True, nullable=False)
