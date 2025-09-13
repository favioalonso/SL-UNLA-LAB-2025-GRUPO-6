from pydantic import BaseModel
from datetime import date, time
from schemas import PersonaOut

class TurnoBase(BaseModel):
    fecha: date
    hora: time
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoOut(TurnoBase):
    estado: str
    id: int
    persona: PersonaOut
    
    class Config:
        orm_mode = True




    




