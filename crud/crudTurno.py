from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from sqlalchemy.exc import SQLAlchemyError
import models.models as models, schemas.schemasTurno as schemasTurno, schemas.schemas as schemas
from datetime import date, time, timedelta, datetime
from crud.crud import calcular_edad
from copy import copy
from schemas.schemasTurno import settings
import pandas as pd
from io import StringIO


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

#Funcion para el endpoint GET/turnos
def get_turnos(db: Session, skip: int, limit: int):
    try:
        from sqlalchemy.orm import joinedload
        turnos = db.query(models.Turno).options(joinedload(models.Turno.persona)).offset(skip).limit(limit).all()
        turnos_lista = []
        for turno in turnos:
            turnos_lista.append(turno_diccionario(turno, turno.persona))
        return turnos_lista
    except Exception as e:
        raise Exception(f"Error al consultar turnos: {e}")
#Funcion para eliminar turno por id
def delete_turno(turno_id: int, db: Session):

    try:
        turno_eliminar = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
        if turno_eliminar:
            # Validar que el turno no esté asistido
            if turno_eliminar.estado.lower() == "asistido":
                raise ValueError("No se puede eliminar un turno que ya fue asistido")

            db.delete(turno_eliminar)
            db.commit()
            return True #exito
        return False
    except ValueError:
        # Re-lanzar ValueError para que sea manejado por el endpoint
        raise
    except Exception as e:
        db.rollback() #No se modifica la base de datos
        raise e

#Funcion para sumar 30 minutos a una hora:time
def siguiente_hora(hora_actual:time):

    #Para usar timedelta es necesario trabajar con un dato datetime
    fecha = datetime.today()
    objeto_hora = datetime.combine(fecha, hora_actual)

    #Extrae unicamente el dato time
    nueva_hora_datetime = objeto_hora + timedelta(minutes=30)
    return nueva_hora_datetime.time()

#Funcion para mostrar turnos disponibles por fecha ingresada
def get_turnos_disponibles(fecha: date, db: Session):
    #Validacion por fecha (No se pueden ver los turnos de dias anteriores a hoy)
    hoy = datetime.today()
    if fecha < hoy.date():
        raise Exception("La fecha no puede ser anterior al día de hoy")
    
    #Variables para validacion de estado y fecha
    franja_horaria = copy(schemasTurno.settings.horarios_turnos) #Acceder a lista de horarios de atencion del .env
    estados_turnos = schemasTurno.settings.estados_posibles #Acceder al diccionario de estados del .env    
    
    turnos_reservados = [turno.hora for turno in db.query(models.Turno.hora).filter(and_(models.Turno.fecha == fecha, or_(models.Turno.estado == estados_turnos.get('ESTADO_ASISTIDO'), models.Turno.estado == estados_turnos.get('ESTADO_CONFIRMADO')))).all()]
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
        from sqlalchemy.orm import joinedload
        turno = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()
        if not turno:
            return None
        return turno_diccionario(turno,turno.persona) #Retorno el diccionario con la persona incluida
    except Exception as e:
        raise Exception(f"Error al consultar turno: {e}")

#Funcion para cancelar un turno específico
def cancelar_turno(db: Session, turno_id: int):
    from sqlalchemy.orm import joinedload
    turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

    if not turno_db:
        return None

    # Validar que el turno no esté ya asistido
    if turno_db.estado.lower() == "asistido":
        raise ValueError("No se puede cancelar un turno que ya fue asistido")

    # Validar que el turno no esté ya cancelado
    if turno_db.estado.lower() == "cancelado":
        raise ValueError("El turno ya está cancelado")

    try:
        # Cambiar estado a cancelado
        turno_db.estado = "Cancelado"
        db.commit()
        db.refresh(turno_db)

        return turno_diccionario(turno_db, turno_db.persona)
    except Exception as e:
        db.rollback()
        raise e

#Funcion para confirmar un turno específico
def confirmar_turno(db: Session, turno_id: int):
    from sqlalchemy.orm import joinedload
    turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

    if not turno_db:
        return None

    # Validar que el turno no esté ya asistido
    if turno_db.estado.lower() == "asistido":
        raise ValueError("No se puede confirmar un turno que ya fue asistido")

    # Validar que el turno no esté cancelado
    if turno_db.estado.lower() == "cancelado":
        raise ValueError("No se puede confirmar un turno cancelado")

    try:
        # Cambiar estado a confirmado
        turno_db.estado = "Confirmado"
        db.commit()
        db.refresh(turno_db)

        return turno_diccionario(turno_db, turno_db.persona)
    except Exception as e:
        db.rollback()
        raise e

