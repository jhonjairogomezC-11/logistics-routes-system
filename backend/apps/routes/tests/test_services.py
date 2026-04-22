# apps/routes/tests/test_services.py
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.routes.models import ExecutionLog, Route
from apps.routes.services import RouteExecutionService, RouteImportService


def make_route(**kwargs):
    """Helper: crea una ruta con valores por defecto."""
    defaults = dict(
        id_route=1,
        origin='Bogotá',
        destination='Medellín',
        distance_km='420.50',
        priority=1,
        time_window_start=timezone.now(),
        time_window_end=timezone.now() + timezone.timedelta(hours=4),
        status='READY',
        created_at=timezone.now(),
    )
    defaults.update(kwargs)
    return Route.objects.create(**defaults)


def valid_row(**kwargs):
    """Helper: fila válida de Excel parseada."""
    now = datetime.now()
    row = dict(
        id_route=100,
        id_oficina_id=None,
        origin='Bogotá',
        destination='Cali',
        distance_km=Decimal('460.00'),
        priority=1,
        time_window_start=now,
        time_window_end=now.replace(hour=now.hour + 2 if now.hour < 22 else 23),
        status='READY',
        payload=None,
        created_at=now,
    )
    row.update(kwargs)
    return row


# ─────────────────────────────────────────────────────────────────────────────
# RouteImportService
# ─────────────────────────────────────────────────────────────────────────────

class RouteImportServiceTest(TestCase):

    def _run(self, valid_rows, errors=None):
        """Helper: ejecuta el servicio con parse_excel mockeado."""
        if errors is None:
            errors = []
        mock_result = {'valid_rows': valid_rows, 'errors': list(errors)}
        with patch('apps.routes.services.parse_excel', return_value=mock_result):
            return RouteImportService.process(file=None)

    # ── Estructura del resultado ──────────────────────────────────────────────

    def test_resultado_tiene_summary_y_errors(self):
        result = self._run(valid_rows=[])
        self.assertIn('summary', result)
        self.assertIn('errors', result)

    def test_summary_tiene_campos_esperados(self):
        result = self._run(valid_rows=[])
        for key in ('total', 'imported', 'duplicates', 'errors'):
            self.assertIn(key, result['summary'])

    # ── Importación exitosa ───────────────────────────────────────────────────

    def test_importa_fila_valida(self):
        result = self._run(valid_rows=[valid_row()])
        self.assertEqual(result['summary']['imported'], 1)
        self.assertEqual(result['summary']['duplicates'], 0)
        self.assertTrue(Route.objects.filter(id_route=100).exists())

    def test_importa_multiples_filas(self):
        rows = [
            valid_row(id_route=101, origin='A', destination='B'),
            valid_row(id_route=102, origin='C', destination='D'),
            valid_row(id_route=103, origin='E', destination='F'),
        ]
        result = self._run(valid_rows=rows)
        self.assertEqual(result['summary']['imported'], 3)
        self.assertEqual(Route.objects.count(), 3)

    # ── Detección de duplicados ───────────────────────────────────────────────

    def test_duplicado_no_se_importa(self):
        """Si ya existe una ruta con mismo origin/destination/ventana, no importar."""
        now = datetime.now()
        start = now
        end = now.replace(hour=now.hour + 2 if now.hour < 22 else 23)

        # Crear ruta existente
        Route.objects.create(
            id_route=200,
            origin='Bogotá',
            destination='Cali',
            distance_km=Decimal('460.00'),
            priority=1,
            time_window_start=start,
            time_window_end=end,
            status='READY',
            created_at=now,
        )

        row = valid_row(
            id_route=201,
            origin='Bogotá',
            destination='Cali',
            time_window_start=start,
            time_window_end=end,
        )
        result = self._run(valid_rows=[row])
        self.assertEqual(result['summary']['imported'], 0)
        self.assertEqual(result['summary']['duplicates'], 1)
        # Solo debe existir la original
        self.assertEqual(Route.objects.filter(origin='Bogotá', destination='Cali').count(), 1)

    def test_duplicado_agrega_error_en_lista(self):
        """El duplicado debe registrarse en la lista de errors del resultado."""
        now = datetime.now()
        start = now
        end = now.replace(hour=now.hour + 2 if now.hour < 22 else 23)
        Route.objects.create(
            id_route=300,
            origin='X', destination='Y',
            distance_km=Decimal('100.00'),
            priority=1,
            time_window_start=start, time_window_end=end,
            status='READY', created_at=now,
        )
        row = valid_row(id_route=301, origin='X', destination='Y',
                        time_window_start=start, time_window_end=end)
        result = self._run(valid_rows=[row])
        self.assertTrue(len(result['errors']) > 0)
        self.assertEqual(result['errors'][-1]['field'], 'duplicado')

    # ── Errores de parse pasados por parse_excel ──────────────────────────────

    def test_errores_previos_se_incluyen_en_resultado(self):
        prev_errors = [
            {'row': 2, 'field': 'origin', 'value': None, 'reason': 'vacío'},
            {'row': 3, 'field': 'distance_km', 'value': -1, 'reason': 'negativo'},
        ]
        result = self._run(valid_rows=[], errors=prev_errors)
        self.assertGreaterEqual(result['summary']['errors'], 2)

    def test_sin_filas_validas_no_crea_rutas(self):
        result = self._run(valid_rows=[])
        self.assertEqual(result['summary']['imported'], 0)
        self.assertEqual(Route.objects.count(), 0)


