"""Lectores de extractos. Reconocen el formato por el CONTENIDO del archivo, no por el nombre.

Cada lector devuelve filas con el esquema de comunes.py. Si un archivo no se puede leer con certeza, el
lector lo informa (avisos) y NO adivina: el paso de verificacion del saldo corrido es la red de seguridad.

Lectores:
  tabla        xls / xlsx / csv con encabezados (Galicia, Macro, Hipotecario, Brubank, y la mayoria de bancos)
  pdf_*        PDFs de texto: galicia_office, galicia_resumen, hipotecario, y uno generico de baja confianza
Para un banco nuevo casi siempre alcanza `tabla`; si no, ver references/agregar_un_banco.md.
"""
import csv
import html
import os
import re
import unicodedata

from .comunes import CERO, a_fecha, a_numero, orientar

BANCOS_COMUNES = ['Macro', 'Galicia', 'Hipotecario', 'Brubank', 'Santander', 'BBVA', 'Nacion', 'Provincia',
                  'Ciudad', 'ICBC', 'Credicoop', 'Patagonia', 'Supervielle', 'HSBC', 'Itau', 'Mercado Pago',
                  'Uala', 'Naranja X', 'Comafi', 'Bind', 'Banco Nación']


def norm(s):
    s = unicodedata.normalize('NFD', str(s)).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', s)


# ---------------------------------------------------------------- banco y cuenta
def detectar_banco(ruta, muestra, cfg):
    texto = (ruta + ' ' + muestra).lower()
    for regla in cfg.get('bancos', []):
        if regla['contiene'].lower() in ruta.lower():
            return regla['banco']
    base = os.path.basename(ruta).lower()
    for b in cfg.get('bancos_conocidos', []) + BANCOS_COMUNES:
        if norm(b) in norm(base):
            return b
    for b in cfg.get('bancos_conocidos', []) + BANCOS_COMUNES:
        if norm(b) in norm(ruta):
            return b
    for b in cfg.get('bancos_conocidos', []) + BANCOS_COMUNES:
        if b.lower() in texto:
            return b
    return 'Banco sin identificar'


def asignar_cuenta(banco, ruta, detectada, cfg):
    """Aplica las reglas de la configuracion (primera que coincide). Si ninguna, usa la detectada;
    si no hay, '(sin identificar)' para que se pregunte, no se adivine."""
    for r in cfg.get('cuentas', []):
        if r.get('banco') and norm(r['banco']) != norm(banco):
            continue
        if 'contiene_archivo' in r and r['contiene_archivo'].lower() not in ruta.lower():
            continue
        if 'contiene_cuenta' in r and r['contiene_cuenta'].lower() not in (detectada or '').lower():
            continue
        return r['cuenta'], r.get('solapa')
    return (detectada or '(sin identificar)'), None


# ---------------------------------------------------------------- lector de tablas
def _filas_crudas(path):
    ext = path.lower().rsplit('.', 1)[-1]
    if ext == 'xls':
        import xlrd
        s = xlrd.open_workbook(path).sheet_by_index(0)
        return [s.row_values(i) for i in range(s.nrows)]
    if ext == 'xlsx':
        import openpyxl
        wb = openpyxl.load_workbook(path, data_only=True)
        for ws in wb.worksheets:
            filas = [list(r) for r in ws.iter_rows(values_only=True)]
            if filas:
                return filas
        return []
    if ext in ('csv', 'txt'):
        raw = open(path, 'rb').read()
        try:
            texto = raw.decode('utf-8-sig')
        except UnicodeDecodeError:
            texto = raw.decode('latin-1')
        try:
            delim = csv.Sniffer().sniff(texto[:4096], delimiters=';,\t|').delimiter
        except csv.Error:
            delim = ';'
        return [r for r in csv.reader(texto.splitlines(), delimiter=delim)]
    return []


def _mapear(encabezado):
    """encabezado: lista de textos. Devuelve {campo: indice} y lista de columnas extra."""
    m, usados = {}, set()
    normas = [norm(c) if c not in (None, '') else '' for c in encabezado]

    def buscar(campo, pred):
        for i, n in enumerate(normas):
            if n and i not in usados and campo not in m and pred(n):
                m[campo] = i
                usados.add(i)
                return
    buscar('fecha', lambda n: n.startswith('fecha') and 'alta' not in n and 'modi' not in n)
    buscar('descripcion', lambda n: n.startswith('descripcion'))
    if 'descripcion' not in m:
        buscar('descripcion', lambda n: n in ('concepto', 'detalle', 'movimiento', 'leyenda'))
    buscar('debito', lambda n: n.startswith('debit') or n in ('debe', 'montodebe', 'retiros', 'egresos'))
    buscar('credito', lambda n: n.startswith('credit') or n in ('haber', 'montohaber', 'depositos', 'ingresos'))
    buscar('saldo', lambda n: n.startswith('saldo'))
    buscar('importe', lambda n: n in ('importe', 'monto'))
    buscar('referencia', lambda n: 'referencia' in n or 'comprobante' in n or n in ('nro', 'numero'))
    buscar('cuenta', lambda n: n in ('cuenta', 'tipodecuenta'))
    extras = [i for i, n in enumerate(normas) if n and i not in usados and not n.startswith('moneda')]
    return m, extras


