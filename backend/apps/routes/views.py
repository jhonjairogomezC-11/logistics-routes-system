# apps/routes/views.py
import logging

from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView, ListAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

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

logger = logging.getLogger('apps.routes')


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000


class RouteListCreateView(ListCreateAPIView):
    """
    GET  /api/routes/  → Lista paginada de rutas con filtros.
    POST /api/routes/  → Crea una ruta individual.
    """
    permission_classes = [IsAuthenticated]
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


class RouteDetailView(RetrieveUpdateAPIView):
    """
    GET   /api/routes/<id_route>/ → Detalle de una ruta.
    PATCH /api/routes/<id_route>/ → Actualización parcial.
    """
    permission_classes = [IsAuthenticated]
    queryset = Route.objects.all()
    serializer_class = RouteSerializer
    lookup_field = 'id_route'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})


class RouteImportView(APIView):
    """
    POST /api/routes/import/ → Sube un archivo Excel y procesa las rutas.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        serializer = RouteImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']

        result = RouteImportService.process(file)
        return Response({'success': True, 'data': result}, status=status.HTTP_201_CREATED)


class RouteLogsView(APIView):
    """
    GET /api/routes/<id_route>/logs/ → Historial de ejecución de una ruta específica.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, id_route):
        logs = ExecutionLog.objects.filter(
            route__id_route=str(id_route)
        ).order_by('-execution_time')
        serializer = ExecutionLogSerializer(logs, many=True)
        return Response({'success': True, 'data': serializer.data})


class RouteExecuteView(APIView):
    """
    POST /api/routes/execute/ → Ejecuta una lista de rutas por sus IDs.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RouteExecuteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        route_ids = serializer.validated_data['route_ids']
        result = RouteExecutionService.execute(route_ids)
        return Response({'success': True, 'data': result}, status=status.HTTP_200_OK)


class GlobalExecutionLogListView(ListAPIView):
    """
    GET /api/logs/ → Auditoría global de logs paginada.
    """
    permission_classes = [IsAuthenticated]
    queryset = ExecutionLog.objects.select_related('route').order_by('-execution_time')
    serializer_class = ExecutionLogSerializer
    pagination_class = StandardResultsSetPagination

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            return Response({'success': True, 'data': paginated_response.data})
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


class DashboardStatsView(APIView):
    """
    GET /api/dashboard/stats/ → Estadísticas del dashboard en una sola consulta.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Una sola consulta agrupada por status
        counts_qs = Route.objects.values('status').annotate(total=Count('id'))
        counts = {item['status']: item['total'] for item in counts_qs}

        data = {
            'total':    Route.objects.count(),
            'ready':    counts.get('READY', 0),
            'pending':  counts.get('PENDING', 0),
            'executed': counts.get('EXECUTED', 0),
            'failed':   counts.get('FAILED', 0),
        }

        return Response({'success': True, 'data': data})