#Funcion para actualizar su turno por ID
def update_turno(db: Session, turno_id: int, turno_update: schemasTurno.TurnoUpdate):
   from sqlalchemy.orm import joinedload
   turno_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.id == turno_id).first()

   if not turno_db:
       return None

   # Validar que el turno no esté asistido o cancelado antes de modificar
   if turno_db.estado.lower() in ["asistido", "cancelado"]:
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
        estados_permitidos = settings.estados_turnos #Trae la lista de estados del archivo .env
        if turno_update.estado.lower() not in [i.lower() for i in estados_permitidos]: #cree un array para que todos los estados permitidos se tomen como minusculas tambien   
            raise ValueError( #si el estado enviado no esta en la lista va a este raise, sino sigue con el programa
                 f"Estado inválido. Los estados permitidos son: {', '.join(estados_permitidos)}" #Si no es ninguno de los mencionados tira un mensaje
        )


   
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


#Funcion para el reporte de turnos por dni
def get_turnos_por_dni(db: Session, dni: str):
    
    #Filtra a la persona por dni
    persona = db.query(models.Persona).filter(models.Persona.dni == dni).first()
    if not persona:
        return None #Si no la encuentra devuelve None
    
    #Buscar todos los turnos de la persona
    #joinedload sirve para optimizar la instruccion, en vez de consultar por cada turno para que traiga los datos, los trae a todos en un solo llamado
    turnos_db = db.query(models.Turno).options(joinedload(models.Turno.persona)).filter(models.Turno.persona_id == persona.id).all()

    #Hacer la conversion de los datos
    resultado = []
    for turno in turnos_db:
        #Bucle para convertir y añadir el diccionario a la lista
        resultado.append(turno_diccionario(turno,turno.persona))

    return resultado


#Funcion del reporte de turnos cancelados (minimo 5)

def get_personas_turnos_cancelados(db: Session, min_cancelados: int):

    personas_estado_cancelado =(
    db.query(models.Persona, func.count(models.Turno.id).label("contador_de_turnos_cancelados")) #Trae a la persona, y un contador de sus turnos cancelados
    .join(models.Turno, models.Persona.id == models.Turno.persona_id).filter (models.Turno.estado == "Cancelado")
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
                models.Turno.estado == "Cancelado" #filtramos por estado cancelado
            )
            .all() #devolvemos el detalle de los turnos
        )

        #Le damos una estructura limpia a los datos con turno_diccionario
        turnos_limpios =[turno_diccionario(i, i.persona) for i in turnos_cancelados_detalle]

        #Lo mismo para la persona
        persona_estructurada = schemas.PersonaOut(
            **persona.__dict__, #obtiene los datos de la persona y ** esto hace que los separe para que schemas de personasOut tome lo que necesita
            edad= calcular_edad(persona.fecha_nacimiento)
        )
        
        #creamos el diccionario para una estructura clara
        lista_cancelados.append({
            "persona": persona_estructurada, #tomamos los datos limpios de personas
            "turnos_cancelados_contador": count, #sumamos el contador con el nombre que tiene en el schema
            "turnos_cancelados_detalle": turnos_limpios, #sumamos los detalles de los turnos cancelados

        })


    return lista_cancelados #retornamos

def get_turnos_por_fecha(db: Session, fecha: date):
    turnos = (
        db.query(models.Turno).options(joinedload(models.Turno.persona))
        .filter(models.Turno.fecha == fecha)
        .all()
    )

    turnos_lista = []
    for turno in turnos:
        turnos_lista.append({
            "id": turno.id,
            "fecha": turno.fecha,
            "hora": turno.hora.strftime("%H:%M"),
            "estado": turno.estado,
            "persona": {
                "nombre": turno.persona.nombre,
                "dni": turno.persona.dni
            }
        })#Devuelve una lista de diccionarios con los datos solicitados

    return turnos_lista

