# apps/routes/tests/test_views.py
import io
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.routes.models import ExecutionLog, Route


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_route(**kwargs):
    now = timezone.now()
    defaults = dict(
        id_route=1,
        origin='Bogotá',
        destination='Medellín',
        distance_km=Decimal('420.50'),
        priority=1,
        time_window_start=now,
        time_window_end=now + timedelta(hours=4),
        status='READY',
        created_at=now,
    )
    defaults.update(kwargs)
    return Route.objects.create(**defaults)


def route_payload(**kwargs):
    now = timezone.now()
    data = dict(
        id_route=10,
        origin='Bogotá',
        destination='Medellín',
        distance_km='420.50',
        priority=1,
        time_window_start=now.isoformat(),
        time_window_end=(now + timedelta(hours=4)).isoformat(),
        status='READY',
    )
    data.update(kwargs)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/routes/
# ─────────────────────────────────────────────────────────────────────────────

class RouteListViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('routes:route-list-create')

    def test_lista_vacia(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_lista_con_rutas(self):
        make_route(id_route=1)
        make_route(id_route=2, origin='Cali', destination='Pasto')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['count'], 2)

    def test_estructura_paginada(self):
        make_route()
        response = self.client.get(self.url)
        data = response.data['data']
        for key in ('count', 'next', 'previous', 'results'):
            self.assertIn(key, data)

    # ── Filtros ───────────────────────────────────────────────────────────────

    def test_filtro_status(self):
        make_route(id_route=1, status='READY')
        make_route(id_route=2, origin='X', destination='Y', status='EXECUTED')
        response = self.client.get(self.url, {'status': 'READY'})
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['status'], 'READY')

    def test_filtro_priority(self):
        make_route(id_route=1, priority=1)
        make_route(id_route=2, origin='X', destination='Y', priority=3)
        response = self.client.get(self.url, {'priority': 3})
        self.assertEqual(response.data['data']['count'], 1)

    def test_filtro_origin_icontains(self):
        make_route(id_route=1, origin='Bogotá Centro')
        make_route(id_route=2, origin='Cali Norte', destination='Pasto')
        response = self.client.get(self.url, {'origin': 'bogotá'})
        self.assertEqual(response.data['data']['count'], 1)

    def test_filtro_destination_icontains(self):
        make_route(id_route=1, destination='Medellín')
        make_route(id_route=2, origin='Cali', destination='Pasto')
        response = self.client.get(self.url, {'destination': 'med'})
        self.assertEqual(response.data['data']['count'], 1)

    def test_filtro_created_at_after(self):
        yesterday = timezone.now() - timedelta(days=1)
        make_route(id_route=1)  # creado ahora
        response = self.client.get(self.url, {'created_at_after': yesterday.isoformat()})
        self.assertEqual(response.data['data']['count'], 1)

    # ── Ordenamiento ──────────────────────────────────────────────────────────

    def test_ordenamiento_por_priority(self):
        make_route(id_route=1, priority=3)
        make_route(id_route=2, origin='X', destination='Y', priority=1)
        response = self.client.get(self.url, {'ordering': 'priority'})
        results = response.data['data']['results']
        self.assertLessEqual(results[0]['priority'], results[1]['priority'])


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/routes/
# ─────────────────────────────────────────────────────────────────────────────

class RouteCreateViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('routes:route-list-create')

    def test_crea_ruta_correctamente(self):
        response = self.client.post(self.url, route_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertTrue(Route.objects.filter(id_route=10).exists())

    def test_respuesta_incluye_datos_de_ruta(self):
        response = self.client.post(self.url, route_payload(), format='json')
        data = response.data['data']
        self.assertIn('id_route', data)
        self.assertEqual(data['id_route'], 10)

    def test_origin_vacio_retorna_400(self):
        response = self.client.post(self.url, route_payload(origin=''), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_distance_km_negativa_retorna_400(self):
        response = self.client.post(self.url, route_payload(distance_km='-1'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_priority_cero_retorna_400(self):
        response = self.client.post(self.url, route_payload(priority=0), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_time_window_invertida_retorna_400(self):
        now = timezone.now()
        data = route_payload(
            time_window_start=(now + timedelta(hours=4)).isoformat(),
            time_window_end=now.isoformat(),
        )
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ruta_duplicada_retorna_400(self):
        now = timezone.now()
        start = now
        end = now + timedelta(hours=4)
        Route.objects.create(
            id_route=99,
            origin='Bogotá', destination='Medellín',
            distance_km=Decimal('420.50'), priority=1,
            time_window_start=start, time_window_end=end,
            status='READY', created_at=now,
        )
        data = route_payload(
            id_route=100,
            time_window_start=start.isoformat(),
            time_window_end=end.isoformat(),
        )
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payload_coordenadas_invalidas_retorna_400(self):
        data = route_payload(payload={'latitud': 90.0, 'longitud': -74.0})
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/routes/<id_route>/
# ─────────────────────────────────────────────────────────────────────────────

class RouteDetailViewTest(APITestCase):

    def setUp(self):
        self.route = make_route(id_route=1)
        self.url = reverse('routes:route-detail', kwargs={'id_route': 1})

    def test_retorna_ruta(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['id_route'], 1)

    def test_incluye_execution_logs(self):
        ExecutionLog.objects.create(route=self.route, result='SUCCESS', message='OK')
        response = self.client.get(self.url)
        self.assertEqual(len(response.data['data']['execution_logs']), 1)

    def test_no_encontrada_retorna_404(self):
        url = reverse('routes:route-detail', kwargs={'id_route': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])


# ─────────────────────────────────────────────────────────────────────────────
# PUT /api/routes/<id_route>/
# ─────────────────────────────────────────────────────────────────────────────

class RouteUpdateViewTest(APITestCase):

    def setUp(self):
        self.route = make_route(id_route=1)
        self.url = reverse('routes:route-detail', kwargs={'id_route': 1})

    def test_actualiza_ruta_completa(self):
        now = timezone.now()
        data = route_payload(
            id_route=1,
            origin='Cali',
            destination='Pasto',
            distance_km='300.00',
            priority=2,
            status='PENDING',
            time_window_start=now.isoformat(),
            time_window_end=(now + timedelta(hours=3)).isoformat(),
        )
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.route.refresh_from_db()
        self.assertEqual(self.route.origin, 'Cali')
        self.assertEqual(self.route.status, 'PENDING')

    def test_actualizacion_invalida_retorna_400(self):
        data = route_payload(id_route=1, distance_km='-5')
        response = self.client.put(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_parcial(self):
        response = self.client.patch(self.url, {'status': 'PENDING'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.route.refresh_from_db()
        self.assertEqual(self.route.status, 'PENDING')

    def test_put_no_encontrada_retorna_404(self):
        url = reverse('routes:route-detail', kwargs={'id_route': 9999})
        response = self.client.put(url, route_payload(id_route=9999), format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/routes/<id_route>/logs/
# ─────────────────────────────────────────────────────────────────────────────

class RouteLogsViewTest(APITestCase):

    def setUp(self):
        self.route = make_route(id_route=1)
        self.url = reverse('routes:route-logs', kwargs={'id_route': 1})

    def test_logs_vacios(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data'], [])

    def test_retorna_logs_de_la_ruta(self):
        ExecutionLog.objects.create(route=self.route, result='SUCCESS', message='OK')
        ExecutionLog.objects.create(route=self.route, result='ERROR', message='Fallo')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']), 2)

    def test_logs_estructura_correcta(self):
        ExecutionLog.objects.create(route=self.route, result='SUCCESS', message='OK')
        response = self.client.get(self.url)
        log = response.data['data'][0]
        for field in ('id', 'route_id', 'execution_time', 'result', 'message'):
            self.assertIn(field, log)

    def test_ruta_inexistente_retorna_404(self):
        url = reverse('routes:route-logs', kwargs={'id_route': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    def test_no_retorna_logs_de_otras_rutas(self):
        other = make_route(id_route=2, origin='X', destination='Y')
        ExecutionLog.objects.create(route=other, result='SUCCESS', message='otro')
        response = self.client.get(self.url)
        self.assertEqual(response.data['data'], [])


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/routes/import/
# ─────────────────────────────────────────────────────────────────────────────

class RouteImportViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('routes:route-import')
        self.mock_result = {
            'summary': {'total': 3, 'imported': 2, 'duplicates': 1, 'errors': 1},
            'errors': [{'row': 2, 'field': 'origin', 'value': None, 'reason': 'vacío'}],
        }

    def _xlsx_file(self):
        return io.BytesIO(b'fake-xlsx-content')

    def test_archivo_no_xlsx_retorna_400(self):
        csv_file = io.BytesIO(b'col1,col2\n1,2')
        csv_file.name = 'rutas.csv'
        response = self.client.post(self.url, {'file': csv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sin_archivo_retorna_400(self):
        response = self.client.post(self.url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_importacion_exitosa(self):
        xlsx = self._xlsx_file()
        xlsx.name = 'rutas.xlsx'
        with patch('apps.routes.services.parse_excel', return_value={
            'valid_rows': [], 'errors': []
        }):
            response = self.client.post(self.url, {'file': xlsx}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_respuesta_incluye_summary(self):
        xlsx = self._xlsx_file()
        xlsx.name = 'rutas.xlsx'
        with patch('apps.routes.services.parse_excel', return_value={
            'valid_rows': [], 'errors': []
        }):
            response = self.client.post(self.url, {'file': xlsx}, format='multipart')
        self.assertIn('summary', response.data['data'])

    def test_respuesta_incluye_errors(self):
        xlsx = self._xlsx_file()
        xlsx.name = 'rutas.xlsx'
        with patch('apps.routes.services.parse_excel', return_value={
            'valid_rows': [], 'errors': []
        }):
            response = self.client.post(self.url, {'file': xlsx}, format='multipart')
        self.assertIn('errors', response.data['data'])


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/routes/execute/
# ─────────────────────────────────────────────────────────────────────────────

class RouteExecuteViewTest(APITestCase):

    def setUp(self):
        self.url = reverse('routes:route-execute')
        self.route = make_route(id_route=1, status='READY')

    def test_ejecuta_ruta_correctamente(self):
        response = self.client.post(self.url, {'route_ids': [1]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn(1, response.data['data']['executed'])

    def test_lista_vacia_retorna_400(self):
        response = self.client.post(self.url, {'route_ids': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_campo_ausente_retorna_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ruta_inexistente_en_failed(self):
        response = self.client.post(self.url, {'route_ids': [9999]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['failed']), 1)
        self.assertEqual(response.data['data']['failed'][0]['route_id'], 9999)

    def test_cambia_status_a_executed(self):
        self.client.post(self.url, {'route_ids': [1]}, format='json')
        self.route.refresh_from_db()
        self.assertEqual(self.route.status, 'EXECUTED')

    def test_respuesta_incluye_summary(self):
        response = self.client.post(self.url, {'route_ids': [1]}, format='json')
        summary = response.data['data']['summary']
        for key in ('total', 'executed', 'failed'):
            self.assertIn(key, summary)

    def test_mixto_exitoso_y_fallido(self):
        response = self.client.post(self.url, {'route_ids': [1, 9999]}, format='json')
        data = response.data['data']
        self.assertEqual(data['summary']['total'], 2)
        self.assertEqual(data['summary']['executed'], 1)
        self.assertEqual(data['summary']['failed'], 1)
