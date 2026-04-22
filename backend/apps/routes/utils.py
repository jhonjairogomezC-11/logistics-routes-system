from datetime import datetime, timedelta
from decimal import Decimal
import json
import openpyxl
from django.utils import timezone


# ─── Conversión de fecha serial de Excel ───────────────────────────────────────
def excel_serial_to_datetime(serial):

    if serial is None:
        return None
    try:
        if isinstance(serial, datetime):
            return timezone.make_aware(serial) if timezone.is_naive(serial) else serial
            
        serial = float(serial)
        base = datetime(1899, 12, 30)
        dt = base + timedelta(days=serial)
        return timezone.make_aware(dt)
    except (ValueError, TypeError):
        # Si ya viene como string de fecha, intentar parsear
        try:
            dt = datetime.fromisoformat(str(serial))
            return timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        except Exception:
            return None


# ─── Normalización del payload JSON ────────────────────────────────────────────
def normalize_payload(raw):
    if not raw:
        return None

    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None

    latitud = raw.get('latitud') or raw.get('lat')
    longitud = raw.get('longitud') or raw.get('lon')
    direccion = raw.get('direccion') or raw.get('address')
    piezas = raw.get('piezas', [])
    primer_peso = piezas[0].get('peso') if piezas else None

    # Conversión segura — si no es numérico válido, retorna None
    def safe_float(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    return {
        'id_punto':     raw.get('idPunto'),
        'direccion':    direccion,
        'latitud':      safe_float(latitud),
        'longitud':     safe_float(longitud),
        'primer_peso':  safe_float(primer_peso),
    }


# ─── Validación de coordenadas (rango Colombia) ────────────────────────────────
def validate_coordinates(lat, lon):

    if lat is None or lon is None:
        return False, 'Coordenadas nulas o incompletas'
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return False, 'Coordenadas no son numéricas'

    if not (-4.3 <= lat <= 13.5):
        return False, f'Latitud {lat} fuera del rango válido (-4.3 a 13.5)'
    if not (-82.0 <= lon <= -66.0):
        return False, f'Longitud {lon} fuera del rango válido (-82.0 a -66.0)'

    return True, None


# ─── Mapeo flexible de encabezados ──────────────────────────────────────────────
def normalize_header(header):
    if not header: return ""
    # Convierte a minúsculas, quita espacios y guiones bajos para comparar
    return str(header).lower().replace("_", "").replace(" ", "").strip()

def get_header_map(headers):
    """Crea un mapa de encabezados encontrados vs nombres esperados."""
    mapping = {
        'idroute':          ['idroute', 'idruta', 'id', 'id_route', 'id_ruta'],
        'idoficinid':       ['idoficinaorigen', 'idoficina', 'oficina', 'id_oficina', 'oficina_id'],
        'origin':           ['origin', 'origen', 'punto_origen', 'salida'],
        'destination':      ['destination', 'destino', 'punto_destino', 'llegada'],
        'distance_km':      ['distancekm', 'distanciakm', 'distancia', 'km'],
        'priority':         ['priority', 'prioridad', 'nivel_prioridad'],
        'time_window_start':['timewindowstart', 'ventanainicio', 'inicio', 'desde'],
        'time_window_end':  ['timewindowend', 'ventanafin', 'fin', 'hasta'],
        'status':           ['status', 'estado', 'fase'],
        'created_at':       ['createdat', 'fecharegistro', 'fecha', 'creado', 'timestamp']
    }
    
    found_map = {}
    normalized_headers = [normalize_header(h) for h in headers]
    
    for target, aliases in mapping.items():
        for i, h in enumerate(normalized_headers):
            if h in aliases:
                found_map[target] = headers[i]
                break
    return found_map

# ─── Parser principal del Excel ────────────────────────────────────────────────
def parse_excel(file):
    valid_rows = []
    errors = []

    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        return {'valid_rows': [], 'errors': [{'row': 0, 'field': 'file', 'value': None, 'reason': f'No se pudo leer el archivo: {e}'}]}

    if 'routes' not in wb.sheetnames:
        # Si no hay hoja 'routes', intentar con la primera hoja disponible
        sheet_name = wb.sheetnames[0]
    else:
        sheet_name = 'routes'

    ws_routes = wb[sheet_name]
    
    # Obtener encabezados de forma segura
    header_row = next(ws_routes.iter_rows(min_row=1, max_row=1), None)
    if not header_row:
        return {'valid_rows': [], 'errors': [{'row': 0, 'field': 'sheet', 'value': None, 'reason': "La hoja está vacía"}]}
    
    headers = [cell.value for cell in header_row]
    h_map = get_header_map(headers)

    # ── Leer hoja route_payload como dict {idRoute: payload_normalizado} ──
    payloads = {}
    payload_sheet = next((s for s in wb.sheetnames if normalize_header(s) in ['routepayload', 'payload', 'datos']), None)
    
    if payload_sheet:
        ws_payload = wb[payload_sheet]
        next(ws_payload.iter_rows(min_row=1, max_row=1), None)  # saltar header
        for row in ws_payload.iter_rows(min_row=2, values_only=True):
            if len(row) >= 2:
                id_route, raw_payload = row[0], row[1]
                if id_route:
                    payloads[id_route] = normalize_payload(raw_payload)

    # ── Procesar cada fila de routes ──
    for row_idx, row in enumerate(ws_routes.iter_rows(min_row=2, values_only=True), start=2):
        row_data = dict(zip(headers, row))
        row_errors = []

        # Extraer usando el mapa flexible
        id_route           = row_data.get(h_map.get('idroute'))
        id_oficina         = row_data.get(h_map.get('idoficinid'))
        origin             = row_data.get(h_map.get('origin'))
        destination        = row_data.get(h_map.get('destination'))
        distance_km        = row_data.get(h_map.get('distance_km'))
        priority           = row_data.get(h_map.get('priority'))
        time_window_start  = row_data.get(h_map.get('time_window_start'))
        time_window_end    = row_data.get(h_map.get('time_window_end'))
        status             = row_data.get(h_map.get('status')) or 'READY'
        created_at         = row_data.get(h_map.get('created_at'))

        # ── Validaciones de campos obligatorios ──
        if not origin:
            row_errors.append({'row': row_idx, 'field': 'origin', 'value': None, 'reason': 'Columna Origen no encontrada o vacía'})
        if not destination:
            row_errors.append({'row': row_idx, 'field': 'destination', 'value': None, 'reason': 'Columna Destino no encontrada o vacía'})
        
        if distance_km is None:
            # Intentar valor fallback si es vital
            distance_km = 1.0 # Default fallback
        else:
            try:
                distance_km = float(distance_km)
            except (ValueError, TypeError):
                row_errors.append({'row': row_idx, 'field': 'distance_km', 'value': distance_km, 'reason': 'Debe ser un número'})

        if priority is None:
            priority = 1
        else:
            try:
                priority = int(priority)
            except (ValueError, TypeError):
                priority = 1

        # Normalizar status
        status = str(status).upper().strip()
        if status not in ('READY', 'PENDING', 'EXECUTED', 'FAILED'):
            status = 'READY'

        # ── Conversión y validación de fechas ──
        tw_start = excel_serial_to_datetime(time_window_start)
        tw_end   = excel_serial_to_datetime(time_window_end)
        cr_at    = excel_serial_to_datetime(created_at)

        if not tw_start:
             tw_start = timezone.now()
        if not tw_end:
             tw_end = tw_start + timedelta(hours=8)
        
        # ── Validación de coordenadas desde el payload ──
        payload = payloads.get(id_route)
        if payload:
            coord_ok, coord_err = validate_coordinates(payload.get('latitud'), payload.get('longitud'))
            if not coord_ok:
                row_errors.append({'row': row_idx, 'field': 'coordenadas', 'value': f"{payload.get('latitud')}, {payload.get('longitud')}", 'reason': coord_err})

        # ── Resultado de la fila ──
        if row_errors:
            errors.extend(row_errors)
        else:
            # Generar ID si falta
            if not id_route:
                id_route = row_idx + 1000

            valid_rows.append({
                'id_route':          id_route,
                'id_oficina_id':     id_oficina,
                'origin':            str(origin).strip(),
                'destination':       str(destination).strip(),
                'distance_km':       Decimal(str(distance_km)),
                'priority':          priority,
                'time_window_start': tw_start,
                'time_window_end':   tw_end,
                'status':            status,
                'payload':           payload,
                'created_at':        cr_at or timezone.now(),
            })

    return {'valid_rows': valid_rows, 'errors': errors}