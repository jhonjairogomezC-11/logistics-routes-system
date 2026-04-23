# apps/routes/models.py
from django.db import models


class OficinaOrg(models.Model):
    """Catálogo de oficinas origen del dataset."""
    id_oficina = models.CharField(max_length=50, unique=True)
    nombre_oficina_origen = models.CharField(max_length=200)

    class Meta:
        db_table = 'oficina_org'

    def __str__(self):
        return self.nombre_oficina_origen


class PoblacionCor(models.Model):
    """Puntos geográficos de referencia (ciudades/municipios)."""
    id_punto = models.CharField(max_length=50, unique=True)
    ciudad = models.CharField(max_length=200)
    lat_ref = models.DecimalField(max_digits=12, decimal_places=8)
    lon_ref = models.DecimalField(max_digits=12, decimal_places=8)

    class Meta:
        db_table = 'poblacion_cor'

    def __str__(self):
        return f"{self.ciudad} ({self.id_punto})"


class PriorityRef(models.Model):
    """Catálogo de prioridades de ruta."""
    priority = models.CharField(max_length=50, unique=True)
    priority_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'priorities_ref'

    def __str__(self):
        return self.priority_name


class Route(models.Model):
    """Ruta logística principal."""
    STATUS_CHOICES = [
        ('READY', 'Ready'),
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('FAILED', 'Failed'),
    ]

    # PK autoincremental de Postgres — nunca viene del Excel
    # id (BigAutoField) es generado automáticamente por Django

    # ID externo del dataset (puede ser alfanumérico)
    id_route = models.CharField(max_length=50, unique=True)

    id_oficina = models.ForeignKey(
        OficinaOrg,
        to_field='id_oficina',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='id_oficina'
    )
    origin = models.CharField(max_length=500)
    destination = models.CharField(max_length=500)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2)
    priority = models.IntegerField()
    time_window_start = models.DateTimeField()
    time_window_end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'routes'
        constraints = [
            models.UniqueConstraint(
                fields=['origin', 'destination', 'time_window_start', 'time_window_end'],
                name='unique_route'
            )
        ]

    def __str__(self):
        return f"Route {self.id_route}: {self.origin} → {self.destination}"


class ExecutionLog(models.Model):
    """Registro de auditoría de ejecuciones y cargas."""
    RESULT_CHOICES = [
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
    ]

    route = models.ForeignKey(
        Route,
        to_field='id_route',
        on_delete=models.CASCADE,
        related_name='execution_logs',
        null=True,
        blank=True
    )
    execution_time = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    message = models.TextField(blank=True)

    class Meta:
        db_table = 'execution_logs'

    def __str__(self):
        return f"Log {self.id} - Route {self.route_id} - {self.result}"