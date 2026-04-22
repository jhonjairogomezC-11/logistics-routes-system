# apps/routes/tests/test_serializers.py
from django.test import TestCase
from django.utils import timezone
from unittest.mock import MagicMock

from apps.routes.models import ExecutionLog, OficinaOrg, Route
from apps.routes.serializers import (
    ExecutionLogSerializer,
    RouteCreateSerializer,
    RouteExecuteSerializer,
    RouteImportSerializer,
    RouteSerializer,
)


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


def base_payload(**kwargs):
    """Helper: payload base válido para RouteCreateSerializer."""
    now = timezone.now()
    data = dict(
        id_route=10,
        origin='Bogotá',
        destination='Medellín',
        distance_km='420.50',
        priority=1,
        time_window_start=now.isoformat(),
        time_window_end=(now + timezone.timedelta(hours=4)).isoformat(),
        status='READY',
    )
    data.update(kwargs)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# ExecutionLogSerializer
# ─────────────────────────────────────────────────────────────────────────────

class ExecutionLogSerializerTest(TestCase):

    def setUp(self):
        self.route = make_route()
        self.log = ExecutionLog.objects.create(
            route=self.route, result='SUCCESS', message='OK'
        )

    def test_campos_presentes(self):
        data = ExecutionLogSerializer(self.log).data
        for field in ['id', 'route_id', 'execution_time', 'result', 'message']:
            self.assertIn(field, data)

    def test_es_solo_lectura(self):
        """El serializer no debe procesar datos de entrada (los ignora)."""
        data = {'result': 'ERROR', 'message': 'test'}
        s = ExecutionLogSerializer(data=data)
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data, {})  # Los campos read-only se descartan


# ─────────────────────────────────────────────────────────────────────────────
# RouteSerializer
# ─────────────────────────────────────────────────────────────────────────────

class RouteSerializerTest(TestCase):

    def setUp(self):
        self.route = make_route()
        ExecutionLog.objects.create(route=self.route, result='SUCCESS', message='OK')

    def test_campos_presentes(self):
        data = RouteSerializer(self.route).data
        for field in [
            'id', 'id_route', 'origin', 'destination', 'distance_km',
            'priority', 'status', 'created_at', 'execution_logs',
        ]:
            self.assertIn(field, data)

    def test_logs_anidados(self):
        data = RouteSerializer(self.route).data
        self.assertEqual(len(data['execution_logs']), 1)
        self.assertEqual(data['execution_logs'][0]['result'], 'SUCCESS')


# ─────────────────────────────────────────────────────────────────────────────
# RouteCreateSerializer — validaciones individuales
# ─────────────────────────────────────────────────────────────────────────────

