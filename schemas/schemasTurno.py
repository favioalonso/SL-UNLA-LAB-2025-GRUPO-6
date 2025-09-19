from time import strftime
from pydantic import BaseModel
from datetime import date, time
from schemas import PersonaOut

class TurnoBase(BaseModel):
    fecha: date
    hora: time = strftime('H:M')
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoOut(BaseModel):
    fecha: date
    hora: time
    estado: str
    persona: PersonaOut
    
    class Config:
        orm_mode = True
