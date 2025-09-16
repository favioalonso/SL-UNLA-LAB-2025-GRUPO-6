from pydantic import BaseModel
from datetime import date, time
from schemas import PersonaOut

class TurnoBase(BaseModel):
    fecha: date
    hora: time
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str
    persona: PersonaOut
    
    class Config:
        orm_mode = True

class Horarios(BaseModel):
    fecha: date
    horarios_disponibles: list[str]

class HorariosResponse(BaseModel):
    fecha: date
    horarios_disponibles: list[str]


    




