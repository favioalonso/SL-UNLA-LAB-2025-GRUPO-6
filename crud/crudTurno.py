from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import models.models as models, schemas.schemasTurno as schemasTurno, schemas.schemas as schemas
from datetime import date, time, timedelta, datetime
from crud.crud import calcular_edad
from copy import copy
from schemas.schemasTurno import settings
import math
from decimal import Decimal

#Imports para generar archivosde reportes
import pandas as pd
from io import StringIO, BytesIO

#Imports para borb version=2.1.22
from borb.pdf import Document, Page, PDF
from borb.pdf.canvas.layout.page_layout.multi_column_layout import SingleColumnLayout
from borb.pdf.canvas.layout.text.paragraph import Paragraph, Alignment
from borb.pdf.canvas.layout.horizontal_rule import HorizontalRule
from borb.pdf.canvas.layout.table.fixed_column_width_table import FixedColumnWidthTable
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.table.table_util import TableCell


"""
USO DEL ARCHIVO DE VARIABLES DE ENTORNO .ENV

- Está definido en schemasTurnos en 'settings'
- Para acceder a la lista del rango horario -> schemasTurnos.settings.horarios_turnos
- Para acceder a la lista de estados posibles de un turno -> schemasTurnos.settings.estados_turnos

USO DE VARIABLE DE ESTADOS

- Se trabaja con un diccionario con pares clave valor
diccionario_estados = schemasTurnos.settings.estados_posibles 

- Se accede a un estado a traves de su clave (no de su valor)
estado_requerido = diccionario_estados.get('OPCION_ESTADO_XXXXX')

"""
#Se le asignan los valores a la variable diccionario_estados para que sean utilizados en los endpoints correspondientes
diccionario_estados = settings.estados_posibles

#Cargo los nombre de los meses una unica vez
meses_nombres= [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]

#Funciones para validad los atributos del cuerpo de entrada de datos
def validar_fecha_hora(turno: schemasTurno.TurnoCreate):

    if turno.hora.hour < 9 or turno.hora.hour >= 17:
        return "La hora debe ser entre las 9:00 y 16:30"
    
    if not (turno.hora.minute == 30 or turno.hora.minute == 0):
        return "La hora debe tener el siguiente formato: HH:00/HH:30"
    
    if turno.fecha < date.today():
        return "La fecha no puede ser menor a la de hoy"
    
    if turno.fecha.weekday() == 6: 
       return "No se pueden reservar turnos los domingos"
    
    return None

#Crea un turno diccionario para que respondan los endpoints y adapte facilmente con el esquema de TurnoOut
def turno_diccionario(nuevo_turno: models.Turno, persona: models.Persona):
    persona_dict={
        "nombre": persona.nombre,
        "email": persona.email,
        "dni": persona.dni,
        "telefono": persona.telefono,
        "fecha_nacimiento": persona.fecha_nacimiento,
        "habilitado": persona.habilitado,
        "id": persona.id,
        "edad":calcular_edad(persona.fecha_nacimiento)
    }
    turno_dict={
        "id" : nuevo_turno.id,
        "persona_id": nuevo_turno.persona_id,
        "fecha": nuevo_turno.fecha,
        "hora": nuevo_turno.hora,
        "estado": nuevo_turno.estado,
        "persona": persona_dict
   }
    return turno_dict

#Regla de negocio, habilita a las personas si ya paso el tiempo de deshabilitacion y deshabilita segun regla de turnos cancelados
def habilitar_persona(db: Session, turno: schemasTurno.TurnoCreate, persona: models.Persona):

    seis_meses_atras = date.today() - timedelta(days=180)
    cant_cancelados = db.query(models.Turno).filter(models.Turno.persona_id == turno.persona_id, 
                                                   func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower(),
                                                   models.Turno.fecha >= seis_meses_atras).count()
    if (cant_cancelados >= 5):
        persona.habilitado = False
        db.commit()
        db.refresh(persona)
        return False
    else:
        if (persona.habilitado == False):
            persona.habilitado = True
            db.commit()
            db.refresh(persona)
    return True

##Error para indicar que no se encontro la persona en la base de datos
class DatabaseResourceNotFound(Exception):
    pass
    