class RouteCreateSerializerFieldValidationTest(TestCase):

    def _get_errors(self, **kwargs):
        s = RouteCreateSerializer(data=base_payload(**kwargs))
        s.is_valid()
        return s.errors

    # origin ──────────────────────────────────────────────────────────────────

    def test_origin_vacio(self):
        errors = self._get_errors(origin='')
        self.assertIn('origin', errors)

    def test_origin_solo_espacios(self):
        errors = self._get_errors(origin='   ')
        self.assertIn('origin', errors)

    def test_origin_valido_strip(self):
        s = RouteCreateSerializer(data=base_payload(origin='  Cali  '))
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data['origin'], 'Cali')

    # destination ─────────────────────────────────────────────────────────────

    def test_destination_vacio(self):
        errors = self._get_errors(destination='')
        self.assertIn('destination', errors)

    def test_destination_solo_espacios(self):
        errors = self._get_errors(destination='   ')
        self.assertIn('destination', errors)

    # distance_km ─────────────────────────────────────────────────────────────

    def test_distance_km_cero(self):
        errors = self._get_errors(distance_km=0)
        self.assertIn('distance_km', errors)

    def test_distance_km_negativa(self):
        errors = self._get_errors(distance_km=-10)
        self.assertIn('distance_km', errors)

    def test_distance_km_valida(self):
        s = RouteCreateSerializer(data=base_payload(distance_km='0.01'))
        self.assertTrue(s.is_valid(), s.errors)

    # priority ────────────────────────────────────────────────────────────────

    def test_priority_cero(self):
        errors = self._get_errors(priority=0)
        self.assertIn('priority', errors)

    def test_priority_negativa(self):
        errors = self._get_errors(priority=-5)
        self.assertIn('priority', errors)

    def test_priority_valida(self):
        s = RouteCreateSerializer(data=base_payload(priority=1))
        self.assertTrue(s.is_valid(), s.errors)

    # payload — coordenadas ───────────────────────────────────────────────────

    def test_payload_coordenadas_invalidas(self):
        """Latitud fuera del rango de Colombia."""
        errors = self._get_errors(payload={'latitud': 90.0, 'longitud': -74.0})
        self.assertIn('payload', errors)

    def test_payload_longitud_invalida(self):
        """Longitud fuera del rango de Colombia."""
        errors = self._get_errors(payload={'latitud': 4.7, 'longitud': -10.0})
        self.assertIn('payload', errors)

    def test_payload_coordenadas_validas(self):
        s = RouteCreateSerializer(
            data=base_payload(payload={'latitud': 4.7110, 'longitud': -74.0721})
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_payload_sin_coordenadas(self):
        """Payload sin lat/lon no debe fallar."""
        s = RouteCreateSerializer(
            data=base_payload(payload={'id_punto': 5, 'direccion': 'Calle 1'})
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_payload_none(self):
        s = RouteCreateSerializer(data=base_payload(payload=None))
        self.assertTrue(s.is_valid(), s.errors)


# ─────────────────────────────────────────────────────────────────────────────
# RouteCreateSerializer — validaciones cruzadas
# ─────────────────────────────────────────────────────────────────────────────

class RouteCreateSerializerCrossValidationTest(TestCase):

    def test_time_window_end_anterior_a_start(self):
        now = timezone.now()
        data = base_payload(
            time_window_start=(now + timezone.timedelta(hours=4)).isoformat(),
            time_window_end=now.isoformat(),
        )
        s = RouteCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('time_window_end', s.errors)

    def test_time_window_igual(self):
        now = timezone.now()
        data = base_payload(
            time_window_start=now.isoformat(),
            time_window_end=now.isoformat(),
        )
        s = RouteCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn('time_window_end', s.errors)

    def test_ruta_duplicada(self):
        """No debe permitir crear una ruta con mismo origin, destination y ventana."""
        now = timezone.now()
        start = now
        end = now + timezone.timedelta(hours=4)
        Route.objects.create(
            id_route=50,
            origin='Bogotá',
            destination='Cali',
            distance_km='460.00',
            priority=1,
            time_window_start=start,
            time_window_end=end,
            status='READY',
            created_at=now,
        )
        data = base_payload(
            id_route=51,
            origin='Bogotá',
            destination='Cali',
            time_window_start=start.isoformat(),
            time_window_end=end.isoformat(),
        )
        s = RouteCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        # El error no-field viene en non_field_errors
        self.assertTrue(
            s.errors.get('non_field_errors') or any(
                'duplicada' in str(v).lower() or 'existe' in str(v).lower()
                for v in s.errors.values()
            )
        )

    def test_datos_validos_completos(self):
        s = RouteCreateSerializer(data=base_payload())
        self.assertTrue(s.is_valid(), s.errors)


# ─────────────────────────────────────────────────────────────────────────────
# RouteImportSerializer
# ─────────────────────────────────────────────────────────────────────────────

class RouteImportSerializerTest(TestCase):

    def _mock_file(self, name):
        f = MagicMock()
        f.name = name
        return f

    def test_archivo_no_xlsx(self):
        s = RouteImportSerializer(data={'file': self._mock_file('rutas.csv')})
        self.assertFalse(s.is_valid())
        self.assertIn('file', s.errors)

    def test_archivo_xlsx_valido(self):
        s = RouteImportSerializer(data={'file': self._mock_file('rutas.xlsx')})
        self.assertTrue(s.is_valid(), s.errors)

    def test_archivo_ausente(self):
        s = RouteImportSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('file', s.errors)


# ─────────────────────────────────────────────────────────────────────────────
# RouteExecuteSerializer
# ─────────────────────────────────────────────────────────────────────────────

class RouteExecuteSerializerTest(TestCase):

    def test_lista_vacia(self):
        s = RouteExecuteSerializer(data={'route_ids': []})
        self.assertFalse(s.is_valid())
        self.assertIn('route_ids', s.errors)

    def test_campo_ausente(self):
        s = RouteExecuteSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn('route_ids', s.errors)

    def test_lista_valida(self):
        s = RouteExecuteSerializer(data={'route_ids': [1, 2, 3]})
        self.assertTrue(s.is_valid(), s.errors)

    def test_un_elemento(self):
        s = RouteExecuteSerializer(data={'route_ids': [99]})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valores_no_enteros(self):
        s = RouteExecuteSerializer(data={'route_ids': ['abc', 'xyz']})
        self.assertFalse(s.is_valid())
        self.assertIn('route_ids', s.errors)
