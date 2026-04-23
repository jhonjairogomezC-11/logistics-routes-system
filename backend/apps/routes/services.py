from django.db import transaction
from decimal import Decimal
from .models import Route, ExecutionLog
from .utils import parse_excel
import logging

logger = logging.getLogger('apps.routes')


class RouteImportService:

    @staticmethod
    def process(file):
        """
        Procesa un archivo Excel de rutas.
        1. Parsea el archivo y valida cada fila
        2. Sincroniza tablas maestras (oficinas, prioridades, poblaciones)
        3. Inserta solo los registros válidos (sin duplicados)
        4. Retorna un reporte detallado con fila/campo/motivo para cada error
        """
        from .models import OficinaOrg, PriorityRef, PoblacionCor

        result = parse_excel(file)
        valid_rows = result['valid_rows']
        # Capturar errores de parseo ANTES de modificar la lista
        parse_errors = list(result['errors'])
        master_data = result.get('has_master_data', {})

        # ─── Sincronizar Tablas Maestras ──────────────────────────────────────
        # ─── Sincronizar Tablas Maestras ──────────────────────────────────────
        # 1. Oficinas
        for ofi in master_data.get('oficinas', []):
            OficinaOrg.objects.update_or_create(
                id_oficina=str(ofi['id']).strip(),
                defaults={
                    'nombre_oficina_origen': str(ofi['nombre']).strip() if ofi['nombre'] else f"Oficina {ofi['id']}"
                }
            )
        
        # 2. Asegurar oficinas referenciadas en las filas de rutas
        referenced_offices = set(str(row['id_oficina_id']) for row in valid_rows if row.get('id_oficina_id'))
        existing_offices = set(OficinaOrg.objects.filter(id_oficina__in=referenced_offices).values_list('id_oficina', flat=True))
        offices_to_create = [
            OficinaOrg(id_oficina=oid, nombre_oficina_origen=f"Oficina {oid} (Auto)")
            for oid in referenced_offices if oid not in existing_offices
        ]
        if offices_to_create:
            OficinaOrg.objects.bulk_create(offices_to_create)

        # 3. Prioridades
        for prio in master_data.get('priorities', []):
            PriorityRef.objects.update_or_create(
                priority=str(prio['id']).strip(),
                defaults={
                    'priority_name': str(prio['nombre']).strip() if prio['nombre'] else f"Prioridad {prio['id']}"
                }
            )

        # 4. Poblaciones
        for pob in master_data.get('poblaciones', []):
            PoblacionCor.objects.update_or_create(
                id_punto=str(pob['id']).strip(),
                defaults={
                    'ciudad': str(pob['ciudad']).strip() if pob['ciudad'] else '',
                    'lat_ref': Decimal(str(pob['lat'] or 0)),
                    'lon_ref': Decimal(str(pob['lon'] or 0)),
                }
            )

        # ─── Insertar Rutas Válidas (Optimizado con Bulk) ────────────────────
        imported = 0
        duplicates = 0
        service_errors = []

        # Obtener rutas existentes para evitar duplicados en memoria
        # Usamos un set de tuplas (origin, destination, start, end) como "firma" de la ruta
        existing_routes_signatures = set(
            Route.objects.values_list('origin', 'destination', 'time_window_start', 'time_window_end')
        )

        routes_to_create = []
        rows_to_process = []

        for row in valid_rows:
            signature = (row['origin'], row['destination'], row['time_window_start'], row['time_window_end'])
            
            if signature in existing_routes_signatures:
                duplicates += 1
                service_errors.append({
                    'row': None,
                    'field': 'duplicado',
                    'value': f"{row['origin']} → {row['destination']}",
                    'reason': 'Ruta duplicada: misma origen, destino y ventana horaria',
                })
                continue
            
            # Preparar objeto Route (sin guardar aún)
            route_obj = Route(
                id_route=row['id_route'],
                id_oficina_id=row.get('id_oficina_id'),
                origin=row['origin'],
                destination=row['destination'],
                distance_km=row['distance_km'],
                priority=row['priority'],
                time_window_start=row['time_window_start'],
                time_window_end=row['time_window_end'],
                status=row['status'],
                payload=row['payload'],
                created_at=row['created_at'],
            )
            routes_to_create.append(route_obj)
            rows_to_process.append(row)
            # Añadir a la firma para evitar duplicados dentro del mismo Excel
            existing_routes_signatures.add(signature)

        if routes_to_create:
            try:
                with transaction.atomic():
                    # 1. Insertar Rutas en bloque
                    created_routes = Route.objects.bulk_create(routes_to_create)
                    imported = len(created_routes)

                    # 2. Crear logs de éxito en bloque
                    logs_to_create = [
                        ExecutionLog(
                            route=route,
                            result='SUCCESS' if route.status in ('READY', 'PENDING', 'EXECUTED') else 'ERROR',
                            message=f"Ruta cargada en sistema. Estado inicial: {route.status}",
                        )
                        for route in created_routes
                    ]
                    ExecutionLog.objects.bulk_create(logs_to_create)
                    
                    for route in created_routes:
                        logger.info(f"Ruta {route.id_route} importada correctamente (bulk)")

            except Exception as e:
                logger.error(f"Error crítico en bulk_create: {e}")
                service_errors.append({
                    'row': None,
                    'field': 'db_error',
                    'value': 'BATCH',
                    'reason': f"Error crítico al guardar bloque de rutas: {str(e)}",
                })
                # En caso de error en el bloque, no marcamos ninguna como importada
                imported = 0

        # ─── Crear logs de auditoría para los errores de PARSEO ───────────────
        parse_logs = [
            ExecutionLog(
                route=None,
                result='ERROR',
                message=(
                    f"FALLO DE CARGA - Fila {err.get('row')}: "
                    f"Campo [{err.get('field')}] "
                    f"valor [{err.get('value')}] → {err.get('reason')}"
                ),
            )
            for err in parse_errors
        ]
        if parse_logs:
            ExecutionLog.objects.bulk_create(parse_logs)

        # Combinar todos los errores para el reporte
        all_errors = parse_errors + service_errors

        logger.info(
            f"Importación completada: {imported} importadas, "
            f"{duplicates} duplicadas/fallidas, "
            f"{len(parse_errors)} errores de validación"
        )

        return {
            'summary': {
                'total':      len(valid_rows) + len(parse_errors),
                'imported':   imported,
                'duplicates': duplicates,
                'errors':     len(parse_errors),
            },
            'errors': all_errors,
        }


