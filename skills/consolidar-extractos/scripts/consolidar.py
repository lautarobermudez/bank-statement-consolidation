#!/usr/bin/env python3
"""Consolida extractos bancarios desordenados en un Excel limpio por banco.

Uso:  python consolidar.py <paso> --config proyecto.json
Pasos: inventario | leer | unificar | pdf | mayor | excel | verificar | todo
       (todo = leer, unificar, pdf, mayor, excel, verificar; `mayor` es opcional y solo actua si hay `mayores` en la config)
Siempre se corre `inventario` primero y se revisa con el usuario (cuentas sin identificar, duplicados, PDFs).
Requiere: openpyxl; xlrd (para .xls); pdfplumber (para PDFs). Todo corre en local.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extractos import pasos                      # noqa: E402
from extractos.comunes import cargar_config      # noqa: E402

PASOS = ['inventario', 'leer', 'unificar', 'pdf', 'mayor', 'excel']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paso', choices=PASOS + ['verificar', 'todo'])
    ap.add_argument('--config', required=True, help='proyecto.json (ver references/configuracion.md)')
    a = ap.parse_args()
    cfg = cargar_config(a.config)
    if not os.path.isdir(cfg['entrada']):
        raise SystemExit(f'No existe la carpeta de entrada: {cfg["entrada"]}')
    os.makedirs(cfg['salida'], exist_ok=True)
    if a.paso == 'todo':
        pasos.inventario(cfg)
        for p in ('leer', 'unificar', 'pdf', 'mayor', 'excel'):
            print(f'\n=== {p} ===')
            getattr(pasos, p)(cfg)
        print('\n=== verificar ===')
        sys.exit(pasos.verificar(cfg))
    if a.paso == 'verificar':
        sys.exit(pasos.verificar(cfg))
    getattr(pasos, a.paso)(cfg)


if __name__ == '__main__':
    main()
