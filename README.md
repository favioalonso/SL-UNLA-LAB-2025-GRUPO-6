# CRUD de Personas y Turnos - SL-UNLA-LAB-2025-GRUPO-6

Este proyecto es una API REST desarrollada en Python con FastAPI y SQLAlchemy para la gestión de personas y turnos. Permite crear, leer, actualizar y eliminar registros de personas y turnos en una base de datos SQLite con arquitectura modular y validaciones robustas.

![Vista previa del CRUD](abm_personas2.gif)

## Características

- **API RESTful completa** para operaciones CRUD sobre personas y turnos
- **Validación de datos** con Pydantic v2 y manejo de errores robusto
- **Base de datos SQLite** con SQLAlchemy ORM y relaciones
- **Cálculo automático de edad** basado en fecha de nacimiento
- **Sistema de turnos** con validaciones de horarios y disponibilidad
- **Búsqueda avanzada** con filtros y paginación
- **Datos de prueba automáticos** al iniciar la aplicación
- **Documentación interactiva** con Swagger UI
- **Arquitectura modular** con separación clara de responsabilidades

## Tecnologías

- **FastAPI** v0.115.2 - Framework web moderno y rápido
- **SQLAlchemy** v2.0.36 - ORM para Python
- **Pydantic** v2.9.2 - Validación de datos y serialización
- **Uvicorn** v0.30.6 - Servidor ASGI
- **SQLite** - Base de datos embebida

## Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

## Instalación

1. **Clona el repositorio:**
   ```sh
   git clone https://github.com/favioalonso/SL-UNLA-LAB-2025-GRUPO-6.git
   cd SL-UNLA-LAB-2025-GRUPO-6
   ```

2. **Crea y activa un entorno virtual:**
   ```sh
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instala las dependencias:**
   ```sh
   pip install -r requirements.txt
   ```

## Uso

1. **Inicia el servidor:**
   ```sh
   uvicorn main.main:app --reload
   ```

2. **Accede a la documentación interactiva:**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Endpoints API

### 📋 Personas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/personas` | Crear una nueva persona |
| `GET` | `/personas` | Listar todas las personas (con paginación) |
| `GET` | `/personas/search` | Búsqueda avanzada con filtros |
| `GET` | `/personas/{persona_id}` | Obtener una persona por ID |
| `PUT` | `/personas/{persona_id}` | Actualizar una persona |
| `DELETE` | `/personas/{persona_id}` | Eliminar una persona |

### 🗓️ Turnos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/turnos` | Crear un nuevo turno |
| `GET` | `/turnos` | Listar todos los turnos (con paginación) |
| `GET` | `/turnos/{turno_id}` | Obtener un turno por ID |
| `PUT` | `/turnos/{turno_id}` | Actualizar un turno |
| `DELETE` | `/turnos/{turno_id}` | Eliminar un turno |
| `GET` | `/turnos/turnos-disponibles` | Obtener horarios disponibles por fecha |

## Funcionalidades del Sistema de Turnos

### Validaciones de Horarios
- **Horario de atención**: Lunes a sábado de 9:00 a 16:30
- **Intervalos**: Turnos cada 30 minutos (9:00, 9:30, 10:00, etc.)
- **Restricciones**: No se permiten turnos los domingos
- **Fecha**: No se pueden crear turnos en fechas pasadas

### Reglas de Negocio
- **Habilitación de personas**: Sistema automático de habilitación/deshabilitación
- **Límite de cancelaciones**: Máximo 5 turnos cancelados en 6 meses
- **Verificación de disponibilidad**: Control de turnos duplicados
- **Estados de turno**: Pendiente, Confirmado, Cancelado, Asistido

## Estructura del Proyecto

```
SL-UNLA-LAB-2025-GRUPO-6/
├── main/
│   └── main.py              # Punto de entrada de la API con todos los endpoints
├── models/
│   ├── models.py            # Modelos SQLAlchemy (Persona, Turno)
│   └── modelsTurno.py       # Modelos específicos de turnos
├── schemas/
│   ├── schemas.py           # Esquemas Pydantic para personas
│   └── schemasTurno.py      # Esquemas Pydantic para turnos
├── crud/
│   ├── crud.py              # Funciones CRUD para personas
│   └── crudTurno.py         # Funciones CRUD para turnos
├── database/
│   └── database.py          # Configuración de la base de datos
├── .venv/                   # Entorno virtual
├── requirements.txt         # Dependencias del proyecto
├── README.md               # Documentación del proyecto
├── abm_personas2.gif       # Demo del funcionamiento
└── personas.db            # Base de datos SQLite (se crea automáticamente)
```

## Ejemplos de Uso

### Crear una Persona
```json
POST /personas
{
  "nombre": "Juan Pérez",
  "email": "juan@email.com",
  "dni": "12345678",
  "telefono": "1123456789",
  "fecha_nacimiento": "1990-05-15",
  "habilitado": true
}
```

### Crear un Turno
```json
POST /turnos
{
  "fecha": "2025-09-25",
  "hora": "14:30:00",
  "persona_id": 1
}
```

### Buscar Personas
```
GET /personas/search?nombre=Juan&edad_min=25&edad_max=50&page=1&per_page=10
```

### Consultar Horarios Disponibles
```
GET /turnos/turnos-disponibles?fecha=2025-09-25
```

## Datos de Prueba

La aplicación incluye datos de prueba que se crean automáticamente al iniciar:
- 3 personas de ejemplo con diferentes perfiles
- Datos realistas para probar todas las funcionalidades

## Manejo de Errores

La API incluye manejo robusto de errores con:
- Códigos de estado HTTP apropiados
- Mensajes de error descriptivos
- Validación de datos de entrada
- Manejo de excepciones de base de datos

## Desarrollo

### Arquitectura
El proyecto sigue el patrón de **Arquitectura Limpia** con:
- **Separación de capas**: API, lógica de negocio, acceso a datos
- **Inyección de dependencias**: Para sesiones de base de datos
- **Modelos Pydantic**: Para validación automática y serialización
- **SQLAlchemy ORM**: Para abstracción de base de datos


## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

---

**Desarrollado por estudiantes de la Universidad de Lanús para Seminario de Lenguajes - 2025**