class RouteExecutionService:

    @staticmethod
    def execute(route_ids):
        """
        Ejecuta una lista de rutas por su id_route (string).
        - Actualiza status a EXECUTED
        - Crea un ExecutionLog por cada ruta procesada
        - Reporta rutas no encontradas o ya ejecutadas
        """
        executed = []
        failed = []

        for route_id in route_ids:
            try:
                route = Route.objects.get(id_route=str(route_id))

                if route.status == 'EXECUTED':
                    failed.append({
                        'route_id': route_id,
                        'reason': 'La ruta ya fue ejecutada anteriormente',
                    })
                    ExecutionLog.objects.create(
                        route=route,
                        result='ERROR',
                        message='La ruta ya fue ejecutada anteriormente',
                    )
                    continue

                route.status = 'EXECUTED'
                route.save()

                ExecutionLog.objects.create(
                    route=route,
                    result='SUCCESS',
                    message='Ejecutada correctamente',
                )

                executed.append(route_id)
                logger.info(f"Ruta {route_id} ejecutada correctamente")

            except Route.DoesNotExist:
                failed.append({
                    'route_id': route_id,
                    'reason': 'Ruta no encontrada',
                })
                logger.warning(f"Ruta {route_id} no encontrada para ejecución")

            except Exception as e:
                failed.append({
                    'route_id': route_id,
                    'reason': str(e),
                })
                logger.error(f"Error ejecutando ruta {route_id}: {e}")

        return {
            'summary': {
                'total':    len(route_ids),
                'executed': len(executed),
                'failed':   len(failed),
            },
            'executed': executed,
            'failed':   failed,
        }