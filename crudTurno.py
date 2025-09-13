from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemasTurno
from datetime import date, time, timedelta


def calcular_edad(fecha_nacimiento):
    from datetime import date
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def validar_hora(hora: time):
    if hora.hour < 9 or hora.hour >= 17:
        return False
    if hora.minute == 30 or hora.minute == 0:
        return True
    else:
        return False
    

    
def create_turnos(db: Session, turno: schemasTurno.TurnoCreate):

    persona = db.query(models.Persona).filter(models.Persona.id == turno.persona_id).first()

    if not persona: 
        return None, "Persona no encontrada"
    
    if turno.fecha < date.today():
        return None, "La fecha no puede ser menor a la de hoy"
    
    if not validar_hora(turno.hora):
        return None, "La hora debe ser entre las 9:00 y 16:30 cada 30 minutos"
     
    existente = db.query(models.Turno).filter(models.Turno.fecha == turno.fecha, func.strftime('%H:%M', models.Turno.hora) == turno.hora.strftime('%H:%M')).first()

    if existente: 
        return None, "El turno ya esta reservado"
    
    seisMesesAtras = date.today() - timedelta(days=180)
    cantCancelados = db.query(models.Turno).filter(models.Turno.persona_id == turno.persona_id, 
                                                   models.Turno.estado == "cancelado", 
                                                   models.Turno.fecha >= seisMesesAtras).count()
    if (cantCancelados >= 5):
        persona = db.query(models.Persona).filter(models.Persona.id == turno.persona_id).first()
        persona.habilitado = False
        return None, "La persona no esta habilitada a sacar un turno"

    nuevo_turno = models.Turno(**turno.dict())
    
    db.add(nuevo_turno)
    db.commit()
    db.refresh(nuevo_turno)

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
    
    return turno_dict, None



