# apps/routes/views.py
import logging

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import RouteFilter
from .models import ExecutionLog, Route
from .serializers import (
    ExecutionLogSerializer,
    RouteCreateSerializer,
    RouteExecuteSerializer,
    RouteImportSerializer,
    RouteSerializer,
)
from .services import RouteExecutionService, RouteImportService

from .services import RouteExecutionService, RouteImportService

logger = logging.getLogger('apps.routes')


from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 1000

class RouteListCreateView(ListCreateAPIView):
    """
    GET  /api/routes/   → Lista paginada de rutas con filtros:
                          status, priority, origin, destination,
                          created_at_after, created_at_before
                          Ordenamiento: created_at, priority, distance_km, status
    POST /api/routes/   → Crea una ruta individual con todas las validaciones.
    """
    queryset = (
        Route.objects
        .select_related('id_oficina')
        .prefetch_related('execution_logs')
        .order_by('-created_at')
    )
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RouteFilter
    ordering_fields = ['created_at', 'priority', 'distance_km', 'status']
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RouteCreateSerializer
        return RouteSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RouteSerializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response({
                'success': True,
                'data': paginated_response.data,
            })
        serializer = RouteSerializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = RouteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        route = serializer.save(created_at=timezone.now())
        output = RouteSerializer(route)
        logger.info(f"Ruta {route.id_route} creada (pk={route.pk})")
        return Response(
            {'success': True, 'data': output.data},
            status=status.HTTP_201_CREATED,
        )


class RouteDetailView(RetrieveUpdateAPIView):
    """
    GET   /api/routes/<id_route>/   → Detalle completo de una ruta con sus logs.
    PUT   /api/routes/<id_route>/   → Actualización completa.
    PATCH /api/routes/<id_route>/   → Actualización parcial.
    """
    queryset = (
        Route.objects
        .select_related('id_oficina')
        .prefetch_related('execution_logs')
    )
    lookup_field = 'id_route'

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return RouteCreateSerializer
        return RouteSerializer

    def retrieve(self, request, *args, **kwargs):
        route = self.get_object()
        serializer = RouteSerializer(route)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        route = self.get_object()
        serializer = RouteCreateSerializer(route, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        route = serializer.save()
        output = RouteSerializer(route)
        logger.info(f"Ruta {route.id_route} actualizada (partial={partial})")
        return Response({'success': True, 'data': output.data})


class RouteLogsView(APIView):
    """
    GET /api/routes/<id_route>/logs/   → Historial de ejecuciones de una ruta.
    """

    def get(self, request, id_route):
        try:
            route = Route.objects.get(id_route=id_route)
        except Route.DoesNotExist:
            return Response(
                {
                    'success': False,
                    'error': {
                        'status_code': 404,
                        'detail': f'Ruta con id_route={id_route} no encontrada.',
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        logs = ExecutionLog.objects.filter(route=route).order_by('-execution_time')
        serializer = ExecutionLogSerializer(logs, many=True)
        return Response({'success': True, 'data': serializer.data})


class RouteImportView(APIView):
    """
    POST /api/routes/import/   → Importa rutas desde un archivo Excel (.xlsx).
    Body: multipart/form-data con campo 'file'.
    Retorna resumen de filas importadas, duplicadas y errores por fila.
    """
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = RouteImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        result = RouteImportService.process(file)
        return Response(
            {'success': True, 'data': result},
            status=status.HTTP_200_OK,
        )


class RouteExecuteView(APIView):
    """
    POST /api/routes/execute/   → Ejecuta una lista de rutas por id_route.
    Body JSON: { "route_ids": [1, 2, 3] }
    Actualiza el status a EXECUTED y crea un ExecutionLog por cada ruta.
    """

    def post(self, request):
        serializer = RouteExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        route_ids = serializer.validated_data['route_ids']
        result = RouteExecutionService.execute(route_ids)
        return Response(
            {'success': True, 'data': result},
            status=status.HTTP_200_OK,
        )
