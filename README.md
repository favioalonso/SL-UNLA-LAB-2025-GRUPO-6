# CRUD de Personas - SL-UNLA-LAB-2025-GRUPO-6

Este proyecto es una API REST desarrollada en Python con FastAPI y SQLAlchemy para la gestión de personas. Permite crear, leer, actualizar y eliminar registros de personas en una base de datos SQLite.

![Vista previa del CRUD](abm_personas2.gif)

## Características

- API RESTful para operaciones CRUD sobre personas.
- Validación de datos con Pydantic.
- Base de datos SQLite.
- Cálculo automático de la edad.
- Código modular y fácil de mantener.

## Requisitos

- Python 3.10 o superior
- pip

## Instalación

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/tu-usuario/SL-UNLA-LAB-2025-GRUPO-6.git
   cd SL-UNLA-LAB-2025-GRUPO-6
   ```

2. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   ```

## Uso

1. **Inicia el servidor:**
   ```sh
   uvicorn main:app --reload
   ```

2. **Accede a la documentación interactiva:**
   - Abre [http://localhost:8000/docs](http://localhost:8000/docs) en tu navegador.

## Endpoints principales

- `POST /personas` : Crear una nueva persona.
- `GET /personas` : Listar todas las personas.
- `GET /personas/{persona_id}` : Obtener una persona por ID.
- `PUT /personas/{persona_id}` : Actualizar una persona.
- `DELETE /personas/{persona_id}` : Eliminar una persona.

## Estructura del proyecto

```
├── main.py         # Punto de entrada de la API
├── models.py       # Definición de modelos SQLAlchemy
├── schemas.py      # Esquemas Pydantic
├── crud.py         # Funciones CRUD
├── database.py     # Configuración de la base de datos
├── requirements.txt
├── README.md
└── abm_personas2.gif
```

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

---

Desarrollado por estudiantes de la Universidad de Lanús para Seminario de Lenguajes

