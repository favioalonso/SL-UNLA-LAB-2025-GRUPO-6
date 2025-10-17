from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime


# Imports
import models.models as models
import schemas.schemas as schemas
import schemas.schemasTurno as schemasTurno
import crud.crud as crud
import crud.crudTurno as crudTurno
from database.database import SessionLocal, engine
from database.seed_data import create_sample_data
from crud.crudTurno import DatabaseResourceNotFound

# Crear tablas
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    try:
        if turno_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ID debe ser un número positivo")

        db_turno = crudTurno.delete_turno(turno_id, db)
        if not db_turno:
            raise HTTPException(status_code=404, detail="Turno no encontrado")
        return {"mensaje": "El turno ha sido eliminado exitosamente"}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

@app.get("/turnos/turnos-disponibles", response_model=schemasTurno.HorariosResponse)
def get_turnos_disponibles(fecha: date, db: Session = Depends(get_db)):

    if fecha.weekday() == 6: 
            raise HTTPException(status_code=404, detail="No se atiende los días domingos, por favor ingresar una fecha de lunes a sábado")
    try: 
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

@app.put("/turnos/{turno_id}/cancelar", response_model=schemasTurno.TurnoOut)
def cancelar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        if turno_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ID debe ser un número positivo")

        turno_cancelado = crudTurno.cancelar_turno(db, turno_id)
        if turno_cancelado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

        return turno_cancelado
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

@app.put("/turnos/{turno_id}/confirmar", response_model=schemasTurno.TurnoOut)
def confirmar_turno(turno_id: int, db: Session = Depends(get_db)):
    try:
        if turno_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El ID debe ser un número positivo")

        turno_confirmado = crudTurno.confirmar_turno(db, turno_id)
        if turno_confirmado is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turno no encontrado")

        return turno_confirmado
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")

# ============ ENDPOINTS DE REPORTES ============

@app.get("/reportes/turnos-por-persona", response_model= list[schemasTurno.TurnoOut])
def get_turnos_por_persona(dni: str = Query(
        description="DNI de la persona(8 digitos)",
        min_length=8,
        max_length=8,
        regex=r"\d{8}"  #\d: tiene que ser numerico - {8}: ocho digitos  
        #regex: patron de busqueda, le digo que restricciones tiene que tener el dni (r: para que no interprete como barra invertida el \d)
        #Defino el formato del dni con sus validaciones
    ),
    db: Session = Depends(get_db)):
    try:
        turnos = crudTurno.get_turnos_por_dni(db, dni)
        if turnos is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontró una persona con el DNI {dni}")

        #Persona con dni existente pero sin turnos
        if not turnos:
            raise HTTPException(status_code=404, detail=f"La persona con DNI {dni} existe pero no tiene turnos registrados.")
        
        return turnos

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")
    

@app.get("/reportes/turnos-cancelados", response_model=list[schemasTurno.PersonaConTurnosCancelados])
def get_reporte_turnos_cancelados(
    #Parametro de entrada, por defecto esta en 5
    min: int = Query(5, description="Número mínimo de turnos cancelados para incluir a una persona", ge=5), #ge: greater than or equal to, mayor o igual que 5
    db:Session = Depends(get_db)
):
    
    try:
        reporte_personas= crudTurno.get_personas_turnos_cancelados(db, min_cancelados= min) #busqueda y entrega de resultados
        if not reporte_personas:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se encontraron personas con {min} o mas turnos cancelados")
        return reporte_personas
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error inesperado: {str(e)}")


@app.get("/reportes/turnos-por-fecha", status_code=status.HTTP_200_OK)
def get_turnos_por_fecha(
    fecha: str = Query(...,
        description="Fecha del día en formato YYYY-MM-DD",
        example="2025-10-05"
    ), db: Session = Depends(get_db)):

    try:
        fecha_valida = datetime.strptime(fecha, "%Y-%m-%d").date()#Paso el formato de string de la fecha de entrada a tipo datetime
                                                                  #y si el formato no es correcto me genera un ValueError  
        turnos = crudTurno.get_turnos_por_fecha(db, fecha_valida)
        if not turnos:
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
        return {"fecha": fecha, "turnos": turnos}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido o fecha inexistente. Use el formato YYYY-MM-DD."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.get("/reportes/turnos-cancelados-por-mes", status_code=status.HTTP_200_OK)
def get_turnos_cancelados_mes_actual(db: Session = Depends(get_db)):
    try:
        turnos = crudTurno.get_turnos_cancelados_mes_actual(db)
        if not turnos:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No hay turnos cancelados en el mes actual."
            )
        return turnos
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el reporte: {str(e)}"
        )
