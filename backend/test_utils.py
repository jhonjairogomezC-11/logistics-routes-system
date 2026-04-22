import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.routes.utils import parse_excel

with open('data/dataset2.xlsx', 'rb') as f:
    result = parse_excel(f)

print(f" Válidas: {len(result['valid_rows'])}")
print(f" Errores: {len(result['errors'])}")
print("\nPrimeros 3 errores:")
for e in result['errors'][:3]:
    print(f"  Fila {e['row']} | {e['field']} | {e['value']} | {e['reason']}")
print("\nPrimera fila válida:")
print(result['valid_rows'][0])