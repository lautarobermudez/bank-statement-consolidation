#!/usr/bin/env python3
"""Build a small, entirely fictional demo and run the whole pipeline on it.

    python examples/make_demo.py

Creates examples/demo_input (messy statements: monthly + grouped + weekly files, different wording (UPPER vs Title Case) and
intra-day order between downloads, a duplicate) and examples/demo_output (one workbook per bank).
Nothing here is real data. Both folders are git-ignored.
"""
import csv
import datetime
import os
import random
import shutil
import sys
from decimal import Decimal as D

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), 'skills', 'consolidar-extractos', 'scripts'))
from extractos import pasos                              # noqa: E402
from extractos.comunes import cargar_config               # noqa: E402

ENTRADA, SALIDA = os.path.join(AQUI, 'demo_input'), os.path.join(AQUI, 'demo_output')
random.seed(42)
START = datetime.date(2026, 1, 1)
PARTNERS = ['Acme Supplies Ltd', 'Globex Corp', 'Initech Services', 'Umbrella Logistics', 'Stark Components',
            'Wayne Packaging', 'Hooli Software', 'Soylent Foods']
KINDS = [('SUPPLIER PAYMENT', 'debit'), ('CUSTOMER TRANSFER', 'credit'), ('PAYROLL', 'debit'),
         ('CARD SETTLEMENT', 'credit'), ('BANK FEE', 'debit'), ('TAX PAYMENT', 'debit')]


def movements(days, opening):
    rows, bal = [], D(opening)
    for d in range(days):
        day = START + datetime.timedelta(days=d)
        if day.weekday() >= 5:
            continue
        for _ in range(random.randint(1, 4)):
            kind, side = random.choice(KINDS)
            amount = (D(random.randint(2500, 450000)) / 100).quantize(D('0.01'))
            who = random.choice(PARTNERS)
            deb, cred = (amount, D(0)) if side == 'debit' else (D(0), amount)
            bal = bal - deb + cred
            rows.append([day, f'{kind} - {who}', deb, cred, bal])
    return rows


def rewrite_order(rows, opening, title_case=False):
    """Same transactions, as another download would deliver them: different wording, other order inside a day."""
    out, by_day = [], {}
    for r in rows:
        by_day.setdefault(r[0], []).append(r)
    bal = D(opening)
    for day in sorted(by_day):
        items = by_day[day][:]
        random.shuffle(items)
        for _, desc, deb, cred, _ in items:
            bal = bal - deb + cred
            out.append([day, desc.title() if title_case else desc, deb, cred, bal])
    return out


def write_csv_northwind(path, rows):
    with open(path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['DATE', 'DESCRIPTION', 'REFERENCE', 'DEBIT', 'CREDIT', 'BALANCE'])
        for i, (d, desc, deb, cred, bal) in enumerate(rows):
            f = lambda x: f'{x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if x else ''
            w.writerow([d.strftime('%d/%m/%Y'), desc, f'NW{i:05d}', f(deb), f(cred), f(bal)])


def write_xlsx_harbor(path, rows):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['Savings account'])
    ws.append(['Number', '00123456'])
    ws.append([])
    ws.append(['Date', 'Details', 'Amount', 'Balance'])
    for d, desc, deb, cred, bal in rows:
        ws.append([datetime.datetime.combine(d, datetime.time()), desc, float(cred - deb), float(bal)])
    wb.save(path)


def main():
    for p in (ENTRADA, SALIDA):
        shutil.rmtree(p, ignore_errors=True)
    os.makedirs(os.path.join(ENTRADA, 'Northwind Bank'))
    os.makedirs(os.path.join(ENTRADA, 'Harbor Bank'))
    os.makedirs(os.path.join(ENTRADA, 'Misc'))

    nw = movements(59, 150000)                       # Jan-Feb, Northwind Bank (csv)
    for month, name in ((1, 'january'), (2, 'february')):
        write_csv_northwind(os.path.join(ENTRADA, 'Northwind Bank', f'Northwind statement {name}.csv'),
                            [r for r in nw if r[0].month == month])
    write_csv_northwind(os.path.join(ENTRADA, 'Northwind Bank', 'Northwind statement jan-feb (grouped).csv'),
                        rewrite_order(nw, 150000, title_case=True))
    shutil.copy(os.path.join(ENTRADA, 'Northwind Bank', 'Northwind statement january.csv'),
                os.path.join(ENTRADA, 'Misc', 'Northwind statement january (copy).csv'))

    hb = movements(59, 80000)                        # Harbor Bank (xlsx, weekly files that overlap a boundary day)
    cut = [r for r in hb if r[0] == datetime.date(2026, 1, 15)]
    first = [r for r in hb if r[0] < datetime.date(2026, 1, 15)] + cut[:1]
    second = cut[1:] + [r for r in hb if r[0] > datetime.date(2026, 1, 15)]
    write_xlsx_harbor(os.path.join(ENTRADA, 'Harbor Bank', 'Harbor savings part 1.xlsx'), first)
    write_xlsx_harbor(os.path.join(ENTRADA, 'Harbor Bank', 'Harbor savings part 2 (newest first).xlsx'), second[::-1])

    import json
    cfg_path = os.path.join(AQUI, 'demo_input', 'proyecto.json')
    json.dump({'empresa': 'Demo Company', 'cuit': '', 'entrada': ENTRADA, 'salida': SALIDA, 'idioma': 'en',
               'periodo_texto': 'Fiscal period January - February 2026.',
               'bancos': [{'contiene': 'Northwind', 'banco': 'Northwind Bank'}, {'contiene': 'Harbor', 'banco': 'Harbor Bank'}],
               'cuentas': [{'banco': 'Northwind Bank', 'cuenta': 'Checking 0001', 'solapa': 'Checking 0001'},
                           {'banco': 'Harbor Bank', 'cuenta': 'Savings 00123456', 'solapa': 'Savings 00123456'}]},
              open(cfg_path, 'w'), indent=1)
    cfg = cargar_config(cfg_path)
    for paso in ('inventario', 'leer', 'unificar', 'pdf', 'excel'):
        print(f'\n=== {paso} ===')
        getattr(pasos, paso)(cfg)
    print('\n=== verificar ===')
    sys.exit(pasos.verificar(cfg))


if __name__ == '__main__':
    main()
