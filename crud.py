from sqlalchemy.orm import Session
import models, schemas


def calcular_edad(fecha_nacimiento):
    from datetime import date
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))

def get_persona(db: Session, persona_id: int):
    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if persona:
        persona_dict = persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
        return schemas.PersonaOut(**persona_dict)
    return None


def get_personas(db: Session, skip: int = 0, limit: int = 100):
    personas = db.query(models.Persona).offset(skip).limit(limit).all()
    result = []
    for persona in personas:
        persona_dict = persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
        result.append(schemas.PersonaOut(**persona_dict))
    return result


def create_persona(db: Session, persona: schemas.PersonaCreate):
    db_persona = models.Persona(**persona.dict())
    db.add(db_persona)
    db.commit()
    db.refresh(db_persona)
    persona_dict = db_persona.__dict__.copy()
    persona_dict['edad'] = calcular_edad(db_persona.fecha_nacimiento)
    return schemas.PersonaOut(**persona_dict)


def update_persona(db: Session, persona_id: int, persona: schemas.PersonaUpdate):
    db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if db_persona:
        for key, value in persona.dict().items():
            setattr(db_persona, key, value)
        db.commit()
        db.refresh(db_persona)
        persona_dict = db_persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(db_persona.fecha_nacimiento)
        return schemas.PersonaOut(**persona_dict)
    return None


def delete_persona(db: Session, persona_id: int):
    db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if db_persona:
        persona_dict = db_persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(db_persona.fecha_nacimiento)
        db.delete(db_persona)
        db.commit()
        return schemas.PersonaOut(**persona_dict)
    return None