#Funcion para el endpoint POST/turnos
def create_turnos(db: Session, turno: schemasTurno.TurnoCreate):
    
    try:
        persona = db.query(models.Persona).filter(models.Persona.id == turno.persona_id).first()

        if not persona: 
            raise DatabaseResourceNotFound("Persona no encontrada")
    
        if(not habilitar_persona(db, turno, persona)):
            raise PermissionError ("La persona no esta habilitada")
    
        error = validar_fecha_hora(turno)
        if error:
            raise ValueError(error)
        #Corrijo la funcion para validar si el turno existe, teniendo en cuenta los cancelados que puedan estar en ese mismo horario
        #Me permite reservar un horario aunque exista un turno en la base de datos con misma fecha y hora pero que este CANCELADO
        existente_no_cancelado = (
            db.query(models.Turno).filter(models.Turno.fecha == turno.fecha, 
                                          func.strftime('%H:%M', models.Turno.hora) == turno.hora.strftime('%H:%M'),
                                          func.lower(models.Turno.estado) != diccionario_estados.get('ESTADO_CANCELADO').lower()).first())#Si el estado es cancelado no lo tiene en cuenta
        if existente_no_cancelado:
            raise ValueError("El horario solicitado ya está reservado por otro paciente.")

        # Corrección: Cambio de .dict() (deprecado en Pydantic v2) a .model_dump()
        # Esto previene warnings y asegura compatibilidad con futuras versiones de Pydantic
        nuevo_turno = models.Turno(**turno.model_dump())
        nuevo_turno.estado = diccionario_estados.get('ESTADO_PENDIENTE')
        db.add(nuevo_turno)
        db.commit()
        db.refresh(nuevo_turno)

        return turno_diccionario(nuevo_turno, persona)
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al crear el turno: {e}")
    except Exception:
        raise

#Funcion para el endpoint GET/turnos (optimizada - sin redundancia)
def get_turnos(db: Session, skip: int, limit: int):
    """
    Obtiene turnos agrupados por persona para evitar redundancia
    Si una persona tiene múltiples turnos, se muestra una sola vez con todos sus turnos
    """
    try:
        turnos = db.query(models.Turno).options(joinedload(models.Turno.persona)).offset(skip).limit(limit).all()

        # Agrupar por persona para evitar redundancia
        personas_dict = {}
        for turno in turnos:
            persona_id = turno.persona_id
            if persona_id not in personas_dict:
                personas_dict[persona_id] = {
                    "persona": schemas.PersonaOut(
                        **turno.persona.__dict__,
                        edad=calcular_edad(turno.persona.fecha_nacimiento)
                    ),
                    "turnos": []
                }
            personas_dict[persona_id]["turnos"].append({
                "id": turno.id,
                "fecha": turno.fecha,
                "hora": turno.hora,
                "estado": turno.estado
            })

        return list(personas_dict.values())
    except Exception as e:
        raise Exception(f"Error al consultar turnos: {e}")
    

def delete_turno(turno_id: int, db: Session):
    """
        Eliminación física del turno
        El registro se elimina de la base de datos
    """
    try:
        turno_eliminar = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
        if turno_eliminar:
            # Validar que el turno no esté asistido
            if turno_eliminar.estado.lower() == diccionario_estados.get('ESTADO_ASISTIDO').lower():
                raise ValueError("No se puede eliminar un turno que ya fue asistido")

            db.delete(turno_eliminar)
            db.commit()
            return True #exito
        return False
    except ValueError:
        # Relanza ValueError para que sea manejado por el endpoint
        raise
    except Exception as e:
        db.rollback() #No se modifica la base de datos
        raise e


def siguiente_hora(hora_actual:time):

    """
        Solicita una hora(time)
        Retorna una hora(time) posterior agregando 30 minutos
    """

    #Para usar timedelta es necesario trabajar con un dato datetime
    fecha = datetime.today()
    objeto_hora = datetime.combine(fecha, hora_actual)

    #Extrae unicamente el dato time
    nueva_hora_datetime = objeto_hora + timedelta(minutes=30)
    return nueva_hora_datetime.time()


def get_turnos_disponibles(fecha: date, db: Session):
    """
        Solicita una fecha(date)
        Retorna una lista de turnos disponibles en esa fecha(date)
    """

    #Validacion por fecha (No se pueden ver los turnos de dias anteriores a hoy)
    hoy = datetime.today()
    if fecha < hoy.date():
        raise Exception("La fecha no puede ser anterior al día de hoy")
    
    #Variables para validacion de estado y fecha
    franja_horaria = copy(schemasTurno.settings.horarios_turnos) #Acceder a lista de horarios de atencion del .env #Acceder al diccionario de estados del .env    
    
    #Se filtran los turnos comparando con el .env cargado previamente
    turnos_reservados = [turno.hora for turno in db.query(models.Turno.hora).filter(and_(models.Turno.fecha == fecha, or_(models.Turno.estado == diccionario_estados.get('ESTADO_ASISTIDO'), models.Turno.estado == diccionario_estados.get('ESTADO_CONFIRMADO')))).all()]
    for reservado in turnos_reservados:
        if reservado in franja_horaria:
            franja_horaria.remove(reservado)

    #Define el rango horario
    hora_inicio = time(hour=9, minute=0)
    hora_fin =  time(hour=16,minute=30)
    posibles_turnos = [] #lista de horarios disponibles
    
    #Bucle para buscar turnos disponibles
    hora = hora_inicio
    while hora <= hora_fin:
        if hora not in turnos_reservados: 
            posibles_turnos.append(hora.strftime("%H:%M")) #Ajusta el formato de fecha
        hora = siguiente_hora(hora)

    return posibles_turnos