def _buscar_encabezado(filas):
    for i, fila in enumerate(filas[:60]):
        m, _ = _mapear(fila)
        if 'fecha' in m and ('saldo' in m or 'importe' in m or ('debito' in m and 'credito' in m)):
            return i, m
    return None, None


def _cuenta_en_cabecera(filas, hasta):
    tipo, numero = '', ''
    for fila in filas[:hasta]:
        celdas = [str(c).strip() for c in fila if c not in (None, '')]
        for j, c in enumerate(celdas):
            n = norm(c)
            if n in ('numero', 'nrodecuenta', 'ncuenta', 'numerodecuenta', 'nrocuenta') and j + 1 < len(celdas):
                numero = celdas[j + 1]
            if re.match(r'(cuenta|caja de ahorro)', c.lower()) and len(celdas) == 1 and not tipo:
                tipo = c.title()
    return (tipo + ' ' + numero).strip()


def leer_tabla(path, cfg=None):
    filas_c = _filas_crudas(path)
    i, m = _buscar_encabezado(filas_c)
    if i is None:
        return None
    enc = filas_c[i]
    _, extras = _mapear(enc)
    det_cuenta = _cuenta_en_cabecera(filas_c, i)
    salida, avisos, saltadas = [], [], 0
    for n, fila in enumerate(filas_c[i + 1:], start=i + 2):
        def cel(campo):
            k = m.get(campo)
            return fila[k] if k is not None and k < len(fila) else None
        f = a_fecha(cel('fecha'))
        if f is None:
            continue
        deb = cred = None
        if 'debito' in m or 'credito' in m:
            deb, cred = a_numero(cel('debito')), a_numero(cel('credito'))
            deb = abs(deb) if deb is not None else None
            cred = abs(cred) if cred is not None else None
        elif 'importe' in m:
            imp = a_numero(cel('importe'))
            if imp is not None:
                deb, cred = (-imp, None) if imp < 0 else (None, imp)
        if deb is None and cred is None:
            saltadas += 1
            continue
        det = []
        for k in extras:
            v = fila[k] if k < len(fila) else None
            if v not in (None, ''):
                if hasattr(v, 'strftime'):
                    v = v.strftime('%d/%m/%Y')
                elif isinstance(v, float) and v == int(v):
                    v = int(v)
                det.append(f'{enc[k]}: {v}'.strip())
        if 'cuenta' in m and not det_cuenta and cel('cuenta'):
            det_cuenta = str(cel('cuenta')).strip()
        ref = cel('referencia')
        salida.append(dict(
            fecha=f, descripcion=str(cel('descripcion') or '').strip(), detalle=' | '.join(det),
            referencia='' if ref is None else (str(int(ref)) if isinstance(ref, float) and ref == int(ref) else str(ref).strip()),
            debito=deb or CERO, credito=cred or CERO, saldo=a_numero(cel('saldo')), fila=n))
    if saltadas:
        avisos.append(f'{saltadas} filas con fecha pero sin importe (saldos iniciales, totales); no se cargaron')
    return dict(formato='tabla', cuenta=det_cuenta, filas=orientar(salida), avisos=avisos)


# ---------------------------------------------------------------- PDFs
def _lineas_pdf(path):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        return [ln for pg in pdf.pages for ln in (pg.extract_text() or '').splitlines()]


def _fila(fecha, desc, detalle, deb, cred, saldo, n):
    return dict(fecha=fecha, descripcion=desc.strip(), detalle=detalle, referencia='',
                debito=deb, credito=cred, saldo=saldo, fila=n)


RE_OFFICE = re.compile(r'^(\d\d/\d\d/\d{4}) (.*) ([+-]) \$ ([\d.]+,\d\d) \$ (-?[\d.]+,\d\d)$')
RE_RESUMEN = re.compile(r'^(\d\d/\d\d/\d\d) (.*?) (-?[\d.]+,\d\d) (-?[\d.]+,\d\d-?)$')
RE_HIPO = re.compile(r'^(\d\d/\d\d/\d{4})\s*(.*?)\s*(-?\d+\.\d\d)\s+(-?\d+\.\d\d)$')
BASURA_HIPO = re.compile(r'^(Movimientos del|\(cid|IMPORTE_MON|FECHA DESCRIP|EDA$|Total:|El presente documento|correspondiente ser)')


