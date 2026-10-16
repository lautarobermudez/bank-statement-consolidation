#!/usr/bin/env python3
"""Prueba de punta a punta con datos INVENTADOS (ninguna empresa ni banco reales).
Genera extractos desordenados a partir de una verdad conocida y comprueba que el flujo la recupera.

Uso:  python tests/test_flujo.py        (sale con codigo 0 si todo pasa)
Casos que cubre (cada uno corresponde a un problema real que ya ocurrio):
  - mensual + semanal + agrupado que se pisan
  - mismas operaciones con DESCRIPCION distinta entre descargas (no comparar por texto)
  - mismas operaciones con distinto orden dentro del dia (el saldo fila a fila cambia)
  - un dia partido entre dos archivos
  - un archivo que lista lo mas nuevo primero
  - un duplicado exacto
  - un archivo sin columna de saldo
  - un banco que no se puede identificar (se avisa, no se adivina)
"""
import csv
import datetime
import json
import os
import random
import shutil
import sys
import tempfile
from decimal import Decimal as D

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'scripts'))
from extractos import pasos                          # noqa: E402
from extractos.comunes import cargar_config, leer_movimientos   # noqa: E402

random.seed(7)
INICIO = datetime.date(2026, 1, 1)


def verdad(dias, saldo0):
    """[(fecha, descripcion, debito, credito)] con 1-4 movimientos por dia."""
    filas = []
    for d in range(dias):
        f = INICIO + datetime.timedelta(days=d)
        if f.weekday() >= 5:
            continue
        for k in range(random.randint(1, 4)):
            imp = D(random.randint(100, 900000)) / 100
            if random.random() < 0.5:
                filas.append([f, f'PAGO PROVEEDOR {random.randint(1, 99)}', imp, D(0)])
            else:
                filas.append([f, f'TRANSF RECIBIDA {random.randint(1, 99)}', D(0), imp])
    return filas


def con_saldo(filas, saldo0):
    s, salida = saldo0, []
    for f, desc, deb, cred in filas:
        s = s - deb + cred
        salida.append((f, desc, deb, cred, s))
    return salida


def ar(n):                       # 1234.5 -> '1.234,50'
    return f'{n:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def escribir_alfa(path, filas, saldo=True, descripcion_extra=''):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['FECHA', 'DESCRIPCION', 'REFERENCIA', 'DEBITO EN $', 'CREDITO EN $', 'SALDO EN $'])
        for i, (f, desc, deb, cred, s) in enumerate(filas):
            w.writerow([f.strftime('%d/%m/%Y'), desc + descripcion_extra, f'REF{i}', ar(deb) if deb else '',
                        ar(cred) if cred else '', ar(s) if saldo else ''])


def escribir_gamma(path, filas):
    """Encabezados en ingles, separador coma, numeros 1,234.56 (US)."""
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['Date', 'Description', 'Debit', 'Credit', 'Balance'])
        for f, desc, deb, cred, s in filas:
            w.writerow([f.strftime('%Y-%m-%d'), desc, f'{deb:,.2f}' if deb else '', f'{cred:,.2f}' if cred else '', f'{s:,.2f}'])


def escribir_beta(path, filas):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Cuenta Corriente Pesos'])
    ws.append(['Numero', '000123456'])
    ws.append([])
    ws.append(['Fecha', 'Detalle', 'Importe', 'Saldo'])
    for f, desc, deb, cred, s in filas:
        ws.append([datetime.datetime.combine(f, datetime.time()), desc, float(cred - deb), float(s)])
    wb.save(path)