# ─────────────────────────────────────────────────────────────────────────────
# RouteExecutionService
# ─────────────────────────────────────────────────────────────────────────────

class RouteExecutionServiceTest(TestCase):

    def setUp(self):
        self.route = make_route(id_route=1, status='READY')

    # ── Estructura del resultado ──────────────────────────────────────────────

    def test_resultado_tiene_summary(self):
        result = RouteExecutionService.execute([1])
        self.assertIn('summary', result)
        for key in ('total', 'executed', 'failed'):
            self.assertIn(key, result['summary'])

    def test_resultado_tiene_executed_y_failed(self):
        result = RouteExecutionService.execute([1])
        self.assertIn('executed', result)
        self.assertIn('failed', result)

    # ── Ejecución exitosa ─────────────────────────────────────────────────────

    def test_ejecuta_ruta_correctamente(self):
        result = RouteExecutionService.execute([1])
        self.assertIn(1, result['executed'])
        self.assertEqual(result['summary']['executed'], 1)
        self.assertEqual(result['summary']['failed'], 0)

    def test_cambia_status_a_executed(self):
        RouteExecutionService.execute([1])
        self.route.refresh_from_db()
        self.assertEqual(self.route.status, 'EXECUTED')

    def test_crea_log_success(self):
        RouteExecutionService.execute([1])
        log = ExecutionLog.objects.get(route=self.route)
        self.assertEqual(log.result, 'SUCCESS')

    # ── Ruta no encontrada ────────────────────────────────────────────────────

    def test_ruta_inexistente(self):
        result = RouteExecutionService.execute([9999])
        self.assertEqual(result['summary']['executed'], 0)
        self.assertEqual(result['summary']['failed'], 1)
        self.assertEqual(result['failed'][0]['route_id'], 9999)
        self.assertIn('no encontrada', result['failed'][0]['reason'].lower())

    def test_ruta_inexistente_no_crea_log(self):
        RouteExecutionService.execute([9999])
        self.assertEqual(ExecutionLog.objects.count(), 0)

    # ── Ruta ya ejecutada ─────────────────────────────────────────────────────

    def test_ruta_ya_ejecutada(self):
        self.route.status = 'EXECUTED'
        self.route.save()
        result = RouteExecutionService.execute([1])
        self.assertEqual(result['summary']['executed'], 0)
        self.assertEqual(result['summary']['failed'], 1)
        self.assertIn('ya fue ejecutada', result['failed'][0]['reason'].lower())

    def test_ruta_ya_ejecutada_crea_log_error(self):
        self.route.status = 'EXECUTED'
        self.route.save()
        RouteExecutionService.execute([1])
        log = ExecutionLog.objects.get(route=self.route)
        self.assertEqual(log.result, 'ERROR')

    # ── Resultados mixtos ─────────────────────────────────────────────────────

    def test_mixto_una_ok_una_no_encontrada(self):
        result = RouteExecutionService.execute([1, 9999])
        self.assertEqual(result['summary']['total'], 2)
        self.assertEqual(result['summary']['executed'], 1)
        self.assertEqual(result['summary']['failed'], 1)

    def test_multiples_rutas_exitosas(self):
        make_route(id_route=2, origin='Cali', destination='Pasto', status='READY')
        make_route(id_route=3, origin='Pereira', destination='Armenia', status='READY')
        result = RouteExecutionService.execute([1, 2, 3])
        self.assertEqual(result['summary']['executed'], 3)
        self.assertEqual(result['summary']['failed'], 0)
        self.assertEqual(ExecutionLog.objects.filter(result='SUCCESS').count(), 3)

    def test_summary_total_correcto(self):
        result = RouteExecutionService.execute([1, 9999, 8888])
        self.assertEqual(result['summary']['total'], 3)