#Funcion para tener el turno por ID
def get_turno(db: Session, turno_id: int):
    try:
        turno = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()
        if not turno:
            return None
        return turno_diccionario(turno,turno.persona) #Retorno el diccionario con la persona incluida
    except Exception as e:
        raise Exception(f"Error al consultar turno: {e}")

#Funcion para cancelar un turno específico
def cancelar_turno(db: Session, turno_id: int):
    turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

    if not turno_db:
        return None

    # Validar que el turno esté en estado pendiente (optimización: 1 comparación en lugar de 2)
    if turno_db.estado.lower() != diccionario_estados.get('ESTADO_PENDIENTE').lower():
        raise ValueError("Solo se pueden cancelar turnos en estado Pendiente")

    try:
        # Cambiar estado a cancelado
        turno_db.estado = diccionario_estados.get('ESTADO_CANCELADO')
        db.commit()
        db.refresh(turno_db)

        return turno_diccionario(turno_db, turno_db.persona)
    except Exception as e:
        db.rollback()
        raise e

#Funcion para confirmar un turno específico
def confirmar_turno(db: Session, turno_id: int):
    turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

    if not turno_db:
        return None

    # Validar que el turno esté en estado pendiente (optimización: 1 comparación en lugar de 2)
    if turno_db.estado.lower() != diccionario_estados.get('ESTADO_PENDIENTE').lower():
        raise ValueError("Solo se pueden confirmar turnos en estado Pendiente")

    try:
        # Cambiar estado a confirmado
        turno_db.estado = diccionario_estados.get('ESTADO_CONFIRMADO')
        db.commit()
        db.refresh(turno_db)

        return turno_diccionario(turno_db, turno_db.persona)
    except Exception as e:
        db.rollback()
        raise e

#Funcion para actualizar su turno por ID
def update_turno(db: Session, turno_id: int, turno_update: schemasTurno.TurnoUpdate):
   turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

   if not turno_db:
       return None

   # Validar que el turno no esté asistido o cancelado antes de modificar
   if turno_db.estado.lower() in [diccionario_estados.get('ESTADO_ASISTIDO').lower(), diccionario_estados.get('ESTADO_CANCELADO').lower()]:
       raise ValueError(f"No se puede modificar un turno {turno_db.estado.lower()}")

   #Si ingresa valores nuevos los cambia, pero si no lo hace quedan los mismos
   nueva_fecha = turno_update.fecha if turno_update.fecha is not None else turno_db.fecha
   nueva_hora = turno_update.hora if turno_update.hora is not None else turno_db.hora
   nuevo_estado = turno_update.estado if turno_update.estado is not None else turno_db.estado


    #creamos turno_provisional para que contenga los datos nuevos y llamamos a validar_fechaYhora para ver si cumple con las condiciones
   turno_provisional = schemasTurno.TurnoCreate(fecha= nueva_fecha, hora= nueva_hora, persona_id=turno_db.persona_id)
   error = validar_fecha_hora(turno_provisional)
   if error:
       raise ValueError(error)
   
    #existente compara si hay dos fechas iguales pero con distinto id, quiere decir que hay dos turnos que se estan por superponer
   existente = db.query(models.Turno).filter(
       models.Turno.fecha == nueva_fecha,
       func.strftime('%H:%M', models.Turno.hora) == nueva_hora.strftime('%H:%M'), #pasa el dato a str con horas y minutos para poder compararlo
       models.Turno.id != turno_db.id
   ).first()

    #si es existente, error
   if existente:
       raise ValueError("Ya existe un turno reservado en esa fecha y hora")
   
   if turno_update.estado is not None: #Verifica si el usuario quiere modificar el turno
            
            # 1. Obtenemos los VALORES permitidos del diccionario (ej: ["Pendiente", "Cancelado", ...])
            #    'diccionario_estados' ya está definido al principio del archivo
            estados_permitidos_valores = list(diccionario_estados.values()) # Convertimos a lista por si acaso
            
            # 2. Creamos una lista de esos valores en minúscula para la comparación
            estados_permitidos_lower = [estado.lower() for estado in estados_permitidos_valores]

            # 3. Comparamos la entrada del usuario (en minúscula)
            estado_enviado_lower = turno_update.estado.lower()
            
            if estado_enviado_lower not in estados_permitidos_lower:
                # 4. Si no es válido, lanzamos un error con los valores correctos (capitalizados)
                raise ValueError(
                    f"Estado inválido. Los estados permitidos son: {', '.join(estados_permitidos_valores)}"
                )
            
            # 5. Si es válido, encontramos el valor con la capitalización correcta y lo asignamos
            #    Esto asegura que en la BD se guarde "Cancelado" y no "cancelado".
            for estado_valido in estados_permitidos_valores:
                if estado_valido.lower() == estado_enviado_lower:
                    nuevo_estado = estado_valido # Asignamos el valor correcto
                    break
   
   try:
       #Asignacion de los nuevos valores
       turno_db.fecha = nueva_fecha
       turno_db.hora = nueva_hora
       turno_db.estado =nuevo_estado

       db.commit()
       db.refresh(turno_db)

       return turno_diccionario(turno_db,turno_db.persona)
   except Exception as e:
       db.rollback() #creamos un rollback por si hay un error que no modifique los datos que ya estaban
       raise e


