from datetime import datetime, timedelta
from decimal import Decimal
import json
import openpyxl


# ─── Conversión de fecha serial de Excel ───────────────────────────────────────
def excel_serial_to_datetime(serial):

    if serial is None:
        return None
    try:
        serial = float(serial)
        base = datetime(1899, 12, 30)
        return base + timedelta(days=serial)
    except (ValueError, TypeError):
        # Si ya viene como string de fecha, intentar parsear
        try:
            return datetime.fromisoformat(str(serial))
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

    if not (-4.0 <= lat <= 12.5):
        return False, f'Latitud {lat} fuera del rango válido (-4.0 a 12.5)'
    if not (-79.0 <= lon <= -67.0):
        return False, f'Longitud {lon} fuera del rango válido (-79.0 a -67.0)'

    return True, None


# ─── Parser principal del Excel ────────────────────────────────────────────────
def parse_excel(file):

    valid_rows = []
    errors = []

    try:
        wb = openpyxl.load_workbook(file, read_only=True, data_only=True)
    except Exception as e:
        return {'valid_rows': [], 'errors': [{'row': 0, 'field': 'file', 'value': None, 'reason': f'No se pudo leer el archivo: {e}'}]}

    # ── Leer hoja routes ──
    if 'routes' not in wb.sheetnames:
        return {'valid_rows': [], 'errors': [{'row': 0, 'field': 'sheet', 'value': None, 'reason': "No se encontró la hoja 'routes'"}]}

    ws_routes = wb['routes']
    headers = [cell.value for cell in next(ws_routes.iter_rows(min_row=1, max_row=1))]

    # ── Leer hoja route_payload como dict {idRoute: payload_normalizado} ──
    payloads = {}
    if 'route_payload' in wb.sheetnames:
        ws_payload = wb['route_payload']
        next(ws_payload.iter_rows(min_row=1, max_row=1))  # saltar header
        for row in ws_payload.iter_rows(min_row=2, values_only=True):
            id_route, raw_payload = row[0], row[1]
            if id_route:
                payloads[id_route] = normalize_payload(raw_payload)

    # ── Procesar cada fila de routes ──
    for row_idx, row in enumerate(ws_routes.iter_rows(min_row=2, values_only=True), start=2):
        row_data = dict(zip(headers, row))
        row_errors = []

        id_route           = row_data.get('idRoute')
        id_oficina         = row_data.get('idOficinaOrigen')
        origin             = row_data.get('origin')
        destination        = row_data.get('destination')
        distance_km        = row_data.get('distance_km')
        priority           = row_data.get('priority')
        time_window_start  = row_data.get('time_window_start')
        time_window_end    = row_data.get('time_window_end')
        status             = row_data.get('status')
        created_at         = row_data.get('created_at') or row_data.get('fechaRegistro')

        # ── Validaciones de campos obligatorios ──
        if not origin or str(origin).strip() == '':
            row_errors.append({'row': row_idx, 'field': 'origin', 'value': origin, 'reason': 'Campo obligatorio vacío'})

        if not destination or str(destination).strip() == '':
            row_errors.append({'row': row_idx, 'field': 'destination', 'value': destination, 'reason': 'Campo obligatorio vacío'})

        if distance_km is None:
            row_errors.append({'row': row_idx, 'field': 'distance_km', 'value': None, 'reason': 'Campo obligatorio'})
        else:
            try:
                distance_km = float(distance_km)
                if distance_km <= 0:
                    row_errors.append({'row': row_idx, 'field': 'distance_km', 'value': distance_km, 'reason': 'Debe ser mayor que 0'})
            except (ValueError, TypeError):
                row_errors.append({'row': row_idx, 'field': 'distance_km', 'value': distance_km, 'reason': 'Debe ser un número'})

        if priority is None:
            row_errors.append({'row': row_idx, 'field': 'priority', 'value': None, 'reason': 'Campo obligatorio'})
        else:
            try:
                priority = int(priority)
                if priority <= 0:
                    row_errors.append({'row': row_idx, 'field': 'priority', 'value': priority, 'reason': 'Debe ser entero positivo'})
            except (ValueError, TypeError):
                row_errors.append({'row': row_idx, 'field': 'priority', 'value': priority, 'reason': 'Debe ser un entero'})

        if status not in ('READY', 'PENDING', 'EXECUTED', 'FAILED'):
            row_errors.append({'row': row_idx, 'field': 'status', 'value': status, 'reason': "Debe ser READY, PENDING, EXECUTED o FAILED"})

        # ── Conversión y validación de fechas ──
        tw_start = excel_serial_to_datetime(time_window_start)
        tw_end   = excel_serial_to_datetime(time_window_end)
        cr_at    = excel_serial_to_datetime(created_at)

        if tw_start is None:
            row_errors.append({'row': row_idx, 'field': 'time_window_start', 'value': time_window_start, 'reason': 'Fecha inválida'})
        if tw_end is None:
            row_errors.append({'row': row_idx, 'field': 'time_window_end', 'value': time_window_end, 'reason': 'Fecha inválida'})
        if tw_start and tw_end and tw_start >= tw_end:
            row_errors.append({'row': row_idx, 'field': 'time_window_end', 'value': time_window_end, 'reason': 'time_window_end debe ser posterior a time_window_start'})

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
                'created_at':        cr_at or datetime.now(),
            })

    return {'valid_rows': valid_rows, 'errors': errors}