from pydantic import BaseModel, field_validator, EmailStr
import re
from datetime import date
from typing import Optional, List
from enum import Enum

class PersonaBase(BaseModel):
    nombre: str
    email: str
    dni: str
    telefono: str
    fecha_nacimiento: date
    habilitado: Optional[bool] = True

    @field_validator('nombre')
    @classmethod
    def validate_nombre(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('El nombre debe tener al menos 2 caracteres')
        if len(v) > 100:
            raise ValueError('El nombre no puede exceder 100 caracteres')
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', v.strip()):
            raise ValueError('El nombre solo puede contener letras y espacios')
        return v.strip().title()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Formato de email inválido')
        return v.lower()

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        if not re.match(r'^\d{8}$', v):
            raise ValueError('El DNI debe tener exactamente 8 dígitos numéricos')
        return v

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        # Remover espacios y guiones
        cleaned = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+54)?[0-9]{10,11}$', cleaned):
            raise ValueError('Formato de teléfono inválido. Debe tener 10-11 dígitos')
        return cleaned

    @field_validator('fecha_nacimiento')
    @classmethod
    def validate_fecha_nacimiento(cls, v):
        if v < date(1900, 1, 1):
            raise ValueError('La fecha de nacimiento no puede ser anterior a 1900')
        if v > date.today():
            raise ValueError('La fecha de nacimiento no puede ser futura')
        # Validar edad mínima (0 años) y máxima (150 años)
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        if age > 150:
            raise ValueError('La edad no puede ser mayor a 150 años')
        return v

class PersonaCreate(PersonaBase):
    pass

class PersonaUpdate(PersonaBase):
    pass

class PersonaOut(PersonaBase):
    id: int
    edad: int
    class Config:
        from_attributes = True

# Modelos para filtrado y paginación
class PersonaFilter(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    edad_min: Optional[int] = None
    edad_max: Optional[int] = None
    order_by: Optional[str] = 'id'
    order: Optional[str] = 'asc'

    @field_validator('edad_min', 'edad_max')
    @classmethod
    def validate_edad(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('La edad debe estar entre 0 y 150 años')
        return v

    @field_validator('order_by')
    @classmethod
    def validate_order_by(cls, v):
        allowed_fields = ['id', 'nombre', 'edad', 'fecha_nacimiento', 'email']
        if v not in allowed_fields:
            raise ValueError(f'order_by debe ser uno de: {", ".join(allowed_fields)}')
        return v

    @field_validator('order')
    @classmethod
    def validate_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('order debe ser "asc" o "desc"')
        return v

class PaginationMetadata(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedPersonaResponse(BaseModel):
    items: List[PersonaOut]
    metadata: PaginationMetadata

class Booleano_Estado(str, Enum):
    TRUE = "habilitado"
    FALSE = "deshabilitado" 
