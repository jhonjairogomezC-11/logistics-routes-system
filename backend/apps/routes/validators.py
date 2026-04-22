# apps/routes/validators.py
from django.core.exceptions import ValidationError


def validate_positive(value):
    """
    Valida que un campo numérico sea estrictamente positivo.
    Usar en modelos: validators=[validate_positive]
    """
    if value is not None and value <= 0:
        raise ValidationError(f"El valor debe ser mayor que 0. Se recibió: {value}")


def validate_status_choice(value):
    """
    Valida que el status sea uno de los valores permitidos.
    """
    valid = {'READY', 'PENDING', 'EXECUTED', 'FAILED'}
    if value not in valid:
        raise ValidationError(
            f"Estado inválido: '{value}'. Los valores permitidos son: {', '.join(sorted(valid))}"
        )


def validate_time_window(start, end):
    """
    Valida que time_window_end sea posterior a time_window_start.
    Uso: llamar desde Model.clean() o desde un serializer.
    """
    if start and end and start >= end:
        raise ValidationError(
            "time_window_end debe ser posterior a time_window_start."
        )


def validate_colombia_coordinates(lat, lon):
    """
    Valida que las coordenadas estén dentro del rango geográfico de Colombia.
    Wrapper compatible con Django ValidationError sobre la función de utils.
    Uso: llamar desde Model.clean() o directamente.
    """
    from .utils import validate_coordinates
    ok, error_msg = validate_coordinates(lat, lon)
    if not ok:
        raise ValidationError(f"Coordenadas inválidas: {error_msg}")
