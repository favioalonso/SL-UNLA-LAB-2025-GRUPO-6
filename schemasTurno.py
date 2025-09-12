from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class TurnoBase(BaseModel):
    fecha: date
    hora: time
    estado:Optional [str] = "Pendiente"
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoOut(TurnoBase):
    id: int

    class Config:
        orm_mode = True





    




