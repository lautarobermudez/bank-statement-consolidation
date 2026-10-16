# bank-statement-consolidation (versión en español)

Convierte una carpeta desordenada de extractos bancarios en **un Excel limpio por banco**, con una solapa por cuenta, un resumen y el saldo corrido verificado de forma independiente.

Está empaquetado como *skill* de Claude Code (`consolidar-extractos`) con scripts de Python por debajo: se puede usar guiado por Claude o desde la línea de comandos.

## Para qué sirve
Cuando gerencia, auditoría o un banco piden "todos los extractos del año fiscal" y lo que hay son varios bancos, cuentas abiertas y cerradas, el mismo período en xls/xlsx/csv/pdf, archivos mensuales y semanales que se pisan, duplicados y textos que cambian entre descargas.

## Cómo funciona
`inventario -> leer -> unificar -> pdf -> excel -> verificar` (detalle en el [README en inglés](README.md#what-it-does)).

Reglas que no se negocian: no inventar ni tapar nada (un saldo que no empalma se informa), comparar filas por fecha + débito + crédito y nunca por texto, un solo archivo por día y cuenta, todo en local.

## Demo
`python examples/make_demo.py` arma un conjunto **inventado** de extractos desordenados y corre todo el flujo (ver capturas en el [README en inglés](README.md#see-it-in-10-seconds)).

## Uso rápido
```bash
pip install -r skills/consolidar-extractos/scripts/requirements.txt
cp skills/consolidar-extractos/scripts/proyecto.ejemplo.json proyecto.json
python skills/consolidar-extractos/scripts/consolidar.py inventario --config proyecto.json
python skills/consolidar-extractos/scripts/consolidar.py todo --config proyecto.json
```
Para instalarla como skill de Claude Code: `./install.sh` (copia la skill a `~/.claude/skills`; repetir con `--force` después de un `git pull`).
La documentación de la skill (en español) está en [`skills/consolidar-extractos/SKILL.md`](skills/consolidar-extractos/SKILL.md) y `references/`.

## Pruebas
`python skills/consolidar-extractos/tests/test_flujo.py` (datos 100% inventados).

## Licencia
MIT.
