from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models, schemas, crud, schemasTurno, crudTurno
from database import SessionLocal, engine, Base #Usamos Base??
from datetime import date

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
    
@app.delete("/turnos/{turno_id}", response_model=schemasTurno.MensajeResponse)
def delete_turno(turno_id: int, db: Session = Depends(get_db)):
    db_turno = crudTurno.delete_turno(turno_id, db)
    if not db_turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return {"mensaje": "El turno ha sido eliminado exitosamente"}

@app.get("/turnos/turnos-disponibles", response_model=schemasTurno.HorariosResponse)
def get_turnos_disponibles(fecha:date, db: Session = Depends(get_db)):
    try:
        lista_disponibles = crudTurno.get_turnos_disponibles(fecha, db)
        if not lista_disponibles:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No hay horarios disponibles para la fecha {fecha}")
        return schemasTurno.HorariosResponse(fecha=fecha,horarios_disponibles=lista_disponibles)
    except Exception as e:
       raise HTTPException(status_shcode=status.HTTP_500_INTERNAL_SERVER_ERROR,detail=f"Error al obtener los turnos disponbiles: {e}")