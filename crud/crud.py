from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import models.models as models, schemas.schemas as schemas


def calcular_edad(fecha_nacimiento):
    try:
        from datetime import date
        if not fecha_nacimiento:
            raise ValueError("Fecha de nacimiento no puede ser None")
        hoy = date.today()
        return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    except (TypeError, AttributeError) as e:
        raise ValueError(f"Fecha de nacimiento inválida: {e}")

def get_persona(db: Session, persona_id: int):
    try:
        persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
        if persona:
            persona_dict = persona.__dict__.copy()
            persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
            return schemas.PersonaOut(**persona_dict)
        return None
    except SQLAlchemyError as e:
        raise Exception(f"Error al consultar persona: {e}")
    except ValueError as e:
        raise Exception(f"Error en datos de persona: {e}")


def get_personas(db: Session, skip: int = 0, limit: int = 100):
    try:
        personas = db.query(models.Persona).offset(skip).limit(limit).all()
        result = []
        for persona in personas:
            persona_dict = persona.__dict__.copy()
            persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
            result.append(schemas.PersonaOut(**persona_dict))
        return result
    except SQLAlchemyError as e:
        raise Exception(f"Error al consultar personas: {e}")
    except ValueError as e:
        raise Exception(f"Error en datos de personas: {e}")


def create_persona(db: Session, persona: schemas.PersonaCreate):
    try:
        db_persona = models.Persona(**persona.dict())
        db.add(db_persona)
        db.commit()
        db.refresh(db_persona)
        persona_dict = db_persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(db_persona.fecha_nacimiento)
        return schemas.PersonaOut(**persona_dict)
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            raise Exception("El email ya existe en el sistema")
        elif "dni" in str(e.orig):
            raise Exception("El DNI ya existe en el sistema")
        else:
            raise Exception(f"Error de integridad en datos: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al crear persona: {e}")
    except ValueError as e:
        raise Exception(f"Error en datos de persona: {e}")


def update_persona(db: Session, persona_id: int, persona: schemas.PersonaUpdate):
    try:
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
    except IntegrityError as e:
        db.rollback()
        if "email" in str(e.orig):
            raise Exception("El email ya existe en el sistema")
        elif "dni" in str(e.orig):
            raise Exception("El DNI ya existe en el sistema")
        else:
            raise Exception(f"Error de integridad en datos: {e}")
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al actualizar persona: {e}")
    except ValueError as e:
        raise Exception(f"Error en datos de persona: {e}")


def delete_persona(db: Session, persona_id: int):
    try:
        db_persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
        if db_persona:
            persona_dict = db_persona.__dict__.copy()
            persona_dict['edad'] = calcular_edad(db_persona.fecha_nacimiento)
            db.delete(db_persona)
            db.commit()
            return schemas.PersonaOut(**persona_dict)
        return None
    except SQLAlchemyError as e:
        db.rollback()
        raise Exception(f"Error al eliminar persona: {e}")
    except ValueError as e:
        raise Exception(f"Error en datos de persona: {e}")
