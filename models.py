
from sqlalchemy import Column, Integer, String, Date, Boolean, Time, ForeignKey
from sqlalchemy.orm import relationship
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

    turnos = relationship("Turno", back_populates="persona")


class Turno(Base):
    __tablename__ = "turnos"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    estado = Column(String, default= "Pendiente")

    persona_id = Column(Integer, ForeignKey("personas.id"), nullable=False)

    persona = relationship("Persona", back_populates="turnos")