#Funcion para el reporte de turnos por dni (optimizada - sin redundancia de datos de persona)
def get_turnos_por_dni(db: Session, dni: str):

    #Filtra a la persona por dni
    persona = db.query(models.Persona).filter(models.Persona.dni == dni).first()
    if not persona:
        return None #Si no la encuentra devuelve None

    #Buscar todos los turnos de la persona
    turnos_db = db.query(models.Turno).filter(models.Turno.persona_id == persona.id).all()

    #Estructura optimizada: persona una vez, turnos sin redundancia
    persona_out = schemas.PersonaOut(
        **persona.__dict__,
        edad=calcular_edad(persona.fecha_nacimiento)
    )

    turnos_sin_persona = [
        {
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora,
            "estado": turno.estado
        }
        for turno in turnos_db
    ]

    return {
        "persona": persona_out,
        "turnos": turnos_sin_persona,
        "total_turnos": len(turnos_sin_persona)
    }


#Funcion del reporte de turnos cancelados (minimo 5)

def get_personas_turnos_cancelados(db: Session, min_cancelados: int):

    personas_estado_cancelado =(
    db.query(models.Persona, func.count(models.Turno.id).label("contador_de_turnos")) #Trae a la persona, y un contador de sus turnos
    .join(models.Turno, models.Persona.id == models.Turno.persona_id).filter(func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower())
    #Uso join para unir a la persona con sus turnos mediante el persona_id y filtro los del estado "cancelado"
    .group_by(models.Persona.id) #Agrupamos por persona
    .having(func.count(models.Turno.id) >= min_cancelados).all()
     #filtrar por las personas que cumplen el minimo de turnos cancelados y mostrar los resultados
    )

    lista_cancelados = []

    #Para cada persona encontrada, sacamos el detalle de sus turnos cancelados
    for persona, count in personas_estado_cancelado:
        turnos_cancelados_detalle = (
            db.query(models.Turno).options(joinedload(models.Turno.persona))
            .filter(
                models.Turno.persona_id == persona.id, #filtramos los turnos de la persona
                func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower() #filtramos por estado cancelado
            )
            .all() #devolvemos el detalle de los turnos
        )

        #Estructura optimizada: turnos sin datos redundantes de persona
        turnos_limpios = [
            {
                "id": turno.id,
                "fecha": turno.fecha,
                "hora": turno.hora,
                "estado": turno.estado
            }
            for turno in turnos_cancelados_detalle
        ]

        #Lo mismo para la persona
        persona_estructurada = schemas.PersonaOut(
            **persona.__dict__, #obtiene los datos de la persona y ** esto hace que los separe para que schemas de personasOut tome lo que necesita
            edad= calcular_edad(persona.fecha_nacimiento)
        )

        #creamos el diccionario para una estructura clara
        lista_cancelados.append({
            "persona": persona_estructurada, #tomamos los datos limpios de personas
            "turnos_cancelados_contador": count, #sumamos el contador con el nombre que tiene en el schema
            "turnos_cancelados_detalle": turnos_limpios, #sumamos los detalles de los turnos cancelados (sin redundancia)

        })


    return lista_cancelados #retornamos

def get_turnos_por_fecha(db: Session, fecha: date):
    """
    Obtiene turnos por fecha agrupados por persona (optimizado)
    Si una persona tiene múltiples turnos el mismo día, se muestra una sola vez con sus turnos
    """
    try:
        turnos = (
            db.query(models.Turno).options(joinedload(models.Turno.persona))
            .filter(models.Turno.fecha == fecha)
            .all()
        )

        #Agrupar turnos por persona para evitar redundancia
        personas_dict = {}
        for turno in turnos:
            persona_id = turno.persona_id
            if persona_id not in personas_dict:
                personas_dict[persona_id] = {
                    "persona": {
                        "id": turno.persona.id,
                        "nombre": turno.persona.nombre,
                        "dni": turno.persona.dni
                    },
                    "turnos": []
                }
            personas_dict[persona_id]["turnos"].append({
                "id": turno.id,
                "hora": turno.hora.strftime("%H:%M"),
                "estado": turno.estado
            })

        return list(personas_dict.values())
    except SQLAlchemyError as e:
        raise Exception(f"Error de base de datos al consultar turnos por fecha: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado al obtener turnos por fecha: {e}") 

