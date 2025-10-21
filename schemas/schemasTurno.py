from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict 
from datetime import date, time
from schemas.schemas import PersonaOut
from typing import Optional, List, Dict
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

#Nueva clase para que el turno solo salga con los datos necesarios y no repita la persona reiteradas veces
class TurnoDetalleSimple(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str

    class Config:
        from_attributes = True

#Clase PersonaConTurnos para que solo me muestre una ves la persona y el resto sean los turnos que tiene
class PersonaConTurnos(BaseModel):
    persona: PersonaOut
    turnos: List[TurnoDetalleSimple]

#Clase para ver a las personas con sus turnos cancelados
class PersonaConTurnosCancelados(BaseModel):
    persona: PersonaOut
    turnos_cancelados_contador: int
    turnos_cancelados_detalle: List[TurnoDetalleSimple] #Lista de los turnos cancelados para mostrar el detalle

#Estructura de paginación
class RespuestaTurnosPaginados(BaseModel):
    total_registros: int
    turnos: List[TurnoOut]
    pagina: int

#Carga las variables del archivo .env
load_dotenv()

#Definición de ruta dinámica para leer el archivo .env
RUTA_ARCHIVO_ENV = Path(__file__).resolve().parent.parent/'.env'

#'__file__' direcciona a la ruta del archivo actual
#'resolve()' convierte la ruta en absoluta para ubicar el archivo en la terminal donde se ejecuta
#'.parent.parent' sube dos carpetas hasta la raíz del proyecto

# Clase de variables de entorno
class ConfiguracionInicial(BaseSettings):
    
    #Variable de franja horaria 
    horarios_turnos: List[str] 
    
    #Variable de turnos posibles
    estados_posibles: List[str]

    #Definimos la configuracion del archivo .env
    model_config = SettingsConfigDict(env_file=RUTA_ARCHIVO_ENV, env_file_encoding='utf-8') #'utf-8' asegura que no existan errores por caracteres extraños
    
    #Convertimos 'estados_posibles' a un diccionario para filtrar por clave y evitar errores al comparar
    
    #Validor de formato Lista[str]
    @field_validator('estados_posibles', mode='after')
    @classmethod
    def convertir_lista_a_dict(cls, valor_extraido: List[str]):
        #Creamos un diccionario de pares clave-valor
        diccionario_estados = {}
        for par in valor_extraido:
            par = par.strip() #Limpiar de espacios en blanco
            if ':' in par:
                clave, valor = par.split(':', 1) #Se separan en clave y valor
                diccionario_estados[clave.strip()] = valor.strip()
                
        return diccionario_estados 
    
settings = ConfiguracionInicial()

