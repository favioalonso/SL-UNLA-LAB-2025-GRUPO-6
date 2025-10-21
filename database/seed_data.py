from datetime import datetime, date, time
import models.models as models
from database.database import SessionLocal
from schemas.schemasTurno import settings


def create_sample_data():
    """
    Función para crear datos de prueba en la base de datos.
    Se ejecuta al iniciar la aplicación si no existen datos previos.
    """
    db = SessionLocal()
    try:
        # Verificar si ya existen datos
        if db.query(models.Persona).count() > 0:
            return  # Ya hay datos, no crear más

        # Obtener estados del .env
        diccionario_estados = settings.estados_posibles

        # Datos de prueba - Personas
        sample_personas = [
            {
                "nombre": "Juan Pérez",
                "email": "juan@gmail.com",
                "dni": "12345678",
                "telefono": "1123456789",
                "fecha_nacimiento": "1990-05-15",
                "habilitado": True
            },
            {
                "nombre": "María García",
                "email": "maria@hotmail.com",
                "dni": "87654321",
                "telefono": "01134567890",
                "fecha_nacimiento": "1985-08-20",
                "habilitado": True
            },
            {
                "nombre": "Carlos Rodriguez",
                "email": "carlos@yahoo.com",
                "dni": "11223344",
                "telefono": "+5411987654321",
                "fecha_nacimiento": "1995-12-10",
                "habilitado": True
            },
            {
                "nombre": "Ana Martinez",
                "email": "ana.martinez@outlook.com",
                "dni": "22334455",
                "telefono": "1145678901",
                "fecha_nacimiento": "1992-03-25",
                "habilitado": True
            },
            {
                "nombre": "Roberto López",
                "email": "roberto.lopez@gmail.com",
                "dni": "33445566",
                "telefono": "1156789012",
                "fecha_nacimiento": "1978-11-30",
                "habilitado": True
            },
            {
                "nombre": "Laura Fernández",
                "email": "laura.f@hotmail.com",
                "dni": "44556677",
                "telefono": "1167890123",
                "fecha_nacimiento": "2000-07-18",
                "habilitado": False  # Deshabilitada por turnos cancelados
            },
            {
                "nombre": "Diego Sanchez",
                "email": "diego.sanchez@yahoo.com",
                "dni": "55667788",
                "telefono": "1178901234",
                "fecha_nacimiento": "1988-09-05",
                "habilitado": True
            }
        ]

        # Crear las personas de prueba
        personas_creadas = []
        for persona_data in sample_personas:
            fecha_obj = datetime.strptime(persona_data["fecha_nacimiento"], "%Y-%m-%d").date()

            db_persona = models.Persona(
                nombre=persona_data["nombre"],
                email=persona_data["email"],
                dni=persona_data["dni"],
                telefono=persona_data["telefono"],
                fecha_nacimiento=fecha_obj,
                habilitado=persona_data["habilitado"]
            )
            db.add(db_persona)
            personas_creadas.append(db_persona)

        db.commit()
        db.refresh(personas_creadas[0])  # Refrescar para obtener IDs

        # Datos de prueba - Turnos (ampliados con casos de múltiples turnos mismo día)
        sample_turnos = [
            # ===== CASOS DE MÚLTIPLES TURNOS EL MISMO DÍA =====
            # Juan Pérez (persona_id 1) - 2 turnos el 2025-11-22
            {"persona_id": 1, "fecha": "2025-11-22", "hora": "09:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 1, "fecha": "2025-11-22", "hora": "14:30:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},

            # María García (persona_id 2) - 2 turnos el 2025-11-23
            {"persona_id": 2, "fecha": "2025-11-23", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 2, "fecha": "2025-11-23", "hora": "15:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},

            # Carlos Rodriguez (persona_id 3) - 2 turnos el 2025-11-24
            {"persona_id": 3, "fecha": "2025-11-24", "hora": "11:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 3, "fecha": "2025-11-24", "hora": "16:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},

            # ===== JUAN PÉREZ (persona_id 1) - Múltiples turnos en diferentes fechas =====
            {"persona_id": 1, "fecha": "2025-09-25", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 1, "fecha": "2025-09-26", "hora": "11:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 1, "fecha": "2025-10-15", "hora": "09:30:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 1, "fecha": "2025-11-05", "hora": "13:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 1, "fecha": "2025-11-15", "hora": "14:30:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 1, "fecha": "2025-12-10", "hora": "10:30:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 1, "fecha": "2025-12-20", "hora": "15:30:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},

            # ===== MARÍA GARCÍA (persona_id 2) - Múltiples turnos =====
            {"persona_id": 2, "fecha": "2025-09-19", "hora": "15:30:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 2, "fecha": "2025-10-12", "hora": "11:30:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 2, "fecha": "2025-11-16", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 2, "fecha": "2025-12-05", "hora": "14:00:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 2, "fecha": "2025-12-16", "hora": "11:00:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 2, "fecha": "2025-10-25", "hora": "10:30:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},

            # ===== CARLOS RODRIGUEZ (persona_id 3) - Múltiples turnos =====
            {"persona_id": 3, "fecha": "2025-09-20", "hora": "09:30:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 3, "fecha": "2025-10-08", "hora": "12:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 3, "fecha": "2025-11-17", "hora": "11:30:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 3, "fecha": "2025-11-20", "hora": "09:30:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 3, "fecha": "2025-12-18", "hora": "13:30:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},

            # ===== ANA MARTINEZ (persona_id 4) - Varios turnos =====
            {"persona_id": 4, "fecha": "2025-10-22", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 4, "fecha": "2025-11-18", "hora": "15:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 4, "fecha": "2025-11-21", "hora": "14:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 4, "fecha": "2025-12-12", "hora": "09:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},

            # ===== ROBERTO LÓPEZ (persona_id 5) - Varios turnos con cancelados =====
            {"persona_id": 5, "fecha": "2025-09-18", "hora": "16:00:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 5, "fecha": "2025-10-28", "hora": "11:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 5, "fecha": "2025-11-19", "hora": "09:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 5, "fecha": "2025-11-30", "hora": "15:30:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 5, "fecha": "2025-12-08", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 5, "fecha": "2025-12-15", "hora": "13:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 5, "fecha": "2025-12-22", "hora": "14:30:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},

            # ===== LAURA FERNÁNDEZ (persona_id 6) - 6 turnos cancelados (deshabilitada) =====
            {"persona_id": 6, "fecha": "2025-09-10", "hora": "10:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 6, "fecha": "2025-09-15", "hora": "11:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 6, "fecha": "2025-10-05", "hora": "12:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 6, "fecha": "2025-10-10", "hora": "13:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 6, "fecha": "2025-10-15", "hora": "14:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},
            {"persona_id": 6, "fecha": "2025-10-20", "hora": "15:00:00", "estado": diccionario_estados.get('ESTADO_CANCELADO')},

            # ===== DIEGO SANCHEZ (persona_id 7) - Variedad de estados =====
            {"persona_id": 7, "fecha": "2025-09-20", "hora": "09:30:00", "estado": diccionario_estados.get('ESTADO_ASISTIDO')},
            {"persona_id": 7, "fecha": "2025-10-18", "hora": "14:00:00", "estado": diccionario_estados.get('ESTADO_CONFIRMADO')},
            {"persona_id": 7, "fecha": "2025-11-25", "hora": "10:30:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
            {"persona_id": 7, "fecha": "2025-12-28", "hora": "16:00:00", "estado": diccionario_estados.get('ESTADO_PENDIENTE')},
        ]

        # Crear los turnos de prueba
        for turno_data in sample_turnos:
            fecha_obj = datetime.strptime(turno_data["fecha"], "%Y-%m-%d").date()
            hora_obj = datetime.strptime(turno_data["hora"], "%H:%M:%S").time()

            db_turno = models.Turno(
                persona_id=turno_data["persona_id"],
                fecha=fecha_obj,
                hora=hora_obj,
                estado=turno_data["estado"]
            )
            db.add(db_turno)

        db.commit()
        print("[OK] Datos de prueba creados exitosamente")
        print(f"   - {len(sample_personas)} personas creadas")
        print(f"   - {len(sample_turnos)} turnos creados")
        print(f"   - Estados: Pendientes, Confirmados, Cancelados, Asistidos")

    except Exception as e:
        print(f"[ERROR] Error al crear datos de prueba: {e}")
        db.rollback()
    finally:
        db.close()