from time import strftime
from pydantic import BaseModel
from datetime import date, time
from schemas import PersonaOut
from typing import Optional

class TurnoBase(BaseModel):
    fecha: date
    hora: time = strftime('H:M')
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoUpdate(BaseModel):
    fecha: Optional [date] = None
    hora: Optional [time] = None
    estado: Optional [str] = None

class TurnoOut(BaseModel):
    fecha: date
    hora: time
    estado: str
    persona: PersonaOut
    
    class Config:
        orm_mode = True