def get_turnos_cancelados_mes_actual(db: Session):

    try:

        fecha_actual = datetime.now()#obtiene la fecha actual para obtener el mes actual y el año, de esa manera filtra los resultados
        anio_actual = fecha_actual.year
        mes_actual = fecha_actual.month
    
        resultados = (
            db.query(
                func.date(models.Turno.fecha).label("dia"),
                func.count(models.Turno.id).label("cantidad")#Cuando se realiza la agrupacion de los resultados se generan estos dos atributos
            )                                                #que van a indicar el dia por el que se agrupo y la cantidad de turnos cancelados que hubo   
            .filter(
                func.strftime("%Y", models.Turno.fecha) == str(anio_actual),
                func.strftime("%m", models.Turno.fecha) == f"{mes_actual:02d}",#filtra los turnos transformando el formato de datetime a string para poder compararlos
                func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower()
            )
            .group_by(func.date(models.Turno.fecha))#agrupa por dia, donde haya turnos cancelados, los resultados me van a devolver la cantidad y la fecha
            .order_by(func.date(models.Turno.fecha))#ordena los resultados segun la fecha
            .all()
        )
        
        turnos_mes = (
                db.query(models.Turno)
                .filter(
                    func.strftime("%Y", models.Turno.fecha) == str(anio_actual),
                    func.strftime("%m", models.Turno.fecha) == f"{mes_actual:02d}",
                    func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower()
                ).all() #obtengo el detalle de los turnos de ese mes
            )
        
        turnos_por_dia = []#creo una lista que tendra todos los turnos cancelados. Contiene sublistas con turnos de un mismo dia
        for fila in resultados:
            dia = fila.dia
            cantidad = fila.cantidad #es la informacion que tendra cada sub lista de turnos en un mismo dia, la fecha y la cantidad 
            turnos_detalle = [
                {
                    "id": turno.id,
                    "persona_id": turno.persona_id,
                    "hora": turno.hora.strftime("%H:%M"),
                    "estado": turno.estado
                }
                for turno in turnos_mes if turno.fecha.strftime("%Y-%m-%d") == str(fila.dia) #una vez que tengo los turnos que corresponden a esa fila del resultado, reformo los datos para que se muestren facilmente
            ]
            turnos_por_dia.append({
                "fecha": dia,
                "cantidad_cancelados": cantidad,
                "turnos": turnos_detalle
            }) #por cada dia muestro sus datos (fecha y cantidad de turnos cancelados) y devuelvo la sublista formada con los datos del turno
        
        total_turnos_cancelados = sum(fila.cantidad for fila in resultados)

        return {
            "anio": anio_actual,
            "mes": meses_nombres[mes_actual-1],
            "cantidad": total_turnos_cancelados,
            "detalle_por_dia": turnos_por_dia
        } #genero el cuerpo de respuesta final, con una lista de turnos por dia que contiene la sublista con los detalles de cada turno
    except SQLAlchemyError as e:
        raise Exception(f"Error en la base de datos al generar el reporte de turnos cancelados: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado al generar el reporte de turnos cancelados: {e}")

def get_turnos_confirmados_desde_hasta(fecha_desde, fecha_hasta, db, pag=1, por_pag=5):

    """
    Solicita una fecha de inicio y fin de la consulta
    Retorna una lista de turnos con estado "confirmado" entre esas fechas inclusive, agrupados por persona
    Se aplica una paginación fija con límite 5 páginas
    """

    if fecha_hasta < fecha_desde:
        raise ValueError("La fecha inicial a consultar no puede ser posterior a la fecha final a consultar")
    
    offset = (pag - 1) * por_pag #Indica cuantos registros "saltar" para mostrar sólo los que corresponden a esa página
    
    consulta_turnos = (
        db.query(models.Turno)
        .options(joinedload(models.Turno.persona)) #Agregar la persona
        .filter(
            models.Turno.fecha >= fecha_desde,
            models.Turno.fecha <= fecha_hasta,
            models.Turno.estado == diccionario_estados.get('ESTADO_CONFIRMADO')
        )
    )
    total_registros = consulta_turnos.count() #Cuenta la cantidad de turnos confirmados
    turnos_filtrados = consulta_turnos.offset(offset).limit(por_pag).all() #Aplica paginación
    
    total_pag = math.ceil(total_registros/por_pag)
    metadata = schemasTurno.MetadataPaginacion(
        pag=pag,
        por_pag=por_pag,
        total_pag=total_pag,
        tiene_posterior=pag < total_pag,
        tiene_anterior=pag > 1
    ) 
    #Convertimos a diccionario para el response model
    turnos_confirmados = []
    for turno in turnos_filtrados:
        turnos_confirmados.append(turno_diccionario(turno, turno.persona))
  
    return {
            "turnos": turnos_confirmados,
            "total_registros": total_registros,
            "metadata": metadata,
            
    }

