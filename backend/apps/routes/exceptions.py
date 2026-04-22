import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('apps.routes')


def custom_exception_handler(exc, context):
    # Primero dejar que DRF maneje lo que conoce
    response = exception_handler(exc, context)

    if response is not None:
        # DRF ya lo manejó — estandarizar el formato
        response.data = {
            'success': False,
            'error': {
                'status_code': response.status_code,
                'detail': response.data,
            }
        }
        logger.warning(f"API error {response.status_code}: {exc}")
    else:
        # Error no manejado por DRF — error inesperado del servidor
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        response = Response(
            {
                'success': False,
                'error': {
                    'status_code': 500,
                    'detail': 'Error interno del servidor. Por favor contacte al administrador.',
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response