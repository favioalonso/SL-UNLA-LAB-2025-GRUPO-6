from datetime import datetime
import models.models as models
from database.database import SessionLocal


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