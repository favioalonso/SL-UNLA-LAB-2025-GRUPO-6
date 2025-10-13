from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict 
from datetime import date, time
from schemas.schemas import PersonaOut
from typing import Optional, List
from dotenv import load_dotenv
from pathlib import Path

class TurnoBase(BaseModel):
    fecha: date
    hora: time
    persona_id: int

class TurnoCreate(TurnoBase):
    pass

class TurnoUpdate(BaseModel):
    fecha: Optional[date] = None
    hora: Optional[time] = None
    estado: Optional[str] = None

class TurnoOut(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str
    persona: PersonaOut

    class Config:
        from_attributes = True
        
#Modelo de respuesta para JSON de horarios segun una unica fecha
class Horarios(BaseModel):
    fecha: date
    horarios_disponibles: list[str]

class HorariosResponse(BaseModel):
    fecha: date
    horarios_disponibles: list[str]

#Retorna un mensaje
class MensajeResponse(BaseModel):
    mensaje: str

#Clase para ver a las personas con sus turnos cancelados
class PersonaConTurnosCancelados(BaseModel):
    persona: PersonaOut
    turnos_cancelados_contador: int
    turnos_cancelados_detalle: List[TurnoOut] #Lista de los turnos cancelados para mostrar el detalle

#Carga las variables del archivo .env
load_dotenv()

#Definición de ruta dinámica para leer el archivo .env
RUTA_ARCHIVO_ENV = Path(__file__).resolve().parent/'.env'

#'__file__' direcciona a la ruta del archivo actual
#'resolve()' convierte la ruta en absoluta para ubicar el archivo en la terminal donde se ejecuta
#'.parent' sube una carpeta

#Clase de variables de entorno
class ConfHorarios(BaseSettings):
    horarios_turnos: List[str] 
    estados_turnos: List[str]

    #Definimos la configuracion del archivo .env
    model_config = SettingsConfigDict(env_file=RUTA_ARCHIVO_ENV, env_file_encoding='utf-8') #'utf-8' asegura que no existan errores por caracteres extraños
    

settings = ConfHorarios()



