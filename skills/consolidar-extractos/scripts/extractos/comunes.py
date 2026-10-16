"""Utilidades comunes: numeros, fechas, esquema de fila, lectura/escritura de CSV y config.

Esquema de un movimiento (dict):
  banco, cuenta, fecha (date), descripcion, detalle, referencia,
  debito (Decimal >= 0), credito (Decimal >= 0), saldo (Decimal | None),
  archivo (ruta relativa a la entrada), fila (posicion en el archivo)
"""
import csv
import datetime
import hashlib
import json
import os
import re
from decimal import Decimal, InvalidOperation

CERO = Decimal('0')
TOL = Decimal('0.02')       # tolerancia al comparar saldos (centavos)

FORMATOS_FECHA = ('%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%Y-%m-%d', '%d.%m.%Y', '%d.%m.%y')


def a_numero(valor):
    """Convierte numeros de Excel o texto ('1.234,56', '$ 1,234.56', '- $ 10', '36.427,00-', '(5)') a Decimal.
    Devuelve None si esta vacio o es un guion."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return Decimal(str(valor))
    if isinstance(valor, Decimal):
        return valor
    t = str(valor).strip()
    if t in ('', '-', '--'):
        return None
    neg = t.startswith('-') or t.endswith('-') or (t.startswith('(') and t.endswith(')'))
    t = re.sub(r'[^\d,.]', '', t)
    if not t:
        return None
    if ',' in t and '.' in t:
        dec = ',' if t.rfind(',') > t.rfind('.') else '.'
    elif ',' in t:
        dec = ',' if re.search(r',\d{1,2}$', t) and t.count(',') == 1 else None
    elif '.' in t:
        dec = '.' if re.search(r'\.\d{1,2}$', t) and t.count('.') == 1 else None
    else:
        dec = None
    if dec == ',':
        t = t.replace('.', '').replace(',', '.')
    elif dec == '.':
        t = t.replace(',', '')
    else:
        t = t.replace('.', '').replace(',', '')
    try:
        v = Decimal(t)
    except InvalidOperation:
        return None
    return -v if neg else v


def a_fecha(valor, datemode=0):
    """date | datetime | serial de Excel | texto -> date (o None si no es una fecha)."""
    if valor is None or valor == '':
        return None
    if isinstance(valor, datetime.datetime):
        return valor.date()
    if isinstance(valor, datetime.date):
        return valor
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        if 20000 < valor < 80000:
            return (datetime.datetime(1899, 12, 30) + datetime.timedelta(days=float(valor))).date()
        return None
    t = str(valor).strip()
    for f in FORMATOS_FECHA:
        try:
            return datetime.datetime.strptime(t, f).date()
        except ValueError:
            pass
    return None


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for bloque in iter(lambda: f.read(1 << 20), b''):
            h.update(bloque)
    return h.hexdigest()


def errores_de_saldo(filas):
    """Cuenta cuantas filas consecutivas no cumplen saldo_anterior + credito - debito = saldo."""
    n = 0
    for a, b in zip(filas, filas[1:]):
        if a['saldo'] is None or b['saldo'] is None:
            continue
        if abs(a['saldo'] + b['credito'] - b['debito'] - b['saldo']) > TOL:
            n += 1
    return n


def orientar(filas):
    """Deja las filas de lo viejo a lo nuevo. Si el archivo viene al reves (el banco lista lo mas nuevo
    primero) lo detecta por el saldo corrido o, si no hay saldo, por las fechas. No inventa nada."""
    if len(filas) < 2:
        return filas
    asc, desc = errores_de_saldo(filas), errores_de_saldo(filas[::-1])
    if asc != desc:
        return filas if asc < desc else filas[::-1]
    if filas[0]['fecha'] > filas[-1]['fecha']:
        return filas[::-1]
    return filas


# ---------------------------------------------------------------- CSV de trabajo
COLUMNAS = ['banco', 'cuenta', 'fecha', 'descripcion', 'detalle', 'referencia', 'debito', 'credito',
            'saldo', 'archivo', 'fila', 'nota']


def escribir_movimientos(path, filas):
    with open(path, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNAS, extrasaction='ignore', delimiter=';')
        w.writeheader()
        for r in filas:
            w.writerow({k: ('' if r.get(k) is None else r.get(k, '')) for k in COLUMNAS})


def leer_movimientos(path):
    with open(path, encoding='utf-8-sig', newline='') as fh:
        filas = list(csv.DictReader(fh, delimiter=';'))
    for r in filas:
        r['fecha'] = datetime.date.fromisoformat(r['fecha'])
        r['debito'] = Decimal(r['debito'] or '0')
        r['credito'] = Decimal(r['credito'] or '0')
        r['saldo'] = Decimal(r['saldo']) if r['saldo'] != '' else None
        r['fila'] = int(r['fila']) if r.get('fila') not in (None, '') else 0
    return filas


def escribir_tabla(path, filas, columnas):
    with open(path, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.DictWriter(fh, fieldnames=columnas, extrasaction='ignore', delimiter=';')
        w.writeheader()
        w.writerows(filas)


# ---------------------------------------------------------------- configuracion
def cargar_config(path):
    with open(path, encoding='utf-8') as fh:
        cfg = json.load(fh)
    for k in ('empresa', 'entrada', 'salida'):
        if not cfg.get(k):
            raise SystemExit(f'Falta "{k}" en la configuracion {path}')
    cfg.setdefault('cuit', '')
    cfg.setdefault('idioma', 'es')
    cfg.setdefault('cuentas', [])
    cfg.setdefault('bancos', [])
    cfg.setdefault('formatos_extra', [])
    cfg['trabajo'] = os.path.join(cfg['salida'], 'trabajo')
    return cfg
