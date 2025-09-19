from pydantic import BaseModel


from datetime import date
from typing import Optional

class PersonaBase(BaseModel):
    nombre: str
    email: str
    dni: str
    telefono: str
    fecha_nacimiento: date
    habilitado: Optional[bool] = True

class PersonaCreate(PersonaBase):
    pass

class PersonaUpdate(PersonaBase):
    pass


class PersonaOut(PersonaBase):
    id: int
    edad: int
    class Config:
        orm_mode = True