#Funcion de turnos cancelados en el mes actual, reformado para que solo realice una consulta, sin usar group_by, por recomendacion en la devolucion de la presentacion 
def get_turnos_cancelados_mes_actual_reformado(db: Session):
    try:
        # Fecha actual
        fecha_actual = datetime.now()
        anio_actual = fecha_actual.year
        mes_actual = fecha_actual.month

        # Obtener todos los turnos cancelados del mes actual en una sola consulta
        turnos_cancelados = (
            db.query(models.Turno)
            .options(joinedload(models.Turno.persona))
            .filter(
                func.strftime("%Y", models.Turno.fecha) == str(anio_actual),
                func.strftime("%m", models.Turno.fecha) == f"{mes_actual:02d}",
                func.lower(models.Turno.estado) == diccionario_estados.get("ESTADO_CANCELADO").lower()
            )
            .order_by(models.Turno.persona_id, models.Turno.fecha)
            .all()
        )
        # Agrupar turnos por persona, se diferencia del otro endpoint en que no realiza la reforma de los datos por fecha, sino por persona.
        personas_dict = {}
        for turno in turnos_cancelados:
            persona = turno.persona
            if persona.id not in personas_dict:
                personas_dict[persona.id] = {
                    "persona": {
                        "id": persona.id,
                        "nombre": persona.nombre,
                        "dni": persona.dni,
                        "telefono":persona.telefono,
                        "cantidad_de_cancelados": 0
                    },
                    "turnos_cancelados": []
                }

            personas_dict[persona.id]["turnos_cancelados"].append({
                "id": turno.id,
                "fecha": turno.fecha.strftime("%Y-%m-%d"),
                "hora": turno.hora.strftime("%H:%M"),
                "estado": turno.estado
            })
            personas_dict[persona.id]["persona"]["cantidad_de_cancelados"] += 1

        # Convertir el diccionari a lista, para respuesta
        detalle_por_persona = list(personas_dict.values())

        # Calcular cantidad total de turnos cancelados
        cantidad_total = len(turnos_cancelados)

        return {
            "anio": anio_actual,
            "mes": meses_nombres[mes_actual - 1],
            "cantidad_total": cantidad_total,
            "detalle_por_persona": detalle_por_persona
        }

    except SQLAlchemyError as e:
        raise Exception(f"Error en la base de datos al generar el reporte de turnos cancelados: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado al generar el reporte de turnos cancelados: {e}")



#=============== FUNCIONES PARA GENERAR ARCHIVOS CSV DE REPORTE ===================

def generar_csv_turnos_cancelados(db: Session, min_cancelados: int):
    #Reutilizo la funcion para traer los resultados del deporte en formato JSON (diccionario o lista de diccionarios)
    lista_cancelados = get_personas_turnos_cancelados(db, min_cancelados)#retorna una lista de persona con sus turnos cancelados

    #Si no hay resultados reotna vacio para mostrar el codigo 204
    if not lista_cancelados:
        return None

    filas_para_df = []#genero una lista con los datos que se van a mostrar en el archivo csv.
    for resultado in lista_cancelados:#cada resultado tiene a una persona con su lista de turnos cancelados 
        persona = resultado["persona"]
        contador = resultado["turnos_cancelados_contador"]

        #Accedo a cada turno de cada persona que esta en la lista
        for turno in resultado["turnos_cancelados_detalle"]:#para mostrar los datos correctamente en un unico archivo csv, por cada turno cancelado se van a mostrar los datos de la persona aunque se repitan
            filas_para_df.append({
                "nombre_persona": persona.nombre,
                "dni": persona.dni,
                "telefono": persona.telefono,
                "habilitado": persona.habilitado,
                "cant_cancelados": contador,
                "turno_id": turno["id"],
                "fecha": turno["fecha"],
                "hora": turno["hora"]
            })

    # Crear DataFrame con pandas, para poder manipular los datos y generar el archivo csv
    df = pd.DataFrame(filas_para_df)

    #Cmbiar el formato para mas claridad
    df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%d/%m/%Y")#Se accede al dato en formato date para reformatearlo y mostrarlo correctamente como string
    df["hora"] = df["hora"].astype(str).str[:5]#Se accede al dato y se pasa a formto string para mostrarlo correctamente
    df["dni"] = df["dni"].astype(str)#cambio el tipo de dato a string
    df["habilitado"] = df["habilitado"].map({True: "Si", False: "No"})#Se cambia el formato para que se muestre con mas claridad el estado habilitado
    df["telefono"] = df["telefono"].astype(str).apply(lambda x: f"'{x}")#cambio el tipo de dato a string, y uso funcion lambda para poner una ' adelante de todos lo numeros, asi lo interpreta como string y muestra el numero completo

    # Ordenar filas
    df.sort_values(by=["nombre_persona", "fecha", "hora"], inplace=True)

    # Convertir a CSV en memoria, lo guarda en la RAM y no crea un archivo, se utiliza para luego enviarlo con fastapi y que se pueda descargar.
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")#Se convierte el DataFrame en archivo csv y se guarda en el buffer.
    csv_buffer.seek(0)#Vuelve a la linea 0 del buffer, para que se lea desde ahi.

    return csv_buffer

