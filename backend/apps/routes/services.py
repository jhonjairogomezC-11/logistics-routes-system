from django.db import transaction
from .models import Route, ExecutionLog
from .utils import parse_excel
import logging

logger = logging.getLogger('apps.routes')


class RouteImportService:

    @staticmethod
    def process(file):
        """
        Procesa un archivo Excel de rutas.
        Crea automáticamente las oficinas faltantes para evitar errores de integridad.
        """
        from .models import OficinaOrg
        
        result = parse_excel(file)
        valid_rows = result['valid_rows']
        errors = result['errors']

        imported = 0
        duplicates = 0

        for row in valid_rows:
            try:
                # Usar un bloque atómico por cada fila para que un error no aborte todo
                with transaction.atomic():
                    # 1. Asegurar que la oficina existe
                    oficina_id = row.get('id_oficina_id')
                    if oficina_id:
                        OficinaOrg.objects.get_or_create(
                            id_oficina=oficina_id,
                            defaults={'nombre_oficina_origen': f"Oficina {oficina_id} (Auto)"}
                        )

                    # 2. Verificar duplicado
                    exists = Route.objects.filter(
                        origin=row['origin'],
                        destination=row['destination'],
                        time_window_start=row['time_window_start'],
                        time_window_end=row['time_window_end'],
                    ).exists()

                    if exists:
                        duplicates += 1
                        errors.append({
                            'row': None,
                            'field': 'duplicado',
                            'value': f"{row['origin']} → {row['destination']}",
                            'reason': 'Ruta duplicada: misma origen, destino y ventana horaria'
                        })
                        continue

                    # 3. Crear la ruta
                    Route.objects.create(
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

                    imported += 1
                    logger.info(f"Ruta {row['id_route']} importada correctamente")

            except Exception as e:
                duplicates += 1
                errors.append({
                    'row': None,
                    'field': 'db_error',
                    'value': row.get('id_route'),
                    'reason': f"Error en base de datos: {str(e)}"
                })
                logger.warning(f"Error al importar ruta {row.get('id_route')}: {e}")

        logger.info(f"Importación completada: {imported} importadas, {duplicates} duplicadas, {len(errors)} errores")

        return {
            'summary': {
                'total': imported + duplicates + len(result['errors']),
                'imported': imported,
                'duplicates': duplicates,
                'errors': len(errors),
            },
            'errors': errors
        }


class RouteExecutionService:

    @staticmethod
    def execute(route_ids):
        """
        Ejecuta una lista de rutas por su id_route.
        Actualiza status a EXECUTED y crea un ExecutionLog por cada una.
        """
        executed = []
        failed = []

        for route_id in route_ids:
            try:
                route = Route.objects.get(id_route=route_id)

                if route.status == 'EXECUTED':
                    failed.append({
                        'route_id': route_id,
                        'reason': 'La ruta ya fue ejecutada anteriormente'
                    })
                    ExecutionLog.objects.create(
                        route=route,
                        result='ERROR',
                        message='La ruta ya fue ejecutada anteriormente'
                    )
                    continue

                route.status = 'EXECUTED'
                route.save()

                ExecutionLog.objects.create(
                    route=route,
                    result='SUCCESS',
                    message='Ejecutada OK'
                )

                executed.append(route_id)
                logger.info(f"Ruta {route_id} ejecutada correctamente")

            except Route.DoesNotExist:
                failed.append({
                    'route_id': route_id,
                    'reason': 'Ruta no encontrada'
                })
                logger.warning(f"Ruta {route_id} no encontrada para ejecución")

            except Exception as e:
                failed.append({
                    'route_id': route_id,
                    'reason': str(e)
                })
                logger.error(f"Error ejecutando ruta {route_id}: {e}")

        return {
            'summary': {
                'total': len(route_ids),
                'executed': len(executed),
                'failed': len(failed),
            },
            'executed': executed,
            'failed': failed,
        }