def _pdf_office(lineas):
    filas, cuenta, cur = [], '', None
    for ln in lineas:
        m = RE_OFFICE.match(ln)
        if m:
            f, desc, sg, imp, sal = m.groups()
            imp = a_numero(imp)
            cur = _fila(a_fecha(f), desc, [], imp if sg == '-' else CERO, imp if sg == '+' else CERO,
                        a_numero(sal), len(filas) + 1)
            filas.append(cur)
        elif ln.startswith('Movimientos de CC'):
            cuenta, cur = 'CC ' + ln.split('$')[-1].strip(), None
        elif cur is not None and not re.match(r'^(Office Banking|CBU:|Fecha Descripci|P[aá]gina|\d+ ?/ ?\d+$)', ln):
            cur['detalle'].append(ln.strip())
    for f in filas:
        f['detalle'] = ' | '.join(f['detalle'])
    return cuenta, filas


def _pdf_resumen(lineas):
    filas, cuenta, cur = [], '', None
    for ln in lineas:
        m = re.search(r'N° (\d{7}-\d \d{3}-\d)', ln)
        if m:
            cuenta = 'CC ' + m.group(1)
    for ln in lineas:
        m = RE_RESUMEN.match(ln)
        if m:
            f, desc, imp, sal = m.groups()
            imp = a_numero(imp)
            cur = _fila(a_fecha(f), desc, [], -imp if imp < 0 else CERO, imp if imp > 0 else CERO,
                        a_numero(sal), len(filas) + 1)
            filas.append(cur)
        elif cur is not None and not re.match(r'^(Resumen de Cuenta|Fecha Descripci|\d{10,}[A-Z]?$|Saldo final|Total)', ln):
            cur['detalle'].append(ln.strip())
    for f in filas:
        f['detalle'] = ' | '.join(f['detalle'])
    return cuenta, filas


def _pdf_hipotecario(lineas):
    cuenta = ''
    for ln in lineas:
        m = re.search(r'(CTE|CA)\s*\$?\s*\*+(\d+)', ln)
        if m:
            cuenta = f'{m.group(1)} ****{m.group(2)}'
    lineas = [l.strip() for l in lineas if l.strip() and not BASURA_HIPO.match(l.strip())]
    base = []
    for i, ln in enumerate(lineas):
        m = RE_HIPO.match(ln)
        if m:
            base.append(dict(i=i, fecha=a_fecha(m.group(1)), desc=m.group(2).strip(),
                             imp=a_numero(m.group(3)), saldo=a_numero(m.group(4))))
    es_fila, usado, filas = {f['i'] for f in base}, set(), []
    for n, f in enumerate(base):
        partes, armada = ([f['desc']] if f['desc'] else []), False
        if not f['desc']:
            armada = True
            if f['i'] > 0 and (f['i'] - 1) not in es_fila and (f['i'] - 1) not in usado:
                partes.insert(0, lineas[f['i'] - 1]); usado.add(f['i'] - 1)
            j = f['i'] + 1
            if j < len(lineas) and j not in es_fila and j not in usado:
                sig = base[n + 1] if n + 1 < len(base) else None
                if sig is None or sig['desc']:
                    partes.append(lineas[j]); usado.add(j)
        filas.append(_fila(f['fecha'], ' '.join(partes), 'descripcion armada de varias lineas del PDF' if armada else '',
                           -f['imp'] if f['imp'] < 0 else CERO, f['imp'] if f['imp'] > 0 else CERO, f['saldo'], n + 1))
    return cuenta, filas


def _pdf_generico(lineas):
    """Baja confianza: linea que empieza con fecha y termina en importe + saldo. El signo del importe se toma
    del propio texto; si el PDF no lo trae, el control de saldo corrido lo va a delatar."""
    filas = []
    for ln in lineas:
        m = re.match(r'^(\d\d[/-]\d\d[/-]\d{2,4})\s+(.*?)\s+(-?\$?\s?-?[\d.,]+\d)\s+(-?\$?\s?-?[\d.,]+\d-?)$', ln)
        if not m:
            continue
        f, desc, imp, sal = m.groups()
        imp, sal, f = a_numero(imp), a_numero(sal), a_fecha(f)
        if imp is None or f is None:
            continue
        filas.append(_fila(f, desc, 'PDF generico: signo tomado del texto', -imp if imp < 0 else CERO,
                           imp if imp > 0 else CERO, sal, len(filas) + 1))
    return '', filas