def generar_csv_turnos_confirmados(db, fecha_desde, fecha_hasta, pag, por_pag):
    try:
        datos = get_turnos_confirmados_desde_hasta(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            db=db,
            pag=pag,
            por_pag=por_pag   
        )#Obtengo los datos para geerar el reporte en csv, me entrega un dicconario con una lista de turnos y la metadata de la paginacion

        turnos = datos["turnos"]#Obtengo los turnos para trabajr con los datos que se tienen que mostrar en el archivo csv.
        # Si no hay turnos devuelve None
        if not turnos:
            return None
        # Armar filas para df.
        filas_para_df = []
        for t in turnos:
            persona = t["persona"]
            filas_para_df.append({
                "nombre_persona": persona["nombre"],
                "dni": persona["dni"],
                "telefono": persona["telefono"],
                "habilitado": persona["habilitado"],
                "turno_id": t["id"],
                "fecha": t["fecha"],
                "hora": t["hora"],
                "estado": t["estado"]
            })

        # Crear DataFrame
        df = pd.DataFrame(filas_para_df)
        #Cmbia el formato para mas claridad
        df["fecha"] = pd.to_datetime(df["fecha"]).dt.strftime("%d/%m/%Y")#Se accede al dato en formato date para reformatearlo y mostrarlo correctamente como string
        df["hora"] = df["hora"].astype(str).str[:5]#Se accede al dato y se pasa a formto string para mostrarlo correctamente
        df["dni"] = df["dni"].astype(str)#cambio el tipo de dato a string
        df["habilitado"] = df["habilitado"].map({True: "Si", False: "No"})#Se cambia el formato para que se muestre con mas claridad el estado habilitado
        df["telefono"] = df["telefono"].astype(str).apply(lambda x: f"'{x}")#cambio el tipo de dato a string, y uso esa funcion lambda para poner una ' adelante de todos lo numeros, asi lo interpreta como string y muestra el numero completo
        #Ordenar filas
        df.sort_values(by=["nombre_persona", "fecha", "hora"], inplace=True)

        #creo una fila mas para la metadata de la paginacion, para saber cuantos registros hay y en que pagina esta
        #.loc ubica en que parte del df se va a ubicar la nueva linea, como le pongo hasta el tamanio del df, va a ser en la ultima posicion
        df.loc[len(df)] = [
            "",                     
            "",                    
            "",                    
            "",#Dejo las primeras columnas de la untima fila vacias porque no hay datos que mostrar.                     
            "METADATA:",#Indico que la informacion pertenece a la metdata de la paginacion             
            f"pag={datos['metadata'].pag}/{datos['metadata'].total_pag}",  
            f"por_pag={datos['metadata'].por_pag}",                        
            f"total_registros={datos['total_registros']}"                   
        ]

        # Convertir a CSV en memoria, lo guarda en la RAM y no crea un archivo, se utiliza para luego enviarlo con fastapi y que se pueda descargar.
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")#Se convierte el DataFrame en archivo csv y se guarda en el buffer.
        csv_buffer.seek(0)#Vuelve a la linea 0 del buffer, para que se lea desde ahi.
        return csv_buffer
    except Exception as e:
        raise Exception(f"Error inesperado al generar CSV de turnos confirmados: {e}")
    

def generar_csv_turnos_cancelados_reformado(db: Session):
    try:
        datos = get_turnos_cancelados_mes_actual_reformado(db)
        if not datos or not datos.get("detalle_por_persona"):
            return None

        filas_csv = []
        for datos_persona in datos["detalle_por_persona"]:
            persona = datos_persona["persona"]
            turnos = datos_persona["turnos_cancelados"]
            for turno in turnos:
                # Creamos una fila de CSV con todos los detalles
                filas_csv.append({
                    "persona_id": persona["id"],
                    "nombre_persona": persona["nombre"],
                    "dni": persona["dni"],
                    "total_cancelados_persona": persona["cantidad_de_cancelados"],
                    "turno_id": turno["id"],
                    "fecha_turno": turno["fecha"],
                    "hora_turno": turno["hora"],
                    "estado_turno": turno["estado"]
                })

        df = pd.DataFrame(filas_csv)

        df["fecha_turno"] = pd.to_datetime(df["fecha_turno"]).dt.strftime("%d/%m/%Y")#Se accede al dato en formato date para reformatearlo y mostrarlo correctamente como string
        df["hora_turno"] = df["hora_turno"].astype(str).str[:5]#Se accede al dato y se pasa a formto string para mostrarlo correctamente
        df["dni"] = df["dni"].astype(str)#cambio el tipo de dato a string
        #Ordenar filas
        df.sort_values(by=["nombre_persona", "fecha_turno", "hora_turno"], inplace=True)

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")
        csv_buffer.seek(0)
        return csv_buffer
    except Exception as e:
        raise Exception(f"Error inesperado al generar PDF de turnos cancelados: {e}")

    

