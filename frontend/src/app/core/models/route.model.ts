// src/app/core/models/route.model.ts

export interface OficinaOrg {
  id_oficina: string;
  nombre_oficina_origen: string;
}

export interface RoutePayload {
  id_punto?: string;
  direccion?: string;
  latitud?: number;
  longitud?: number;
  primer_peso?: number;
}

export interface ExecutionLog {
  id: number;
  route: string; // ID alfanumérico de la ruta
  execution_time: string;
  result: 'SUCCESS' | 'ERROR';
  message: string;
}

export interface Route {
  id_route: string;
  id_oficina: string;
  origin: string;
  destination: string;
  distance_km: number;
  priority: number;
  time_window_start: string;
  time_window_end: string;
  status: 'READY' | 'PENDING' | 'EXECUTED' | 'FAILED';
  payload?: RoutePayload | null;
  created_at: string;
  execution_logs?: ExecutionLog[];
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    status_code: number;
    detail: any;
  };
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
