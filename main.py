from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, crud, schemasTurno, crudTurno
from database import SessionLocal, engine, Base

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
    return crud.create_persona(db, persona)


@app.get("/personas", response_model=list[schemas.PersonaOut])
def read_personas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_personas(db, skip=skip, limit=limit)


@app.get("/personas/{persona_id}", response_model=schemas.PersonaOut)
def read_persona(persona_id: int, db: Session = Depends(get_db)):
    db_persona = crud.get_persona(db, persona_id)
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return db_persona


@app.put("/personas/{persona_id}", response_model=schemas.PersonaOut)
def update_persona(persona_id: int, persona: schemas.PersonaUpdate, db: Session = Depends(get_db)):
    db_persona = crud.update_persona(db, persona_id, persona)
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return db_persona


@app.delete("/personas/{persona_id}", response_model=schemas.PersonaOut)
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    db_persona = crud.delete_persona(db, persona_id)
    if db_persona is None:
        raise HTTPException(status_code=404, detail="Persona no encontrada")
    return db_persona

@app.post("/turnos",response_model= schemasTurno.TurnoOut, status_code=status.HTTP_201_CREATED)
def crear_turno(turno: schemasTurno.TurnoCreate, db: Session = Depends(get_db)):
    try:
        return crudTurno.create_turnos(db,turno)
    
    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except PermissionError as e:

        raise HTTPException(status_code= status.HTTP_403_FORBIDDEN, detail=str(e))
    
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
        return crudTurno.get_turnos(db, skip, limit)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado: {str(e)}"
        )

@app.get("/turnos/{turno_id}", response_model=schemasTurno.TurnoOut)
def get_turno_id(turno_id: int, db: Session = Depends(get_db)):
    try:
        turno = crudTurno.get_turno(db, turno_id)

        if turno is None:
            raise ValueError("Turno no encontrado")
        return turno
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) #Turno no encontrado
    
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Dato invalido: {str(e)}") #No es del tipo int el id
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

@app.put("/turnos/{turno_id}", response_model=schemasTurno.TurnoOut)
def put_turno_id(turno_id: int, turno_update: schemasTurno.TurnoUpdate, db: Session = Depends(get_db)):
    try:
        updated = crudTurno.update_turno(db, turno_id, turno_update)

        if updated is None:
            #Si CRUD devuelve NONE, no encontrado
            raise HTTPException(status_code= status.HTTP_404_NOT_FOUND, detail= "Turno no encontrado")
        
        return updated
    
    except HTTPException:
        raise

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail= str(e)) #No tiene permiso 
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= str(e)) #Error al validar los datos
    
    except TypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Datos invalidos: {str(e)}")
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail= f"Error inesperado: {str(e)}")