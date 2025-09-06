from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, crud
from database import SessionLocal, engine, Base

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