#=============== FUNCIONES PARA GENERAR ARCHIVOS PDF DE REPORTE ===================

def generar_pdf_turnos_cancelados_mes_actual_reformado(datos: dict):
    try:
        if not datos or not datos.get("detalle_por_persona"):
            return None
        # Crear documento
        pdf = Document()
        page = Page()#crea una pagina
        pdf.add_page(page)
        layout = SingleColumnLayout(page)#Permite agregar contenido y tiene ajustes automaticos sobre donde ubicar cada cosa que se agregue a la pagina, es un controlador de la misma.
        # Se le agrega un titulo al documento
        layout.add(
            Paragraph(
                f"Reporte de Turnos Cancelados — {datos['mes'].capitalize()} {datos['anio']}",
                font="Helvetica-Bold", #El tipo de etra
                font_size=16, #Tamanio de las letras
                margin_bottom=0, #Minima separacion con el siguiente contenido
                horizontal_alignment=Alignment.CENTERED #Se indica que se centre
            )
        )
        layout.add(Paragraph(f"Total de turnos cancelados: {datos['cantidad_total']}", margin_top=0, margin_bottom=0, font="Helvetica-Bold", font_size=12))
        layout.add(Paragraph(f"Cantidad de personas con turnos cancelados: {len(datos['detalle_por_persona'])}", margin_top=0, font="Helvetica-Bold", font_size=12))
        layout.add(HorizontalRule()) #Agrega una linea horizontal

        # Recorrer personas
        for fila in datos["detalle_por_persona"]:
            persona = fila["persona"]
            turnos = fila["turnos_cancelados"]
            
            layout.add(
                Paragraph(
                    f"Persona: {persona['nombre']} (DNI {persona['dni']}), ID: {persona['id']}, contacto: {persona['telefono']}", #Agrego los datos de cada persona mientras se recorre
                    font="Helvetica-Bold",
                    margin_bottom=0
                )
            )
            layout.add(Paragraph(f"Cantidad de turnos cancelados: {persona['cantidad_de_cancelados']}", margin_top=0, margin_bottom=0))

            #Creo una tabla con los turnos cancelados de cada persona. Una tabla por turnos correspondientes a cada persona.
            total_filas = 1 + len(turnos) #La cantidad de turnos cancelados de cada persona mas la fila de los encabezados.
            encabezados = ["ID Turno", "Fecha", "Hora", "Estado", "Persona_id"] #Los encaezados que quiero mostrar de los turnos de cada persona.
            tamanio_columnas = [Decimal(50),Decimal(80), Decimal(40), Decimal(80), Decimal(50)] #Indico el tamaño de las celdas para cada atributo.
            table = FixedColumnWidthTable(number_of_rows=total_filas, number_of_columns=5, column_widths=tamanio_columnas)#Genero la tabla, indicando sus atributos.

            for encabezado in encabezados:
                table.add(TableCell(Paragraph(encabezado, font="Helvetica-Bold", font_size=11, horizontal_alignment=Alignment.CENTERED), 
                                    background_color= HexColor("#3465A4"))) #Agrego contenido a cada celda de la primera fila. Los datos y su formato y un color de fondo.
                
            for t in turnos:
                table.add(TableCell (Paragraph(str(t["id"]), horizontal_alignment=Alignment.CENTERED), background_color= HexColor("#E6F0FF")))
                table.add(TableCell (Paragraph(t["fecha"], horizontal_alignment=Alignment.CENTERED), background_color= HexColor("#E6F0FF")))
                table.add(TableCell (Paragraph(t["hora"], horizontal_alignment=Alignment.CENTERED), background_color= HexColor("#E6F0FF")))
                table.add(TableCell (Paragraph(t["estado"], horizontal_alignment=Alignment.CENTERED), background_color= HexColor("#D9534F")))#Agrego los datos de cada turno cancelado, con un color de fondo en cada celda.
                table.add(TableCell (Paragraph(str(persona["id"]), horizontal_alignment=Alignment.CENTERED), background_color= HexColor("#E6F0FF")))
            table.set_padding_on_all_cells(Decimal(3), Decimal(3), Decimal(2), Decimal(3)) #Agrego separacion entre el contenido y todos los bordes.
            layout.add(table) #Agrego la tabla a la pagina.
            layout.add(Paragraph(" ", margin_top=0, margin_bottom=0))
            layout.add(HorizontalRule())

        buffer = BytesIO() #Genero un archivo en memoria, donde se va a guardar el pdf temporal que se enviara con fastapi en formato de bytes.
        PDF.dumps(buffer, pdf) #Genero el pdf y lo guardo en el buffer.
        buffer.seek(0) #Indico que se vuelva al principio del archivo para leerlo correctamente.
        return buffer
    except Exception as e:
        raise Exception(f"Error inesperado al generar PDF de turnos cancelados: {e}")
