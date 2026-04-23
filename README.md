# Logistics Routes System

Sistema Full Stack para gestión, importación y ejecución de rutas logísticas.

**Stack:** Django REST Framework (Python) · Angular 21 · PostgreSQL

---

## Requisitos previos

| Herramienta | Versión mínima |
|-------------|----------------|
| Python      | 3.11+          |
| Node.js     | 20+            |
| npm         | 9+             |
| PostgreSQL  | 14+            |

---

## 1. Despliegue Rápido con Docker (Recomendado)

La forma más sencilla de evaluar este proyecto es utilizando Docker. Esto levantará la base de datos PostgreSQL, el Backend (Django/Gunicorn) y el Frontend (Angular/Nginx) con un solo comando.

```bash
docker-compose up -d --build
```

El sistema estará disponible en:
- **Frontend (Angular):** http://localhost:4200
- **Backend (API):** http://localhost:8000/api/
- **Admin Django:** http://localhost:8000/admin/

*(Nota: La base de datos creará sus tablas automáticamente al iniciar).*

---

## 2. Instalación Manual (Desarrollo local)

Si prefieres ejecutar el código directamente en tu máquina local:

### 2.1 Base de datos
Puedes levantar únicamente la base de datos con Docker:
```bash
docker-compose up -d db
```
*(O crearla manualmente en pgAdmin con el nombre `logistics_db` y usuario `logistics_user` clave `admin`)*.

### 2.2 Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac
pip install -r requirements/base.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2.3 Frontend
```bash
cd frontend
npm install
npm start
```
---

## 4. Importar el dataset de prueba

1. Abre la aplicación en **http://localhost:4200**
2. Ve a **Importar Excel** en el menú lateral
3. Selecciona el archivo `dataset_2.xlsx`
4. Haz clic en **Procesar Importación**
5. El sistema mostrará el resumen: rutas importadas, duplicadas y errores con detalle (fila/campo/motivo)

---

## 5. Estructura del proyecto

```
logistics-routes-system/
├── backend/
│   ├── apps/
│   │   └── routes/          # App principal
│   │       ├── models.py    # Route, ExecutionLog, tablas maestras
│   │       ├── views.py     # Endpoints REST
│   │       ├── serializers.py
│   │       ├── services.py  # Lógica de importación y ejecución
│   │       ├── utils.py     # Parser Excel, validación coordenadas
│   │       ├── filters.py   # Filtros de búsqueda
│   │       └── exceptions.py # Manejador global de errores
│   ├── config/
│   │   ├── settings/
│   │   │   ├── base.py
│   │   │   └── development.py
│   │   └── urls.py
│   ├── requirements/
│   │   ├── base.txt
│   │   └── development.txt
│   └── manage.py
│
├── frontend/
│   └── src/
│       └── app/
│           ├── core/
│           │   ├── models/  # Interfaces TypeScript
│           │   └── services/ # RouteService (HTTP)
│           ├── features/
│           │   ├── dashboard/  # Estadísticas
│           │   ├── import/     # Carga de Excel
│           │   ├── routes/     # Lista y detalle de rutas
│           │   └── logs/       # Auditoría de logs
│           └── shared/
│               └── components/layout/  # Shell principal con sidenav
│
├── .env.example             # Variables de entorno de referencia
└── README.md
```

---

## Validaciones implementadas

### Importación Excel y Creación Individual

- `origin` y `destination`: texto no vacío
- `distance_km`: numérico, estrictamente mayor que 0
- `priority`: entero positivo
- `time_window_start` / `time_window_end`: fecha-hora válida
- `time_window_start` debe ser anterior a `time_window_end`
- `status`: debe ser `READY`, `PENDING`, `EXECUTED` o `FAILED`
- Sin duplicados: combinación `origin + destination + time_window_start + time_window_end` debe ser única
- **Coordenadas en rango Colombia**: lat [-4.3, 13.5] / lon [-82.0, -56.0]
- Coordenadas string o número: se convierten automáticamente
- Fechas seriales de Excel (float): se convierten automáticamente

### Dataset Excel (`dataset_2.xlsx`)

El archivo tiene 6 hojas:
- `oficina_org`: catálogo de oficinas origen
- `priorities_ref`: catálogo de prioridades
- `poblacion_cor`: puntos geográficos de referencia
- `routes`: tabla principal (fechas en serial Excel — se convierten automáticamente)
- `route_payload`: payloads JSON con campos inconsistentes (`direccion`/`address`, `latitud`/`lat`, `longitud`/`lon`)
- `execution_logs`: historial previo (se importa como logs de auditoría)

---

## Notas de diseño

- Los **IDs externos del dataset** (`id_route`, `idOficina`, `idPunto`, etc.) se almacenan como `VARCHAR` para soportar valores alfanuméricos en fuentes reales.
- La **clave primaria de PostgreSQL** (`id`) es siempre un `INTEGER` autoincremental independiente.
- Los errores de importación incluyen: **fila, campo y motivo** exactos.
