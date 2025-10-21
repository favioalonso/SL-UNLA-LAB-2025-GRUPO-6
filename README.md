# CRUD de Personas y Turnos - SL-UNLA-LAB-2025-GRUPO-6

Este proyecto es una API REST desarrollada en Python con FastAPI y SQLAlchemy para la gestión de personas y turnos. Permite crear, leer, actualizar y eliminar registros de personas y turnos en una base de datos SQLite con arquitectura modular y validaciones robustas.

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
   - Swagger UI: [http://localhost:8C000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

3. **Accede a la Collection de Postman:**
   - Descarga el archivo de la [Collection](./Collection.postman_collection.json)
   - Importa el archivo a [Postman](https://www.postman.com/)

## Endpoints API

### 📋 Personas

| Método | Endpoint | Descripción | Desarrollado por |
|--------|----------|-------------|------------------|
| `POST` | `/personas` | Crear una nueva persona | Favio Alonso |
| `GET` | `/personas` | Listar todas las personas (con paginación) | Favio Alonso |
| `GET` | `/personas/search` | Búsqueda avanzada con filtros | Favio Alonso |
| `GET` | `/personas/{persona_id}` | Obtener una persona por ID | Favio Alonso |
| `PUT` | `/personas/{persona_id}` | Actualizar una persona | Favio Alonso |
| `DELETE` | `/personas/{persona_id}` | Eliminar una persona | Favio Alonso |

### 🗓️ Turnos

| Método | Endpoint | Descripción | Desarrollado por |
|--------|----------|-------------|------------------|
| `POST` | `/turnos` | Crear un nuevo turno | Marcos Charadia |
| `GET` | `/turnos` | Listar todos los turnos (con paginación) | Marcos Charadia |
| `GET` | `/turnos/{turno_id}` | Obtener un turno por ID | Gonzalo Liberatori |
| `PUT` | `/turnos/{turno_id}` | Actualizar un turno | Gonzalo Liberatori |
| `DELETE` | `/turnos/{turno_id}` | Eliminar un turno | Martina Martinez |
| `GET` | `/turnos/turnos-disponibles` | Obtener horarios disponibles por fecha | Martina Martinez |
| `PUT` | `/turnos/{id}/cancelar` | Cancelar turno por id | Favio Alonso |
| `PUT` | `/turnos/{id}/confirmar` | Confirmar turno por id | Favio Alonso |

### 📈 Reportes
| Método | Endpoint | Descripción | Desarrollado por |
|--------|----------|-------------|------------------|
| `GET` | `/reportes/turnos-por-fecha?fecha=YYYY-MM-DD` | Reporte de turnos por fecha | Marcos Charadia |
| `GET` | `/reportes/turnos-cancelados-por-mes` | Reporte de turnos cancelados por mes | Marcos Charadia |
| `GET` | `/reportes/turnos-por-persona?dni=12345678`| Reporte de turnos por persona por dni | Gonzalo Liberatori |
| `GET` | `/reportes/turnos-cancelados?min=5` | Reporte de personas con min 5 turnos cancelados | Gonzalo Liberatori |
| `GET` | `/reportes/turnos-confirmados?desde=YYYY-MM-DD&hasta=YYYY-MM-DD` | Reporte de turnos confirmados entre dos fechas | Martina Martinez |
| `GET` | `/reportes/estado-personas?habilitada=true/false` | Reporte de personas segun estado | Martina Martinez |


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

## 📊 Datos de Prueba

La aplicación incluye **datos de prueba automáticos** que se crean al iniciar el servidor por primera vez, permitiendo probar todas las funcionalidades del sistema inmediatamente.

### 👥 Personas (7 registros)

| Estado | Cantidad | Descripción |
|--------|----------|-------------|
| ✅ Habilitadas | 6 | Edades entre 25-46 años, diversos proveedores de email |
| ❌ Deshabilitadas | 1 | Laura Fernández (6 turnos cancelados) - demuestra deshabilitación automática |

### 📅 Turnos (20 registros)

Los turnos se distribuyen estratégicamente para probar todos los endpoints de reportes:

| Estado | Cantidad | Propósito |
|--------|----------|-----------|
| 🟡 **Pendientes** | 5 | Operaciones de confirmación y cancelación |
| 🟢 **Confirmados** | 5 | Reportes entre fechas (nov 15-19, 2025) con paginación |
| 🔴 **Cancelados** | 7 | Reporte de personas con 5+ cancelados (6 de Laura + 1 de María) |
| 🔵 **Asistidos** | 3 | Validación de restricciones (no modificables/eliminables) |

### ✨ Escenarios de Prueba Incluidos

- 📆 **Reportes por fecha**: Turnos en septiembre, octubre y noviembre 2025
- 📊 **Reportes de cancelados del mes**: Múltiples turnos en meses recientes
- 👤 **Reportes por persona**: Cada persona con turnos en diferentes estados
- ⚠️ **Personas con 5+ turnos cancelados**: Laura Fernández (condición automática)
- 📈 **Reportes de confirmados entre fechas**: 5 turnos en rango específico
- 🔄 **Estado de personas**: 6 habilitadas y 1 deshabilitada

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

## Link al video Hito 1
https://drive.google.com/file/d/1zRo9_vqyDQRZcNrbqrovAnPfdVERRIvS/view?usp=sharing

## Link al video Hito 2
https://drive.google.com/file/d/1_mOngNIFYOWGUB_p0UwPGWNjN9FxRYMx/view?usp=sharing

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más información.

---

**Desarrollado por estudiantes de la Universidad de Lanús para Seminario de Lenguajes - 2025**