def leer_pdf(path):
    lineas = _lineas_pdf(path)
    texto = '\n'.join(lineas[:40])
    if 'Office Banking' in texto and 'Movimientos de CC' in texto:
        formato, (cuenta, filas) = 'pdf_galicia_office', _pdf_office(lineas)
    elif 'Resumen de Cuenta Corriente' in texto:
        formato, (cuenta, filas) = 'pdf_galicia_resumen', _pdf_resumen(lineas)
    elif 'IMPORTE_MON' in texto or re.search(r'Movimientos del \d\d/\d\d/\d{4} al', texto):
        formato, (cuenta, filas) = 'pdf_hipotecario', _pdf_hipotecario(lineas)
    else:
        formato, (cuenta, filas) = 'pdf_generico', _pdf_generico(lineas)
    avisos = ['formato PDF generico (baja confianza): revisar contra el banco'] if formato == 'pdf_generico' else []
    if not filas:
        avisos.append('no se pudo leer ninguna fila (PDF escaneado o formato nuevo)')
    return dict(formato=formato, cuenta=cuenta, filas=orientar(filas), avisos=avisos)


# ---------------------------------------------------------------- despacho
def leer_archivo(path, ruta_rel, cfg):
    """Devuelve dict(banco, cuenta, solapa, formato, filas, avisos) o None si no es un extracto soportado."""
    ext = path.lower().rsplit('.', 1)[-1]
    if ext == 'pdf':
        r = leer_pdf(path)
    elif ext in ('xls', 'xlsx', 'csv', 'txt'):
        r = leer_tabla(path, cfg)
        if r is None:
            return dict(banco='?', cuenta='', solapa=None, formato='no reconocido', filas=[],
                        avisos=['no se encontro un encabezado con fecha/debito/credito/saldo'])
    else:
        return None
    banco = detectar_banco(ruta_rel, '', cfg)
    cuenta, solapa = asignar_cuenta(banco, ruta_rel, r['cuenta'], cfg)
    r.update(banco=banco, cuenta=cuenta, solapa=solapa)
    return r


# ---------------------------------------------------------------- libro mayor (fuente secundaria)
def leer_mayor(path, desde=None, hasta=None):
    """Lee el CSV del libro mayor de una cuenta bancaria exportado de un sistema contable
    (Cuenta;Fecha;Comprobante;CUIT;Razon Social;Concepto;Monto Debe;Monto Haber;Saldo;...).
    OJO: NO es un extracto del banco. Desde el lado del banco, Haber = debito y Debe = credito.
    El saldo del mayor es acumulado desde el inicio de lo exportado: no es el saldo bancario.
    Las entidades HTML (&#243;) se decodifican ANTES de separar por ';' (contienen un ';' y partian las filas).
    Se leen los campos de derecha a izquierda porque el concepto puede traer ';'.
    Devuelve dict(cuenta_mayor, filas, excluidas, avisos). `excluidas` = filas fuera de [desde, hasta]."""
    raw = open(path, 'rb').read()
    try:
        texto = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        texto = raw.decode('latin-1')
    texto = html.unescape(texto)
    cuenta, filas, excluidas, avisos = '', [], [], []
    for n, ln in enumerate(texto.splitlines(), start=1):
        p = ln.split(';')
        if p[0] and p[0].strip().lower() != 'cuenta':
            cuenta = p[0].strip()
            continue
        if len(p) < 14 or not re.match(r'\d\d/\d\d/\d{4}$', p[1].strip()):
            continue
        f = a_fecha(p[1])
        concepto = ';'.join(p[5:-9]).strip()
        razon, cuit, comp = p[4].strip(), p[3].strip(), p[2].strip()
        debe, haber, saldo = a_numero(p[-9]), a_numero(p[-8]), a_numero(p[-7])
        det = ' | '.join(x for x in (razon, f'CUIT {cuit}' if cuit else '', f'Comprobante {comp}' if comp else '') if x)
        fila = dict(fecha=f, descripcion=concepto or razon, detalle=det, referencia=comp,
                    debito=haber or CERO, credito=debe or CERO, saldo=saldo, fila=n,
                    alta=p[-4].strip())
        if (desde and f < desde) or (hasta and f > hasta):
            excluidas.append(fila)
        else:
            filas.append(fila)
    if not filas:
        avisos.append('no se encontro ninguna fila del mayor dentro del periodo')
    return dict(cuenta_mayor=cuenta, filas=filas, excluidas=excluidas, avisos=avisos)
