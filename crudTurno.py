from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemasTurno
from datetime import date, time, timedelta, datetime
from crud import calcular_edad

#Funciones para validad los atributos del cuerpo de entrada de datos
def validar_fechaYhora(turno: schemasTurno.TurnoCreate):

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

    seisMesesAtras = date.today() - timedelta(days=180)
    cantCancelados = db.query(models.Turno).filter(models.Turno.persona_id == turno.persona_id, 
                                                   models.Turno.estado == "cancelado", 
                                                   models.Turno.fecha >= seisMesesAtras).count()
    if (cantCancelados >= 5):
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
    
#Funcion para el endpoint POST/turnos
def create_turnos(db: Session, turno: schemasTurno.TurnoCreate):

    persona = db.query(models.Persona).filter(models.Persona.id == turno.persona_id).first()

    if not persona: 
        raise ValueError("Persona no encontrada")
    
    if(not habilitar_persona(db, turno, persona)):
        raise PermissionError ("La persona no esta habilitada")
    
    error = validar_fechaYhora(turno)
    if error:
        raise ValueError(error)
        
    existente = db.query(models.Turno).filter(models.Turno.fecha == turno.fecha, func.strftime('%H:%M', models.Turno.hora) == turno.hora.strftime('%H:%M')).first()

    if existente: 
        raise ValueError("El turno ya esta reservado")

    nuevo_turno = models.Turno(**turno.dict())
    
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)

    return turno_diccionario(nuevo_turno, persona)

#Funcion para el endpoint GET/turnos
def get_turnos(db: Session, skip: int, limit: int):
    turnos = db.query(models.Turno).offset(skip).limit(limit).all()
    if not turnos:
        raise ValueError("No hay turnos registrados")
    turnos_lista = []
    for turno in turnos:
        turnos_lista.append(turno_diccionario(turno, turno.persona))
    return turnos_lista

#Funcion para tener el turno por ID
def get_turno(db: Session, turno_id: int):
    turno = db.query(models.Turno).filter(models.Turno.id == turno_id).first()
    if not turno:
        return None 
    return turno_diccionario(turno,turno.persona) #Retorno el diccionario con la persona incluida

#Funcion para actualizar su turno por ID
def update_turno(db: Session, turno_id: int, turno_update: schemasTurno.TurnoUpdate):
   turno_db = db.query(models.Turno). filter(models.Turno.id == turno_id).first()

   if not turno_db:
       return None
   #Si ingresa valores nuevos los cambia, pero si no lo hace quedan los mismos
   nueva_fecha = turno_update.fecha if turno_update.fecha is not None else turno_db.fecha
   nueva_hora = turno_update.hora if turno_update.hora is not None else turno_db.hora
   nuevo_estado = turno_update.estado if turno_update.estado is not None else turno_db.estado


    #creamos turno_provisional para que contenga los datos nuevos y llamamos a validar_fechaYhora para ver si cumple con las condiciones
   turno_provisional = schemasTurno.TurnoCreate(fecha= nueva_fecha, hora= nueva_hora, persona_id=turno_db.persona_id)
   error = validar_fechaYhora(turno_provisional)
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
   
   
   if turno_update.estado is not None:
       estados_permitidos = {"pendiente", "cancelado", "confirmado", "asistido"}
       if turno_update.estado.lower() not in estados_permitidos: #verifica el estado que se cambia teniendo en cuenta minusculas   
           raise ValueError(f"Estado inválido. Los estados permitidos son: {', '.join(estados_permitidos)}") #Si no es ninguno de los mencionados tira un mensaje
   
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