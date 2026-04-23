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
        Crea automáticamente las oficinas faltantes para evitar errores de integridad.
        """
        from .models import OficinaOrg, PriorityRef, PoblacionCor
        
        result = parse_excel(file)
        valid_rows = result['valid_rows']
        errors = result['errors']
        master_data = result.get('has_master_data', {})

        # ─── Sincronizar Tablas Maestras ───
        # 1. Oficinas (ID y Nombre real)
        for ofi in master_data.get('oficinas', []):
            OficinaOrg.objects.update_or_create(
                id_oficina=ofi['id'],
                defaults={'nombre_oficina_origen': str(ofi['nombre']).strip() or f"Oficina {ofi['id']}"}
            )
        
        # 2. Prioridades (ID y Nombre descriptivo)
        for prio in master_data.get('priorities', []):
            PriorityRef.objects.update_or_create(
                priority=prio['id'],
                defaults={'priority_name': str(prio['nombre']).strip() or f"Prioridad {prio['id']}"}
            )

        # 3. Poblaciones / Puntos (ID, Ciudad y Coordenadas de referencia)
        for pob in master_data.get('poblaciones', []):
            PoblacionCor.objects.update_or_create(
                id_punto=pob['id'],
                defaults={
                    'ciudad': str(pob['ciudad']).strip(),
                    'lat_ref': Decimal(str(pob['lat'] or 0)),
                    'lon_ref': Decimal(str(pob['lon'] or 0)),
                }
            )

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
                    
                    # 4. Crear log inicial para TODAS las rutas (Traceability total)
                    ExecutionLog.objects.create(
                        route=route_obj,
                        result='SUCCESS' if route_obj.status in ['READY', 'PENDING', 'EXECUTED'] else 'ERROR',
                        message=f"Ruta cargada en sistema. Estado inicial: {route_obj.status}"
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

        # 5. Registrar errores de PARSEO (los que no llegaron a ser valid_rows)
        for err in result['errors']:
            ExecutionLog.objects.create(
                route=None,
                result='ERROR',
                message=f"FALLO DE CARGA - Fila {err.get('row')}: Campo [{err.get('field')}] valor [{err.get('value')}] -> {err.get('reason')}"
            )

        logger.info(f"Importación completada: {imported} importadas, {duplicates} duplicadas, {len(errors)} errores")

        return {
            'summary': {
                'total': imported + duplicates + len(errors),
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