from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func, desc, asc
import models.models as models, schemas.schemas as schemas
import math
from datetime import date
import pandas as pd
from io import StringIO



def calcular_edad(fecha_nacimiento):
    try:
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


def get_personas_filtered(
    db: Session,
    filters: schemas.PersonaFilter,
    page: int = 1,
    per_page: int = 10
):
    try:
        # Query base
        query = db.query(models.Persona)

        # Aplicar filtros
        if filters.nombre:
            query = query.filter(models.Persona.nombre.ilike(f"%{filters.nombre}%"))

        if filters.email:
            query = query.filter(models.Persona.email.ilike(f"%{filters.email}%"))

        # Filtros por edad (requiere cálculo)
        if filters.edad_min is not None or filters.edad_max is not None:
            today = date.today()

            if filters.edad_min is not None:
                # Fecha máxima para edad mínima
                max_birth_date = date(today.year - filters.edad_min, today.month, today.day)
                query = query.filter(models.Persona.fecha_nacimiento <= max_birth_date)

            if filters.edad_max is not None:
                # Fecha mínima para edad máxima
                min_birth_date = date(today.year - filters.edad_max - 1, today.month, today.day)
                query = query.filter(models.Persona.fecha_nacimiento > min_birth_date)

        # Contar total antes de aplicar paginación
        total = query.count()

        # Aplicar ordenamiento
        if filters.order_by == 'nombre':
            order_column = models.Persona.nombre
        elif filters.order_by == 'email':
            order_column = models.Persona.email
        elif filters.order_by == 'fecha_nacimiento':
            order_column = models.Persona.fecha_nacimiento
        elif filters.order_by == 'edad':
            # Para ordenar por edad, ordenamos por fecha de nacimiento en orden inverso
            order_column = models.Persona.fecha_nacimiento
            filters.order = 'desc' if filters.order == 'asc' else 'asc'
        else:
            order_column = models.Persona.id

        if filters.order == 'desc':
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(asc(order_column))

        # Aplicar paginación
        offset = (page - 1) * per_page
        personas = query.offset(offset).limit(per_page).all()

        # Convertir a schemas con edad calculada
        result_items = []
        for persona in personas:
            persona_dict = persona.__dict__.copy()
            persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
            result_items.append(schemas.PersonaOut(**persona_dict))

        # Calcular metadata de paginación
        total_pages = math.ceil(total / per_page)
        metadata = schemas.PaginationMetadata(
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )

        return schemas.PaginatedPersonaResponse(
            items=result_items,
            metadata=metadata
        )

    except SQLAlchemyError as e:
        raise Exception(f"Error al consultar personas filtradas: {e}")
    except ValueError as e:
        raise Exception(f"Error en filtros de búsqueda: {e}")

def get_personas_habilitadas_o_deshabilitadas(estado: bool, db: Session):
    """
        Consulta a las personas según el estado "True" o "False"
        Retorna las personas que tienen el estado elegido
    """

    #Consulta filtrada por estado
    personas = db.query(models.Persona).filter(
        models.Persona.habilitado == estado
    ).all()

     # Convertir a schemas con edad calculada
    personas_filtradas = []
    for persona in personas:
        persona_dict = persona.__dict__.copy()
        persona_dict['edad'] = calcular_edad(persona.fecha_nacimiento)
        personas_filtradas.append(schemas.PersonaOut(**persona_dict))

    return personas_filtradas

def generar_csv_estado_personas(db: Session, estado: bool):
    try:
        # Llamar al CRUD existente
        personas = get_personas_habilitadas_o_deshabilitadas(estado, db)

        if not personas:
            return None   # Para que el endpoint devuelva 204

        filas_para_df = []
        for p in personas:
            filas_para_df.append({
                "id": p.id,
                "nombre": p.nombre,
                "email": p.email,
                "dni": p.dni,
                "telefono": p.telefono,
                "fecha_nacimiento": p.fecha_nacimiento.strftime("%Y-%m-%d"),
                "habilitado": p.habilitado,
                "edad": p.edad
            })

        # Crear DataFrame
        df = pd.DataFrame(filas_para_df)

        df["telefono"] = df["telefono"].astype(str).apply(lambda x: f"'{x}")#cambio el tipo de dato a string, y uso esa funcion lambda para poner una ' adelante de todos lo numeros, asi lo interpreta como string y muestra el numero completo
        df["habilitado"] = df["habilitado"].map({True: "Si", False: "No"})#Reformo el estado habilitado para que se muestre si o no, para visualizar mas facil en el archivo csv.

        df.sort_values(by=["id"], inplace=True)#ordeno el df por los id de las personas
        
        # CSV en memoria
        csv_buffer = StringIO()#Se crea un buffer, un archivo en memoria que se puede enviar con fastapi para descargarlo
        df.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")#Gnero el archivo csv desde el DataFrame y lo guardo en el buffer
        csv_buffer.seek(0)

        return csv_buffer
    except Exception as e:
        raise Exception(f"Error inesperado al generar CSV de estado de personas: {e}")