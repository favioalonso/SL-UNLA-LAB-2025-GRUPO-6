from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import date, time
from schemas.schemas import PersonaOut
from typing import Optional, List, Dict, Any
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

#Schema optimizado para turno sin datos de persona (evita redundancia)
class TurnoSinPersona(BaseModel):
    id: int
    fecha: date
    hora: time
    estado: str

    class Config:
        from_attributes = True

#Schema para persona con sus turnos (estructura optimizada)
class PersonaConTurnos(BaseModel):
    persona: PersonaOut
    turnos: List[TurnoSinPersona]
    total_turnos: int

#Clase para ver a las personas con sus turnos cancelados (optimizada)
class PersonaConTurnosCancelados(BaseModel):
    persona: PersonaOut
    turnos_cancelados_contador: int
    turnos_cancelados_detalle: List[TurnoSinPersona] #Lista de turnos cancelados sin redundancia de persona

#Schema para representar persona con turnos en un reporte por fecha (estructura simplificada)
class PersonaTurnosFecha(BaseModel):
    persona: Dict[str, Any]  # Diccionario con id, nombre, dni
    turnos: List[Dict[str, Any]]  # Lista de turnos sin datos de persona

#Schema para listado general de turnos agrupados por persona
class PersonaConTurnosLista(BaseModel):
    persona: PersonaOut
    turnos: List[Dict[str, Any]]  # Lista de turnos sin datos de persona

#Estructura de paginación (optimizada con agrupación por persona)
class RespuestaTurnosConfirmadosPaginados(BaseModel):
    total_registros: int
    personas_con_turnos: List[Dict[str, Any]]  # Lista de personas con sus turnos confirmados

#Clase para metadata paginación
class MetadataPaginacion(BaseModel):
    pag: int
    por_pag: int
    total_pag: int
    tiene_posterior: bool
    tiene_anterior: bool

#Estructura de paginación
class RespuestaTurnosPaginados(BaseModel):
    turnos: List[TurnoOut]
    total_registros: int
    metadata: MetadataPaginacion

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

