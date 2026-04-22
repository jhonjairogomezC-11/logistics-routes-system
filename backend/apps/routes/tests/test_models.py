# apps/routes/tests/test_models.py
from django.test import TestCase
from django.utils import timezone
from django.db import IntegrityError

from apps.routes.models import ExecutionLog, OficinaOrg, PoblacionCor, PriorityRef, Route


class OficinaOrgModelTest(TestCase):

    def setUp(self):
        self.oficina = OficinaOrg.objects.create(
            id_oficina=1,
            nombre_oficina_origen='Oficina Bogotá'
        )

    def test_str(self):
        self.assertEqual(str(self.oficina), 'Oficina Bogotá')

    def test_id_oficina_unique(self):
        with self.assertRaises(IntegrityError):
            OficinaOrg.objects.create(id_oficina=1, nombre_oficina_origen='Duplicada')

    def test_campos(self):
        self.assertEqual(self.oficina.id_oficina, 1)
        self.assertEqual(self.oficina.nombre_oficina_origen, 'Oficina Bogotá')


class PoblacionCorModelTest(TestCase):

    def setUp(self):
        self.punto = PoblacionCor.objects.create(
            id_punto=10,
            ciudad='Medellín',
            lat_ref='6.25184000',
            lon_ref='-75.56359000',
        )

    def test_str(self):
        self.assertEqual(str(self.punto), 'Medellín (10)')

    def test_id_punto_unique(self):
        with self.assertRaises(IntegrityError):
            PoblacionCor.objects.create(
                id_punto=10, ciudad='Otra', lat_ref='0', lon_ref='0'
            )

    def test_campos(self):
        self.assertEqual(self.punto.ciudad, 'Medellín')


class PriorityRefModelTest(TestCase):

    def setUp(self):
        self.priority = PriorityRef.objects.create(priority=1, priority_name='Alta')

    def test_str(self):
        self.assertEqual(str(self.priority), 'Alta')

    def test_priority_unique(self):
        with self.assertRaises(IntegrityError):
            PriorityRef.objects.create(priority=1, priority_name='Duplicada')


class RouteModelTest(TestCase):

    def setUp(self):
        self.oficina = OficinaOrg.objects.create(
            id_oficina=1,
            nombre_oficina_origen='Oficina Principal'
        )
        self.route = Route.objects.create(
            id_route=100,
            id_oficina=self.oficina,
            origin='Bogotá',
            destination='Medellín',
            distance_km='420.50',
            priority=1,
            time_window_start=timezone.now(),
            time_window_end=timezone.now() + timezone.timedelta(hours=4),
            status='READY',
            created_at=timezone.now(),
        )

    def test_str(self):
        self.assertIn('100', str(self.route))
        self.assertIn('Bogotá', str(self.route))
        self.assertIn('Medellín', str(self.route))

    def test_id_route_unique(self):
        with self.assertRaises(IntegrityError):
            Route.objects.create(
                id_route=100,
                origin='Cali',
                destination='Pasto',
                distance_km='300.00',
                priority=2,
                time_window_start=timezone.now(),
                time_window_end=timezone.now() + timezone.timedelta(hours=2),
                status='PENDING',
                created_at=timezone.now(),
            )

    def test_unique_route_constraint(self):
        """No puede existir otra ruta con mismo origin, destination y ventana horaria."""
        start = self.route.time_window_start
        end = self.route.time_window_end
        with self.assertRaises(IntegrityError):
            Route.objects.create(
                id_route=999,
                origin='Bogotá',
                destination='Medellín',
                distance_km='420.50',
                priority=1,
                time_window_start=start,
                time_window_end=end,
                status='PENDING',
                created_at=timezone.now(),
            )

    def test_status_choices(self):
        self.assertIn(self.route.status, ['READY', 'PENDING', 'EXECUTED', 'FAILED'])

    def test_payload_nullable(self):
        self.assertIsNone(self.route.payload)

    def test_id_oficina_fk(self):
        self.assertEqual(self.route.id_oficina.id_oficina, 1)

    def test_execution_logs_related_name(self):
        self.assertEqual(self.route.execution_logs.count(), 0)


class ExecutionLogModelTest(TestCase):

    def setUp(self):
        self.route = Route.objects.create(
            id_route=200,
            origin='Cali',
            destination='Barranquilla',
            distance_km='1100.00',
            priority=2,
            time_window_start=timezone.now(),
            time_window_end=timezone.now() + timezone.timedelta(hours=6),
            status='EXECUTED',
            created_at=timezone.now(),
        )
        self.log = ExecutionLog.objects.create(
            route=self.route,
            result='SUCCESS',
            message='Ejecutada OK',
        )

    def test_str(self):
        self.assertIn(str(self.log.id), str(self.log))
        self.assertIn('SUCCESS', str(self.log))

    def test_execution_time_auto(self):
        self.assertIsNotNone(self.log.execution_time)

    def test_result_choices(self):
        self.assertIn(self.log.result, ['SUCCESS', 'ERROR'])

    def test_cascade_delete(self):
        """Al eliminar la ruta, sus logs deben eliminarse en cascada."""
        log_id = self.log.id
        self.route.delete()
        self.assertFalse(ExecutionLog.objects.filter(id=log_id).exists())

    def test_related_name(self):
        self.assertEqual(self.route.execution_logs.count(), 1)
        self.assertEqual(self.route.execution_logs.first().result, 'SUCCESS')
