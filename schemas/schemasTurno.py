from pydantic import BaseModel, model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import date, time, timedelta, datetime
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
    #Variables de control de franja horaria
    horario_inicio: str
    horario_fin: str
    intervalo: int

    #Variable de franja horaria, no se leerá directamente desde el archivo .env 
    horarios_turnos: List[str] = Field(default=[], init=False)
    
    #Variable de turnos posibles
    estados_posibles: Dict[str, str]

    #Definimos la configuracion del archivo .env
    model_config = SettingsConfigDict(env_file=RUTA_ARCHIVO_ENV, env_file_encoding='utf-8') #'utf-8' asegura que no existan errores por caracteres extraños
    
    #Se carga la lista de horarios segun los limites del .env
    @model_validator(mode='after')
    def generar_lista_horarios(self):
        try:
            hora_inicio = datetime.strptime(self.horario_inicio, "%H:%M")
            hora_fin = datetime.strptime(self.horario_fin, "%H:%M")

            intervalo = timedelta(minutes=self.intervalo)

            lista_horarios = [0]
            hora_actual = hora_inicio

            while hora_actual <= hora_fin:
                lista_horarios.append(hora_actual.strftime("%H:%M"))
                hora_actual += intervalo
            self.horarios_turnos = lista_horarios
        except ValueError as error:
            raise ValueError(f"Error en el formato de hora: {error}")
        return self
       
settings = ConfiguracionInicial()


   
