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
        for ofi in master_data.get('oficinas', []):
            OficinaOrg.objects.update_or_create(
                id_oficina=str(ofi['id']).strip(),
                defaults={
                    'nombre_oficina_origen': str(ofi['nombre']).strip() if ofi['nombre'] else f"Oficina {ofi['id']}"
                }
            )

        for prio in master_data.get('priorities', []):
            PriorityRef.objects.update_or_create(
                priority=str(prio['id']).strip(),
                defaults={
                    'priority_name': str(prio['nombre']).strip() if prio['nombre'] else f"Prioridad {prio['id']}"
                }
            )

        for pob in master_data.get('poblaciones', []):
            PoblacionCor.objects.update_or_create(
                id_punto=str(pob['id']).strip(),
                defaults={
                    'ciudad': str(pob['ciudad']).strip() if pob['ciudad'] else '',
                    'lat_ref': Decimal(str(pob['lat'] or 0)),
                    'lon_ref': Decimal(str(pob['lon'] or 0)),
                }
            )

        # ─── Insertar Rutas Válidas ───────────────────────────────────────────
        imported = 0
        duplicates = 0
        service_errors = []  # errores detectados durante la inserción

        for row in valid_rows:
            try:
                with transaction.atomic():
                    # Asegurar que la oficina existe si hay referencia
                    oficina_id = row.get('id_oficina_id')
                    if oficina_id:
                        OficinaOrg.objects.get_or_create(
                            id_oficina=str(oficina_id),
                            defaults={'nombre_oficina_origen': f"Oficina {oficina_id} (Auto)"}
                        )

                    # Verificar duplicado por clave de negocio
                    exists = Route.objects.filter(
                        origin=row['origin'],
                        destination=row['destination'],
                        time_window_start=row['time_window_start'],
                        time_window_end=row['time_window_end'],
                    ).exists()

                    if exists:
                        duplicates += 1
                        service_errors.append({
                            'row': None,
                            'field': 'duplicado',
                            'value': f"{row['origin']} → {row['destination']}",
                            'reason': 'Ruta duplicada: misma origen, destino y ventana horaria',
                        })
                        continue

                    # Crear la ruta
                    route_obj = Route.objects.create(
                        id_route=row['id_route'],
                        id_oficina_id=oficina_id,
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

                    # Log de carga inicial (trazabilidad completa)
                    ExecutionLog.objects.create(
                        route=route_obj,
                        result='SUCCESS' if route_obj.status in ('READY', 'PENDING', 'EXECUTED') else 'ERROR',
                        message=f"Ruta cargada en sistema. Estado inicial: {route_obj.status}",
                    )

                    imported += 1
                    logger.info(f"Ruta {row['id_route']} importada correctamente")

            except Exception as e:
                duplicates += 1
                service_errors.append({
                    'row': None,
                    'field': 'db_error',
                    'value': row.get('id_route'),
                    'reason': f"Error en base de datos: {str(e)}",
                })
                logger.warning(f"Error al importar ruta {row.get('id_route')}: {e}")

        # ─── Crear logs de auditoría para los errores de PARSEO ───────────────
        for err in parse_errors:
            ExecutionLog.objects.create(
                route=None,
                result='ERROR',
                message=(
                    f"FALLO DE CARGA - Fila {err.get('row')}: "
                    f"Campo [{err.get('field')}] "
                    f"valor [{err.get('value')}] → {err.get('reason')}"
                ),
            )

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