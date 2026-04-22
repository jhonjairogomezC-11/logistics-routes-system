from rest_framework import serializers
from .models import Route, ExecutionLog
from .utils import validate_coordinates


class ExecutionLogSerializer(serializers.ModelSerializer):
    """
    Serializer de solo lectura para los logs de ejecución.
    Usado en GET /routes/{id}/logs/
    """
    class Meta:
        model = ExecutionLog
        fields = ['id', 'route_id', 'execution_time', 'result', 'message']
        read_only_fields = fields


class RouteSerializer(serializers.ModelSerializer):
    """
    Serializer de lectura completa para listar rutas.
    Usado en GET /routes/ y GET /routes/{id}/
    Incluye los logs de ejecución anidados.
    """
    execution_logs = ExecutionLogSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = [
            'id', 'id_route', 'id_oficina_id',
            'origin', 'destination', 'distance_km',
            'priority', 'time_window_start', 'time_window_end',
            'status', 'payload', 'created_at', 'execution_logs'
        ]
        read_only_fields = ['id', 'created_at', 'execution_logs']


class RouteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer de escritura para creación individual de rutas.
    Usado en POST /routes/
    Implementa todas las validaciones de la prueba técnica — Pregunta #12.
    """
    class Meta:
        model = Route
        fields = [
            'id_route', 'id_oficina_id',
            'origin', 'destination', 'distance_km',
            'priority', 'time_window_start', 'time_window_end',
            'status', 'payload'
        ]

    # ── Validaciones de campo individual ──────────────────────────────────────

    def validate_origin(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El origen no puede estar vacío.")
        return value.strip()

    def validate_destination(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El destino no puede estar vacío.")
        return value.strip()

    def validate_distance_km(self, value):
        if value <= 0:
            raise serializers.ValidationError("La distancia debe ser mayor que 0.")
        return value

    def validate_priority(self, value):
        if value <= 0:
            raise serializers.ValidationError("La prioridad debe ser un entero positivo.")
        return value

    def validate_payload(self, value):
        """Valida coordenadas si el payload está presente."""
        if value:
            lat = value.get('latitud')
            lon = value.get('longitud')
            if lat is not None or lon is not None:
                coord_ok, coord_err = validate_coordinates(lat, lon)
                if not coord_ok:
                    raise serializers.ValidationError(
                        f"Coordenadas inválidas en payload: {coord_err}"
                    )
        return value

    # ── Validación cruzada entre campos ───────────────────────────────────────

    def validate(self, data):
        """
        Validaciones que involucran múltiples campos a la vez.
        Se ejecuta después de todas las validaciones individuales.
        """
        tw_start = data.get('time_window_start')
        tw_end = data.get('time_window_end')

        # Validar ventana horaria
        if tw_start and tw_end and tw_start >= tw_end:
            raise serializers.ValidationError({
                'time_window_end': 'Debe ser posterior a time_window_start.'
            })

        # Validar duplicado
        origin = data.get('origin')
        destination = data.get('destination')

        if origin and destination and tw_start and tw_end:
            exists = Route.objects.filter(
                origin=origin,
                destination=destination,
                time_window_start=tw_start,
                time_window_end=tw_end,
            ).exists()

            if exists:
                raise serializers.ValidationError(
                    'Ya existe una ruta con el mismo origen, destino y ventana horaria.'
                )

        return data


class RouteImportSerializer(serializers.Serializer):
    """
    Serializer para recibir el archivo Excel en POST /routes/import/
    Solo valida que el archivo exista y sea un .xlsx
    """
    file = serializers.FileField()

    def validate_file(self, value):
        if not value.name.endswith('.xlsx'):
            raise serializers.ValidationError(
                "Solo se aceptan archivos Excel con extensión .xlsx"
            )
        return value


class RouteExecuteSerializer(serializers.Serializer):
    """
    Serializer para recibir los IDs en POST /routes/execute/
    """
    route_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        error_messages={
            'min_length': 'Debe enviar al menos un ID de ruta para ejecutar.'
        }
    )