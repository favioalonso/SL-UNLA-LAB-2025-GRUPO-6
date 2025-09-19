from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
import models.models as models, schemas.schemas as schemas, crud.crud as crud
from database.database import SessionLocal, engine, Base
from crudTurno import DatabaseResourceNotFound

# Crea las tablas en la base de datos (si no existen)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Función para crear datos de prueba
def create_sample_data():
    db = SessionLocal()
    try:
        # Verificar si ya existen datos
        if db.query(models.Persona).count() > 0:
            return  # Ya hay datos, no crear más

        # Datos de prueba
        sample_personas = [
            {
                "nombre": "Juan Pérez",
                "email": "juan@gmail.com",
                "dni": "12345678",
                "telefono": "1123456789",
                "fecha_nacimiento": "1990-05-15"
            },
            {
                "nombre": "María García",
                "email": "maria@hotmail.com",
                "dni": "87654321",
                "telefono": "01134567890",
                "fecha_nacimiento": "1985-08-20"
            },
            {
                "nombre": "Carlos Rodriguez",
                "email": "carlos@yahoo.com",
                "dni": "11223344",
                "telefono": "+5411987654321",
                "fecha_nacimiento": "1995-12-10"
            }
        ]

        # Crear las personas de prueba
        for persona_data in sample_personas:
            from datetime import datetime
            fecha_obj = datetime.strptime(persona_data["fecha_nacimiento"], "%Y-%m-%d").date()

            db_persona = models.Persona(
                nombre=persona_data["nombre"],
                email=persona_data["email"],
                dni=persona_data["dni"],
                telefono=persona_data["telefono"],
                fecha_nacimiento=fecha_obj,
                habilitado=True
            )
            db.add(db_persona)

        db.commit()
        print("✅ Datos de prueba creados exitosamente")

    except Exception as e:
        print(f"❌ Error al crear datos de prueba: {e}")
        db.rollback()
    finally:
        db.close()

# Crear datos de prueba al iniciar la aplicación
create_sample_data()

# Dependencia para obtener la sesión de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/personas", response_model=schemas.PersonaOut)
def create_persona(persona: schemas.PersonaCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_persona(db, persona)
    except Exception as e:
        error_message = str(e)
        if "email ya existe" in error_message:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        elif "DNI ya existe" in error_message:
            raise HTTPException(status_code=400, detail="El DNI ya está registrado")
        else:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor: {error_message}")


@app.get("/personas", response_model=list[schemas.PersonaOut])
def read_personas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        if skip < 0 or limit < 0:
            raise HTTPException(status_code=400, detail="Los parámetros skip y limit deben ser positivos")
        return crud.get_personas(db, skip=skip, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.get("/personas/search", response_model=schemas.PaginatedPersonaResponse)
def search_personas(
    nombre: Optional[str] = Query(None, description="Buscar por nombre (búsqueda parcial)"),
    email: Optional[str] = Query(None, description="Buscar por email (búsqueda parcial)"),
    edad_min: Optional[int] = Query(None, ge=0, le=150, description="Edad mínima"),
    edad_max: Optional[int] = Query(None, ge=0, le=150, description="Edad máxima"),
    order_by: Optional[str] = Query("id", description="Campo para ordenar: id, nombre, edad, fecha_nacimiento, email"),
    order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Elementos por página"),
    db: Session = Depends(get_db)
):
    try:
        # Validar que edad_min <= edad_max
        if edad_min is not None and edad_max is not None and edad_min > edad_max:
            raise HTTPException(status_code=400, detail="edad_min no puede ser mayor que edad_max")

        # Crear filtros
        filters = schemas.PersonaFilter(
            nombre=nombre,
            email=email,
            edad_min=edad_min,
            edad_max=edad_max,
            order_by=order_by,
            order=order
        )

        return crud.get_personas_filtered(db, filters, page, per_page)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def read_persona(persona_id: int, db: Session = Depends(get_db)):
    try:
        if persona_id <= 0:
            raise HTTPException(status_code=400, detail="El ID debe ser un número positivo")
        db_persona = crud.get_persona(db, persona_id)
        if db_persona is None:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return db_persona
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.put("/personas/{persona_id}", response_model=schemas.PersonaOut)
def update_persona(persona_id: int, persona: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    try:
        if persona_id <= 0:
            raise HTTPException(status_code=400, detail="El ID debe ser un número positivo")
        db_persona = crud.update_persona(db, persona_id, persona)
        if db_persona is None:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return db_persona
    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        if "email ya existe" in error_message:
            raise HTTPException(status_code=400, detail="El email ya está registrado")
        elif "DNI ya existe" in error_message:
            raise HTTPException(status_code=400, detail="El DNI ya está registrado")
        else:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor: {error_message}")


@app.delete("/personas/{persona_id}", response_model=schemas.PersonaOut)
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    try:
        if persona_id <= 0:
            raise HTTPException(status_code=400, detail="El ID debe ser un número positivo")
        db_persona = crud.delete_persona(db, persona_id)
        if db_persona is None:
            raise HTTPException(status_code=404, detail="Persona no encontrada")
        return db_persona
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@app.post("/turnos",response_model= schemasTurno.TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(turno: schemasTurno.TurnoCreate, db: Session = Depends(get_db)):
    try:
        return crudTurno.create_turnos(db,turno)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except PermissionError as e:
        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail=str(e))
    
    except DatabaseResourceNotFound as e:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail=str(e))
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

@app.get("/turnos", response_model=list[schemasTurno.TurnoOut])
def get_turnos(db: Session = Depends(get_db), skip:int = 0, limit:int = 100):
    try:

        turnos_db = crudTurno.get_turnos(db, skip, limit)
        if not turnos_db:
            raise HTTPException(status_code= status.HTTP_204_NO_CONTENT)
        return turnos_db
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )
