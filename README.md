# Logistics Routes System

> Gestión de rutas logísticas con carga masiva desde Excel, validaciones geográficas y trazabilidad completa de ejecuciones.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.2-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-3.17-red?style=flat-square&logo=django&logoColor=white)
![Angular](https://img.shields.io/badge/Angular-21-DD0031?style=flat-square&logo=angular&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

---

## Qué es esto y para qué sirve

El problema que resuelve este sistema es simple de enunciar pero tedioso de manejar a mano: una operación logística tiene cientos de rutas que llegan en archivos Excel —con fechas en formato serial de Windows, coordenadas que a veces caen en el océano Atlántico, y payloads JSON con nombres de campos que cambian entre filas— y alguien necesita cargar todo eso en una base de datos, filtrar lo válido, registrar lo que falló y saber qué se ejecutó y cuándo.

El sistema hace exactamente eso. Recibe el archivo, lo parsea hoja por hoja, sincroniza las tablas maestras de oficinas, prioridades y puntos geográficos, valida cada fila contra reglas concretas (distancia positiva, ventana horaria coherente, coordenadas dentro del territorio colombiano) y guarda solo lo que pasa. Todo lo que falla queda registrado en los logs de auditoría con fila, campo y motivo exactos.

Una vez cargadas las rutas, se pueden ejecutar en lote enviando sus IDs, lo que cambia su estado a `EXECUTED` y genera el log correspondiente. Hay un dashboard que muestra el conteo por estado en tiempo real, una vista de lista con filtros y ordenamiento, y un historial de logs globales paginado. El frontend en Angular es la cara visible de todo esto, pero la API REST funciona igual de bien sola —de hecho, la colección de Postman ya viene lista.

---

## Qué hay dentro

El proyecto tiene tres capas bien separadas y un par de directorios de soporte:

**`backend/`** — El corazón del sistema. Django 5.2 con Django REST Framework. Dentro de `apps/routes/` está todo: modelos, serializers, vistas, servicios, utilidades de parseo del Excel, filtros, autenticación por token y las pruebas unitarias. La configuración está dividida en `base.py` y `development.py` bajo `config/settings/`, y los requirements en tres archivos: `base.txt`, `development.txt` (agrega pytest y factory-boy) y `production.txt` (agrega gunicorn y whitenoise).

**`frontend/`** — Aplicación Angular 21 con Angular Material. Está organizada por features: `dashboard`, `routes`, `import`, `logs` y `auth`. El core tiene los servicios (`auth.service.ts`, `route.service.ts`), el interceptor HTTP que inyecta el token en cada petición y el guard que protege las rutas privadas. En Docker, se compila con `ng build --configuration production` y se sirve con Nginx en el puerto 4200.

**`data/`** — Aquí vive `dataset_2.xlsx`, el archivo de prueba con todos los casos: rutas válidas, fechas en formato serial de Excel, coordenadas fuera de Colombia, payloads con campos inconsistentes. Es el archivo que hay que subir para probar el flujo completo de importación.

**`postman/`** — La colección `Logistics_Routes_API.postman_collection.json` con 8 peticiones listas para usar. El login captura el token automáticamente y lo inyecta en las demás.

**`docs/database/`** — Un `schema.sql` con el DDL completo de las 5 tablas, generado para referencia rápida. Sirve para entender la estructura sin tener que mirar los modelos de Django.

---

## Herramientas que usamos

| Tecnología | Para qué la usamos aquí |
|---|---|
| **Django 5.2** | El esqueleto del backend: modelos, ORM, migraciones, admin y ciclo request/response |
| **Django REST Framework 3.17** | Los endpoints REST, serializers con validaciones, paginación y autenticación por token |
| **django-filter 25.2** | Filtros declarativos en `GET /api/routes/` por status, priority, origin, destination y fechas |
| **django-cors-headers 4.9** | CORS configurable por variable de entorno para que el frontend pueda hablar con la API |
| **psycopg2-binary 2.9** | Driver de PostgreSQL para Django |
| **openpyxl 3.1** | Parseo del archivo Excel hoja por hoja, sin cargar todo en memoria (modo read-only) |
| **python-dotenv 1.2** | Leer el archivo `.env` en desarrollo local |
| **gunicorn 23** | Servidor WSGI en producción/Docker, con timeout de 300s para archivos Excel grandes |
| **whitenoise 6.9** | Servir los archivos estáticos del admin de Django sin necesidad de un servidor adicional |
| **PostgreSQL 16** | Base de datos principal; usamos `JSONB` para el campo payload y constraints de unicidad |
| **Angular 21** | Framework del frontend con componentes standalone y carga lazy por ruta |
| **Angular Material 21** | Componentes UI: tablas, cards, diálogos, progress bars, formularios |
| **Angular Signals** | Estado reactivo en el `AuthService` y el `DashboardComponent` sin necesidad de NgRx |
| **Nginx (alpine)** | Servidor del frontend compilado en Docker, con `try_files` para que el routing de Angular funcione |
| **Docker + Docker Compose** | Tres servicios coordinados: `db`, `backend` y `frontend`, con healthcheck en la base de datos |
| **pytest + pytest-django** | Suite de pruebas unitarias del backend |
| **factory-boy** | Factories para los modelos en tests |

---

## Cómo levantar el proyecto — con Docker (empieza por aquí)

Esta es la forma más rápida. En dos minutos tenemos los tres servicios corriendo sin instalar Python ni Node.

**Requisitos previos:** Docker Desktop instalado y corriendo. Nada más.

```bash
# 1. Clonar el repositorio
git clone https://github.com/jhonjairogomezC-11/logistics-routes-system.git
cd logistics-routes-system

# 2. Levantar todo
docker compose up --build
```

Docker Compose levanta tres servicios en orden: primero la base de datos PostgreSQL (con healthcheck), luego el backend (que corre `collectstatic`, `migrate`, crea el superusuario `admin` y arranca gunicorn), y finalmente el frontend (que compila Angular y lo sirve con Nginx).

La primera vez tarda un poco más porque compila el frontend. Las siguientes veces es casi instantáneo.

**Verificar que todo está corriendo:**

```bash
docker compose ps
# Los tres servicios deben aparecer como "running" o "healthy"
```

**URLs una vez levantado:**

| Servicio | URL |
|---|---|
| Frontend | http://localhost:4200 |
| API REST | http://localhost:8000/api/ |
| Admin Django | http://localhost:8000/admin/ |

Credenciales del admin creado automáticamente: `admin` / `admin123`.

**Para bajar todo:**
```bash
docker compose down
# Con -v si también queremos borrar el volumen de la base de datos
docker compose down -v
```

---

## Cómo levantar el proyecto — en local sin Docker

Para quien prefiere tener control directo sobre cada proceso o necesita debuggear.

**Requisitos previos:**
- Python 3.13 (el backend está desarrollado y probado con esta versión)
- Node.js 20 + npm 11
- PostgreSQL 16 corriendo localmente

### Backend

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements/development.txt

# Configurar variables de entorno
cp ../.env.example .env
# Editar .env con los datos de tu PostgreSQL local
```

Antes de correr las migraciones, la base de datos debe existir:
```sql
-- En psql o cualquier cliente PostgreSQL:
CREATE DATABASE logistics_db;
```

```bash
# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional, para acceder al admin)
python manage.py createsuperuser

# Levantar el servidor de desarrollo
python manage.py runserver
```

La API queda disponible en `http://localhost:8000/api/`.

**Para correr los tests:**
```bash
pytest
# O con más detalle:
pytest -v
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Verificar que el environment apunta a la API correcta
# src/environments/environment.ts debe tener:
# apiUrl: 'http://localhost:8000/api'

# Levantar el servidor de desarrollo
npm start
```

El frontend queda en `http://localhost:4200`.

**Posibles problemas comunes:**

- *"CORS error en el navegador"*: Verificar que `CORS_ALLOWED_ORIGINS` en el `.env` incluya `http://localhost:4200`.
- *"psycopg2 no instala en Windows"*: `requirements/base.txt` usa `psycopg2-binary` precisamente para evitar esto, pero si hay problemas con la versión de Python, instalar Visual C++ Build Tools.
- *"La compilación de Angular falla con errores de TypeScript"*: Verificar que se está usando Node.js 20. La versión 18 tiene incompatibilidades con Angular 21.

---

## Variables de entorno

Todas las variables van en `backend/.env`. El archivo `/.env.example` en la raíz del proyecto tiene la plantilla:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DEBUG` | Modo debug de Django. En producción debe ser `False` | `True` |
| `SECRET_KEY` | Clave secreta de Django. Cambiar en producción por una cadena larga y aleatoria | `change-me-in-production-...` |
| `DB_NAME` | Nombre de la base de datos PostgreSQL | `logistics_db` |
| `DB_USER` | Usuario de PostgreSQL | `postgres` |
| `DB_PASSWORD` | Contraseña del usuario | `your_password_here` |
| `DB_HOST` | Host de la base de datos. En Docker es el nombre del servicio (`db`) | `localhost` |
| `DB_PORT` | Puerto de PostgreSQL | `5432` |
| `ALLOWED_HOSTS` | Hosts permitidos separados por coma | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS permitidos separados por coma | `http://localhost:4200` |

En Docker, estas variables se inyectan directamente desde el `docker-compose.yml` y no hace falta un `.env` separado para el backend.

---

## El dataset de prueba

El archivo `data/dataset_2.xlsx` es el conjunto de datos que se usa para probar la importación. Tiene 6 hojas:

| Hoja | Contenido |
|---|---|
| `routes` | La hoja principal. Rutas con campos `id_route`, `id_oficina_origen`, `origin`, `destination`, `distance_km`, `priority`, `time_window_start`, `time_window_end`, `status`, `created_at` |
| `route_payload` | Payloads JSON asociados a cada ruta. Intencionalmente tiene campos con nombres inconsistentes entre filas (`latitud`/`lat`, `longitud`/`lon`, `direccion`/`address`) |
| `oficina_org` | Tabla maestra de oficinas origen |
| `priorities_ref` | Tabla maestra de prioridades |
| `poblacion_cor` | Puntos geográficos de referencia con coordenadas |
| `execution_logs` | Logs históricos. El sistema los ignora al importar (los genera él mismo) |

El dataset tiene casos de error deliberados para probar las validaciones: fechas almacenadas como números seriales de Excel (ej. `45678.5` en lugar de un datetime legible), coordenadas con latitud o longitud fuera del rango geográfico de Colombia (latitud: -4.3 a 13.5, longitud: -82.0 a -56.0), rutas con distancia cero o negativa, y rutas duplicadas que violan la restricción de unicidad `(origin, destination, time_window_start, time_window_end)`.

Después de importar el dataset, la respuesta del API muestra exactamente cuántas se importaron, cuántas eran duplicadas y cuántas fallaron, con el detalle fila/campo/motivo para cada error.

---

## Cómo usar la colección de Postman

El archivo está en `postman/Logistics_Routes_API.postman_collection.json`.

**Importar:** Abrir Postman → Import → seleccionar el archivo. La colección ya tiene dos variables configuradas: `base_url` (`http://localhost:8000`) y `auth_token` (vacío al inicio).

**El primer paso siempre es hacer login.** La petición "1. Autenticación (Login)" tiene un script de test que captura el token de la respuesta y lo guarda automáticamente en `auth_token`. Todas las demás peticiones de la colección usan esa variable en el header `Authorization: Token {{auth_token}}`, así que no hay que hacer nada manualmente.

| # | Petición | Para qué sirve |
|---|---|---|
| 1 | Autenticación (Login) | Obtener el token. Ejecutar siempre primero |
| 2 | Importación Masiva | Subir `dataset_2.xlsx` desde Body → form-data, campo `file` |
| 3 | Creación Individual | Crear una ruta manualmente con todos sus campos y validaciones |
| 4 | Listado General (Paginado) | Ver todas las rutas, 50 por página |
| 5 | Listado con Filtros y Orden | Filtrar por `status=READY`, `priority=1`, ordenar por `-distance_km` |
| 6 | Ejecución de Rutas (Batch) | Enviar un array de `route_ids` para ejecutarlos en lote |
| 7 | Consulta de Logs (Global) | Auditoría completa paginada de todo el sistema |
| 8 | Consulta de Logs (Por Ruta) | Historial de una ruta específica por su `id_route` |

Para la importación (petición 2), hay que ir a Body → form-data, seleccionar el tipo `File` en el campo `file` y elegir `data/dataset_2.xlsx`.

---

## Qué cumple de la prueba técnica

| Requisito | Estado | Dónde verificarlo |
|---|---|---|
| API REST con Django y DRF | ✅ | `backend/apps/routes/views.py`, `urls.py` |
| Importación masiva desde Excel (.xlsx) | ✅ | `POST /api/routes/import/` → `services.py` + `utils.py` |
| Validación de campos obligatorios (origin, destination, distance_km, priority) | ✅ | `utils.py` (parseo) y `serializers.py` (creación individual) |
| Validación de ventana horaria (start < end) | ✅ | `utils.py` líneas 337-343, `serializers.py` líneas 92-95 |
| Detección de duplicados por (origin, destination, start, end) | ✅ | `services.py` líneas 77-95, constraint en `models.py` líneas 78-83 |
| Validación de coordenadas geográficas (rango Colombia) | ✅ | `utils.py` `validate_coordinates()` líneas 77-104 |
| Manejo de fechas en formato serial de Excel | ✅ | `utils.py` `excel_serial_to_datetime()` líneas 9-30 |
| Ejecución de rutas (cambio de estado a EXECUTED) | ✅ | `POST /api/routes/execute/` → `services.py` `RouteExecutionService` |
| Logs de auditoría por ruta y globales | ✅ | `GET /api/routes/<id>/logs/` y `GET /api/logs/` |
| Paginación de la lista de rutas | ✅ | `StandardResultsSetPagination` en `views.py` (50 por página, máx 1000) |
| Filtros por status, priority, origin, destination y fechas | ✅ | `filters.py` + parámetros de query en `GET /api/routes/` |
| Ordenamiento por campos | ✅ | `?ordering=priority`, `?ordering=-distance_km`, etc. |
| Base de datos PostgreSQL | ✅ | `config/settings/base.py` líneas 68-77 |
| Colección de Postman | ✅ | `postman/Logistics_Routes_API.postman_collection.json` |
| Dataset de prueba con datos reales | ✅ | `data/dataset_2.xlsx` |

---

## Extras y decisiones técnicas

**Bulk insert en la importación.** En lugar de guardar cada ruta en un loop con `.save()`, el servicio de importación agrupa todas las filas válidas en una lista y ejecuta un único `Route.objects.bulk_create()` dentro de una transacción atómica. Lo mismo para los logs de éxito. Con datasets de varios cientos de filas, la diferencia en tiempo es notable. El tradeoff es que si el bloque falla, ninguna ruta se guarda (o se guardan todas), lo cual es el comportamiento correcto en importaciones masivas.

**Mapeo flexible de encabezados.** El parser del Excel no asume que los encabezados tienen exactamente los nombres esperados. La función `get_header_map()` en `utils.py` acepta variantes: `id_route` o `id_ruta` o `id`, `origin` o `origen` o `salida`, etc. Esto hace que el sistema no explote si alguien renombra una columna siguiendo su propio criterio.

**Normalización de payloads inconsistentes.** La hoja `route_payload` tiene filas donde los campos se llaman `latitud`/`lat`, `longitud`/`lon`, `direccion`/`address` dependiendo de la fila. La función `normalize_payload()` maneja todos los alias y devuelve siempre la misma estructura, o `None` si el payload no tiene sentido.

**Sincronización de tablas maestras en cada importación.** Cada vez que se sube un Excel, el sistema sincroniza las hojas `oficina_org`, `priorities_ref` y `poblacion_cor` con `update_or_create`, sin borrar lo que ya existía. Esto permite que importaciones sucesivas vayan enriqueciendo el catálogo sin pisar datos previos.

**Autenticación por token con señales de Angular.** El `AuthService` usa `signal()` y `computed()` de Angular 21 para el estado reactivo del usuario autenticado. El guard `authGuard` y el interceptor `authInterceptor` se implementaron como funciones (el nuevo estilo Angular, sin clases), y el interceptor maneja automáticamente la expiración del token redirigiendo al login cuando el backend responde 401.

**Custom exception handler.** Todos los errores de la API tienen el mismo formato: `{ success: false, error: { status_code: ..., detail: ... } }`. Se implementó un `custom_exception_handler` en `exceptions.py` que envuelve tanto los errores de DRF como los errores no manejados en esa estructura, así el frontend siempre sabe qué esperar.

**Suite de tests con cobertura real.** Los tests en `apps/routes/tests/` cubren los endpoints principales con casos positivos y negativos: lista vacía y con datos, filtros por cada campo, ordenamiento, creación con cada validación que falla, detalle con logs embebidos, importación con mock del parser, ejecución mixta (algunas rutas existen, otras no), logs por ruta y globales. Son más de 30 casos de prueba que se ejecutan con `pytest`.

**Django Admin configurado.** Todos los modelos están registrados en `admin.py` con `list_display`, `list_filter`, `search_fields` y `ordering` apropiados. `RouteAdmin` incluye un `TabularInline` de los logs de ejecución, así que desde el admin se ve el historial de una ruta directamente en su formulario.

---

## Posibles problemas conocidos

**Timeout en Docker al importar archivos Excel grandes.** Gunicorn tiene el timeout configurado a 300 segundos en el `docker-compose.yml`. Si el archivo es extremadamente grande (miles de filas con payloads complejos), podría ser necesario aumentarlo. El comando de arranque está en la sección `command` del servicio `backend` en `docker-compose.yml`.

**El `.env` del backend en local vs Docker.** En local, el `.env` va dentro de `backend/`. En Docker, las variables se inyectan directamente desde `docker-compose.yml`, así que el `.env` no se usa. Si se cambia algo en el `.env` esperando verlo en Docker, no va a funcionar — hay que editar el `docker-compose.yml`.

**Puerto 4200 ocupado.** Nginx en el contenedor del frontend escucha en el puerto 4200 (configurado en `nginx.conf`). Si ese puerto está en uso, Docker Compose fallará al intentar mapearlo. Solución: cambiar `"4200:4200"` en `docker-compose.yml` al puerto disponible.

**npm version mismatch en la imagen de Docker.** El `package.json` especifica `"packageManager": "npm@11.6.2"`. Si la imagen base de Node que se usa en el `Dockerfile` del frontend tiene una versión diferente de npm, puede haber advertencias durante el build. No rompe nada, pero si aparece un error de lock file, el `Dockerfile` instala con `npm install` (sin `--frozen-lockfile`) precisamente para evitar esto.
