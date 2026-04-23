-- DDL del Sistema de Rutas Logísticas
-- Generado automáticamente para visualización de la estructura de base de datos

-- 1. Tabla de Oficinas Origen
CREATE TABLE oficina_org (
    id SERIAL PRIMARY KEY,
    id_oficina VARCHAR(50) UNIQUE NOT NULL,
    nombre_oficina_origen VARCHAR(200) NOT NULL
);

-- 2. Tabla de Referencia de Poblaciones (Coordenadas)
CREATE TABLE poblacion_cor (
    id SERIAL PRIMARY KEY,
    id_punto VARCHAR(50) UNIQUE NOT NULL,
    ciudad VARCHAR(200) NOT NULL,
    lat_ref DECIMAL(12, 8) NOT NULL,
    lon_ref DECIMAL(12, 8) NOT NULL
);

-- 3. Tabla de Referencia de Prioridades
CREATE TABLE priorities_ref (
    id SERIAL PRIMARY KEY,
    priority VARCHAR(50) UNIQUE NOT NULL,
    priority_name VARCHAR(100) NOT NULL
);

-- 4. Tabla Principal de Rutas
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    id_route VARCHAR(50) UNIQUE NOT NULL,
    id_oficina VARCHAR(50) REFERENCES oficina_org(id_oficina) ON DELETE SET NULL,
    origin VARCHAR(500) NOT NULL,
    destination VARCHAR(500) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    priority INTEGER NOT NULL,
    time_window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Restricción de unicidad para evitar duplicados de negocio
    CONSTRAINT unique_route UNIQUE (origin, destination, time_window_start, time_window_end)
);

-- 5. Tabla de Logs de Auditoría (Trazabilidad)
CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    route_id VARCHAR(50) REFERENCES routes(id_route) ON DELETE CASCADE,
    execution_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    result VARCHAR(20) NOT NULL,
    message TEXT
);
