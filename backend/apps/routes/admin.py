# apps/routes/admin.py
from django.contrib import admin
from .models import ExecutionLog, OficinaOrg, PoblacionCor, PriorityRef, Route


@admin.register(OficinaOrg)
class OficinaOrgAdmin(admin.ModelAdmin):
    list_display = ['id_oficina', 'nombre_oficina_origen']
    search_fields = ['nombre_oficina_origen']
    ordering = ['id_oficina']


@admin.register(PoblacionCor)
class PoblacionCorAdmin(admin.ModelAdmin):
    list_display = ['id_punto', 'ciudad', 'lat_ref', 'lon_ref']
    search_fields = ['ciudad']
    ordering = ['id_punto']


@admin.register(PriorityRef)
class PriorityRefAdmin(admin.ModelAdmin):
    list_display = ['priority', 'priority_name']
    ordering = ['priority']


class ExecutionLogInline(admin.TabularInline):
    model = ExecutionLog
    extra = 0
    readonly_fields = ['execution_time', 'result', 'message']
    can_delete = False


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = [
        'id_route', 'id_oficina', 'origin', 'destination',
        'distance_km', 'priority', 'status', 'created_at',
    ]
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['origin', 'destination', 'id_route']

    ordering = ['-created_at']
    readonly_fields = ['created_at']
    inlines = [ExecutionLogInline]
    fieldsets = (
        ('Identificación', {
            'fields': ('id_route', 'id_oficina')
        }),
        ('Ruta', {
            'fields': ('origin', 'destination', 'distance_km')
        }),
        ('Planificación', {
            'fields': ('priority', 'time_window_start', 'time_window_end', 'status')
        }),
        ('Datos adicionales', {
            'fields': ('payload', 'created_at'),
            'classes': ('collapse',),
        }),
    )


@admin.register(ExecutionLog)
class ExecutionLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'route', 'result', 'execution_time', 'message']
    list_filter = ['result', 'execution_time']
    search_fields = ['route__id_route', 'message']
    ordering = ['-execution_time']
    readonly_fields = ['route', 'execution_time', 'result', 'message']
