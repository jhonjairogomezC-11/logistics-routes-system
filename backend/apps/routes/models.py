# apps/routes/models.py
from django.db import models


class OficinaOrg(models.Model):
    id_oficina = models.IntegerField(unique=True)
    nombre_oficina_origen = models.CharField(max_length=100)

    class Meta:
        db_table = 'oficina_org'

    def __str__(self):
        return self.nombre_oficina_origen


class PoblacionCor(models.Model):
    id_punto = models.IntegerField(unique=True)
    ciudad = models.CharField(max_length=100)
    lat_ref = models.DecimalField(max_digits=12, decimal_places=8)
    lon_ref = models.DecimalField(max_digits=12, decimal_places=8)

    class Meta:
        db_table = 'poblacion_cor'

    def __str__(self):
        return f"{self.ciudad} ({self.id_punto})"


class PriorityRef(models.Model):
    priority = models.IntegerField(unique=True)
    priority_name = models.CharField(max_length=20)

    class Meta:
        db_table = 'priorities_ref'

    def __str__(self):
        return self.priority_name


class Route(models.Model):
    STATUS_CHOICES = [
        ('READY', 'Ready'),
        ('PENDING', 'Pending'),
        ('EXECUTED', 'Executed'),
        ('FAILED', 'Failed'),
    ]

    id_route = models.IntegerField(unique=True)
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
    payload = models.JSONField(null=True, blank=True)  # payload normalizado
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
    RESULT_CHOICES = [
        ('SUCCESS', 'Success'),
        ('ERROR', 'Error'),
    ]

    route = models.ForeignKey(
        Route,
        to_field='id_route',
        on_delete=models.CASCADE,
        related_name='execution_logs'
    )
    execution_time = models.DateTimeField(auto_now_add=True)
    result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    message = models.TextField(blank=True)

    class Meta:
        db_table = 'execution_logs'

    def __str__(self):
        return f"Log {self.id} - Route {self.route_id} - {self.result}"