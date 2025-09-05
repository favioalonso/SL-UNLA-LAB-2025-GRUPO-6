from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
# Crear motor de base de datos SQLite
engine = create_engine('sqlite:///mi_base.db', echo=True)


# Declarar la base
Base = declarative_base()

# Crear una clase que representa una tabla
class Persona(Base):
    __tablename__ = 'personas'
    id = Column(Integer, primary_key=True)
    nombre = Column(String)
    edad = Column(Integer)



# Crear las tablas en el archivo si no existen
Base.metadata.create_all(engine)

# Crear una sesión para interactuar con la base
Session = sessionmaker(bind=engine)
session = Session()

# Agregar una persona
nueva_persona = Persona(nombre="Carlos", edad=40)
session.add(nueva_persona)
session.commit()

# Consultar personas
for persona in session.query(Persona).all():
     print(persona.nombre, persona.edad)
