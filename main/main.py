from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from functools import lru_cache


# Imports
import models.models as models
import schemas.schemas as schemas
import schemas.schemasTurno as schemasTurno
import crud.crud as crud
import crud.crudTurno as crudTurno
from database.database import SessionLocal, engine
from crud.crudTurno import DatabaseResourceNotFound

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

#-------------------------------------------------------------------------------------------------------------------------------
#Se utiliza el decorador 'lru_cache' para no leer repetidamente el archivo .env
@lru_cache
def cargar_variables_entorno():
    return schemasTurno.ConfHorarios()
#Cada vez que se llame a cargar_configuracion() se retorna lo guardado en el caché
#-------------------------------------------------------------------------------------------------------------------------------


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

# ============ ENDPOINTS DE PERSONAS ============
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

# ============ ENDPOINTS DE TURNOS ============
@app.get("/turnos", response_model=list[schemasTurno.TurnoOut])
def get_turnos(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    try:
        turnos_db = crudTurno.get_turnos(db, skip, limit)
        return turnos_db
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

@app.post("/turnos", response_model=schemasTurno.TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(turno: schemasTurno.TurnoCreate, db: Session = Depends(get_db)):
    try:
        return crudTurno.create_turnos(db, turno)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except DatabaseResourceNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

@app.delete("/turnos/{turno_id}", response_model=schemasTurno.MensajeResponse)
def delete_turno(turno_id: int, db: Session = Depends(get_db)):
    db_turno = crudTurno.delete_turno(turno_id, db)
    if not db_turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"mensaje": "El turno ha sido eliminado exitosamente"}

@app.get("/turnos/turnos-disponibles", response_model=schemasTurno.HorariosResponse)
def get_turnos_disponibles(fecha: date, db: Session = Depends(get_db)):
    try:
        if fecha.weekday() == 6: 
            return "No se atiende los días domingos, por favor ingresar una fecha de lunes a sábados"
        lista_disponibles = crudTurno.get_turnos_disponibles(fecha, db)
        if not lista_disponibles:
            raise HTTPException(status_code=404, detail=f"No hay horarios disponibles para la fecha {fecha}")
        
        return schemasTurno.HorariosResponse(fecha=fecha, horarios_disponibles=lista_disponibles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener los turnos disponibles: {e}")


@app.get("/turnos/{turno_id}", response_model=schemasTurno.TurnoOut)
def get_turno_id(turno_id: int, db: Session = Depends(get_db)):
    try:
        turno = crudTurno.get_turno(db, turno_id)
        if turno is None:
            raise ValueError("Turno no encontrado")
        return turno
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Dato invalido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

@app.put("/turnos/{turno_id}", response_model=schemasTurno.TurnoOut)
def put_turno_id(turno_id: int, turno_update: schemasTurno.TurnoUpdate, db: Session = Depends(get_db)):
    try:
        updated = crudTurno.update_turno(db, turno_id, turno_update)
        if updated is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")
        return updated
    except HTTPException:
        raise
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos invalidos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")