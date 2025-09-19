from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models.models as models, schemas.schemas as schemas, crud.crud as crud
from database.database import SessionLocal, engine, Base

# Crea las tablas en la base de datos (si no existen)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