def get_turnos_cancelados_mes_actual(db: Session):

    hoy = datetime.now()#obtiene la fecha actual para obtener el mes actual y el año, de esa manera filtra los resultados
    anio_actual = hoy.year
    mes_actual = hoy.month
 
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
    
    if not resultados:
        return None
    
    turnos_por_dia = []#creo una lista que tendra todos los turnos cancelados. Contiene sublistas con turnos de un mismo dia
    for fila in resultados:
        dia = fila.dia
        cantidad = fila.cantidad #es la informacion que tendra cada sub lista de turnos en un mismo dia, la fecha y la cantidad

        turnos_dia = (
            db.query(models.Turno)
            .filter(
                func.date(models.Turno.fecha) == dia,
                func.lower(models.Turno.estado) == diccionario_estados.get('ESTADO_CANCELADO').lower()
            ).all() #para cada resultado del group_by por dia, busco los turnos que corresponden a cada uno de esos resultados para generar las sublistas con su informacion
        ) 

        turnos_detalle = [
            {
                "id": turno.id,
                "persona_id": turno.persona_id,
                "fecha": turno.fecha.strftime("%Y-%m-%d"),
                "hora": turno.hora.strftime("%H:%M"),
                "estado": turno.estado
            }
            for turno in turnos_dia #una vez que tengo los turnos que corresponden a esa fila del resultado, reformo los datos para que se muestren facilmente
        ]
        
        turnos_por_dia.append({
            "fecha": dia,
            "cantidad_cancelados": cantidad,
            "turnos": turnos_detalle
        }) #por cada dia muestro sus datos (fecha y cantidad de turnos cancelados) y devuelvo la sublista formada con los datos del turno
        
    meses= [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    mes_nombre = meses[mes_actual - 1]

    total_turnos_cancelados = sum(fila.cantidad for fila in resultados)

    return {
        "anio": anio_actual,
        "mes": mes_nombre,
        "cantidad": total_turnos_cancelados,
        "detalle_por_dia": turnos_por_dia
    } #genero el cuerpo de respuesta final, con una lista de turnos por dia que contiene la sublista con los detalles de cada turno


def get_turnos_confirmados_desde_hasta(db: Session, fecha_desde, fecha_hasta, page: int = 1,
    per_page: int = 5):

    """
    Solicita una fecha de inicio y fin de la consulta
    Retorna una lista de turnos con estado "confirmado" entre esas fechas inclusive
    Se aplica una paginación fija con límite 5 páginas
    """
    # Aplicar paginación
    offset = (page - 1) * per_page

    if fecha_hasta < fecha_desde:
        raise ValueError("La fecha inicial a consultar no puede ser posterior a la fecha final a consultar")
    
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
    turnos_filtrados = consulta_turnos.offset(offset).limit(per_page).all() #Aplica paginación

    #Convertimos a diccionario para el response model
    turnos_confirmados = []
    for turno in turnos_filtrados:
        turnos_confirmados.append(turno_diccionario(turno, turno.persona))
    return {
        "total_registros": total_registros,
        "turnos": turnos_confirmados
    }
        
def generar_csv_turnos_cancelados(db: Session, min_cancelados: int):

    # Reutilizamos tu función
    lista_cancelados = get_personas_turnos_cancelados(db, min_cancelados)

    if not lista_cancelados:
        return None

    filas = []

    for item in lista_cancelados:
        persona = item["persona"]
        contador = item["turnos_cancelados_contador"]

        for turno in item["turnos_cancelados_detalle"]:
            filas.append({
                "nombre_persona": persona.nombre,
                "dni": persona.dni,
                "telefono": persona.telefono,
                "habilitado": persona.habilitado,
                "cant_cancelados": contador,
                "turno_id": turno["id"],
                "fecha": turno["fecha"],
                "hora": turno["hora"]
            })

    # Crear DataFrame
    df = pd.DataFrame(filas)

    # Convertir a CSV en memoria (sin crear archivos en disco)
    buffer = StringIO()
    df.to_csv(buffer, index=False, sep=";")
    buffer.seek(0)

    return buffer




def generar_csv_turnos_confirmados(db, fecha_desde, fecha_hasta, pag, por_pag):
    """
    Genera un CSV con los turnos confirmados entre dos fechas.
    Reutiliza la función de paginación existente.
    Devuelve el contenido CSV como texto.
    """
    try:
        # Reutilizamos tu función de CRUD existente
        datos = get_turnos_confirmados_desde_hasta(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            db=db,
            pag=pag,
            por_pag=por_pag      # Traer todos sin paginar
        )

        turnos = datos["turnos"]  # Lista de diccionarios

        # Si no hay turnos → devolver None
        if not turnos:
            return None

        # Armar filas para CSV
        filas = []
        for t in turnos:
            persona = t["persona"]
            filas.append({
                "nombre": persona["nombre"],
                "dni": persona["dni"],
                "telefono": persona["telefono"],
                "habilitado": persona["habilitado"],
                "turno_id": t["id"],
                "fecha": t["fecha"],
                "hora": t["hora"],
                "estado": t["estado"]
            })

        # Crear DataFrame
        df = pd.DataFrame(filas)

        # Convertir a CSV en memoria
        buffer = StringIO()
        df.to_csv(buffer, index=False, sep=";")
        buffer.seek(0)

        return buffer

    except SQLAlchemyError as e:
        raise Exception(f"Error de base de datos al generar CSV de turnos confirmados: {e}")
    except Exception as e:
        raise Exception(f"Error inesperado al generar CSV de turnos confirmados: {e}")