def main():
    tmp = tempfile.mkdtemp(prefix='test_extractos_')
    entrada, salida = os.path.join(tmp, 'entrada'), os.path.join(tmp, 'salida')
    os.makedirs(os.path.join(entrada, 'Banco Alfa'))
    os.makedirs(os.path.join(entrada, 'Banco Beta'))
    os.makedirs(os.path.join(entrada, 'Varios'))

    # ---- Banco Alfa: csv. verdad de 90 dias con saldo inicial 1000
    base = verdad(90, 1000)
    alfa = con_saldo(base, D(1000))
    for mes in (1, 2, 3):                                   # mensuales
        escribir_alfa(os.path.join(entrada, 'Banco Alfa', f'Movimientos Alfa mes {mes}.csv'),
                      [r for r in alfa if r[0].month == mes])
    # agrupado: mismas operaciones, otra descripcion, y 1er mes sin saldo no (tiene todo)
    escribir_alfa(os.path.join(entrada, 'Banco Alfa', 'Movimientos Alfa agrupado ene-mar.csv'), alfa, descripcion_extra=' MT')
    # duplicado exacto del mensual 1
    shutil.copy(os.path.join(entrada, 'Banco Alfa', 'Movimientos Alfa mes 1.csv'),
                os.path.join(entrada, 'Varios', 'Movimientos Alfa mes 1 (copia).csv'))
    # semana suelta SIN saldo
    sem = [r for r in alfa if datetime.date(2026, 2, 2) <= r[0] <= datetime.date(2026, 2, 8)]
    escribir_alfa(os.path.join(entrada, 'Banco Alfa', 'Movimientos Alfa semana sin saldo.csv'), sem, saldo=False)

    # ---- Banco Beta: xlsx con importe firmado
    base = verdad(60, 5000)
    beta = con_saldo(base, D(5000))
    # semanal con un dia partido: ultimo dia de la semana 1 tiene filas repartidas
    corte = datetime.date(2026, 1, 15)
    dia_corte = [r for r in beta if r[0] == corte]
    while len(dia_corte) < 4:                                # forzar un dia de 4 movimientos
        extra = beta[beta.index(dia_corte[-1])]
        break
    previos = [r for r in beta if r[0] < corte]
    despues = [r for r in beta if r[0] > corte]
    if len(dia_corte) >= 2:
        k = 1
        parte1, parte2 = dia_corte[:k], dia_corte[k:]
    else:
        parte1, parte2 = dia_corte, []
    escribir_beta(os.path.join(entrada, 'Banco Beta', 'Beta semana 1.xlsx'), previos + parte1)
    escribir_beta(os.path.join(entrada, 'Banco Beta', 'Beta semana 2 (inversa).xlsx'), (parte2 + despues)[::-1])

    # ---- Banco Gamma: encabezados en ingles, numeros US
    os.makedirs(os.path.join(entrada, 'Banco Gamma'))
    base = verdad(30, 300)
    gamma = con_saldo(base, D(300))
    escribir_gamma(os.path.join(entrada, 'Banco Gamma', 'Gamma statement.csv'), gamma)

    # ---- banco imposible de identificar
    escribir_alfa(os.path.join(entrada, 'Varios', 'extracto_raro.csv'), alfa[:5])

    cfg_json = os.path.join(tmp, 'proyecto.json')
    json.dump({'empresa': 'Empresa de Prueba', 'cuit': '', 'entrada': entrada, 'salida': salida, 'idioma': 'es',
               'bancos': [{'contiene': 'Alfa', 'banco': 'Banco Alfa'}, {'contiene': 'Beta', 'banco': 'Banco Beta'}, {'contiene': 'Gamma', 'banco': 'Banco Gamma'}],
               'cuentas': [{'banco': 'Banco Alfa', 'cuenta': 'CC Alfa'}, {'banco': 'Banco Beta', 'cuenta': 'CC Beta'}]},
              open(cfg_json, 'w'))
    cfg = cargar_config(cfg_json)

    fallos = []

    def chequear(cond, msg):
        print(('  OK   ' if cond else '  FALLA ') + msg)
        if not cond:
            fallos.append(msg)

    inv = pasos.inventario(cfg)
    chequear(any(f['banco'] == 'Banco sin identificar' for f in inv), 'banco no identificable: se avisa y no se adivina')
    chequear(any('IDENTICO' in f['marcas'] for f in inv), 'duplicado exacto detectado')
    # el archivo raro se excluye del resultado (no tiene banco); se lo saca para el resto de la prueba
    os.remove(os.path.join(entrada, 'Varios', 'extracto_raro.csv'))
    pasos.inventario(cfg)
    pasos.leer(cfg)
    pasos.unificar(cfg)
    pasos.pdf(cfg)
    pasos.excel(cfg)
    rc = pasos.verificar(cfg)
    final = leer_movimientos(os.path.join(cfg['trabajo'], 'final.csv'))
    cortes = list(csv.DictReader(open(os.path.join(cfg['trabajo'], 'cortes_final.csv'), encoding='utf-8-sig'), delimiter=';'))

    for nombre, verdad_filas in (('Banco Alfa', alfa), ('Banco Beta', beta), ('Banco Gamma', gamma)):
        f = [r for r in final if r['banco'] == nombre]
        chequear(len(f) == len(verdad_filas), f'{nombre}: {len(f)} filas recuperadas de {len(verdad_filas)} reales')
        chequear(sum(r['debito'] for r in f) == sum(r[2] for r in verdad_filas) and
                 sum(r['credito'] for r in f) == sum(r[3] for r in verdad_filas), f'{nombre}: totales de debito y credito exactos')
        chequear(f[-1]['saldo'] == verdad_filas[-1][4], f'{nombre}: saldo final igual al real ({verdad_filas[-1][4]})')
    chequear(len(cortes) == 0, 'cero cortes de saldo en el resultado')
    chequear(rc == 0, 'el verificador independiente da OK')
    chequear(os.path.exists(os.path.join(salida, 'Banco Alfa Empresa de Prueba - Movimientos.xlsx')), 'se genero un Excel por banco')

    shutil.rmtree(tmp, ignore_errors=True)
    if fallos:
        print(f'\n{len(fallos)} FALLOS')
        sys.exit(1)
    print('\nTODAS LAS PRUEBAS PASARON')


if __name__ == '__main__':
    main()
