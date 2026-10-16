---
name: consolidar-extractos
description: Ordena y unifica extractos bancarios desordenados (xls, xlsx, csv, pdf, mensuales, semanales, agrupados, duplicados, varias cuentas y bancos) de cualquier empresa en UN Excel limpio por banco, con una solapa por cuenta, resumen y saldo corrido verificado. Usar cuando el usuario pida consolidar, ordenar, unificar o emprolijar extractos o movimientos bancarios de un período (por ejemplo para gerencia, auditoría, contador, un banco o un cliente de la consultora). NO es para el libro mayor contable (eso no es un extracto del banco), ni para conciliar contra la contabilidad, ni para facturas u órdenes de pago.
user-invocable: true
---

# /consolidar-extractos — Extractos bancarios desordenados -> un Excel limpio por banco

Argumentos: `$ARGUMENTS` (puede ser la carpeta con los extractos, o venir vacío).
Todo corre **en local**: los extractos tienen datos sensibles, no se suben a ningún servicio.

## Regla de oro
**No inventar ni tapar nada.** Un saldo que no empalma se informa, no se corrige. Una cuenta o un banco que no se
puede identificar se pregunta, no se adivina. Los originales no se tocan.

## Antes de empezar
1. Hacer el **plan de delegación** (skill `plan-de-delegacion`) y esperar el OK del usuario. El reparto típico:
   lectura, unificación, controles y Excel = scripts; banco o formato nuevo, cuentas ambiguas y formato del Excel =
   conversación con el usuario; descargar los extractos, decidir qué se entrega y a quién = el usuario.
2. Aclarar **qué es lo que tiene**: ¿son extractos del banco o el libro mayor de un sistema contable? El mayor no es
   un extracto (no lo llames así ni lo presentes como tal). Si es el mayor, parar y avisar.
3. Saber el **período** (año fiscal) y para quién es (gerencia, auditoría, banco...).

## Flujo (scripts en `scripts/`)
Preparar `proyecto.json` copiando `scripts/proyecto.ejemplo.json` (campos en `references/configuracion.md`).
Dependencias: `openpyxl`, `xlrd` (para .xls), `pdfplumber` (para PDFs); ver `scripts/requirements.txt`. Si faltan,
avisar y crear un entorno aparte; no instalar nada global sin decirlo.

```
python scripts/consolidar.py inventario --config proyecto.json   # 1. qué hay
python scripts/consolidar.py leer       --config proyecto.json   # 2. todo al mismo esquema
python scripts/consolidar.py unificar   --config proyecto.json   # 3. un archivo por día y cuenta
python scripts/consolidar.py pdf        --config proyecto.json   # 4. suma lo que solo está en PDF
python scripts/consolidar.py mayor      --config proyecto.json   # 4b. (opcional) tramos sin extracto, desde el libro mayor
python scripts/consolidar.py excel      --config proyecto.json   # 5. un Excel por banco
python scripts/consolidar.py verificar  --config proyecto.json   # 6. control independiente
python scripts/consolidar.py todo       --config proyecto.json   # 2 a 6 de corrido (incluye `mayor` si está configurado)
```

1. **Inventario, y revisarlo con el usuario antes de seguir.** Mirar: bancos o cuentas sin identificar (agregar
   reglas en `cuentas` / `bancos` de la configuración), archivos con saldo que no cierra, duplicados idénticos,
   PDFs sin versión Excel, cuentas que cortan (casi siempre son cierres de cuenta, **no** faltantes: confirmarlo).
2. **Leer + unificar + pdf.** Leer el informe de cada paso. Si aparecen cortes de saldo, ver
   `references/resolver_problemas.md` antes de tocar nada.
3. **Excel + verificar.** `verificar` reabre los Excel y recalcula filas, totales y saldo corrido. Si no da OK, no se entrega.
4. **Entrega.** Mostrar al usuario: cuentas y períodos, filas por banco, cortes de saldo (si hay), y qué se tomó de
   PDFs. El usuario revisa y decide si consolida en un solo archivo. **No enviar mails ni subir nada sin que lo pida.**

## Si falta el extracto de un tramo (libro mayor como último recurso)
Si el extracto de un período se perdió, se puede suplir con el **libro mayor** de la cuenta bancaria exportado del
sistema contable (CSV). Reglas: va **siempre en hojas aparte, rotuladas** ("tomado del libro mayor, no es extracto
del banco"), nunca mezclado con las hojas del banco; su saldo es acumulado desde el inicio de lo exportado y **no es
el saldo bancario**; Haber = débito del banco y Debe = crédito. Se configura en `mayores` (ver
`references/configuracion.md`) y el CSV va **fuera** de la carpeta de entrada. Las filas fuera del período pedido se
excluyen y se informan (ej.: un asiento cargado meses después). Avisar al usuario que ese tramo no es del banco.
Un PDF o archivo que resulta idéntico (mismo `md5`) a uno ya cargado no aporta nada: decirlo.

## Qué dejan los scripts (en `<salida>/`)
- `<Banco> <Empresa> - Movimientos.xlsx`: Resumen + una solapa por cuenta (+ `Avisos` solo si hay saldos que no empalman).
- `interno/Trazabilidad - filas tomadas de otro archivo.xlsx`: de dónde salió cada fila que no estaba en el archivo principal.
- `trabajo/`: CSV intermedios (inventario, crudos, unificados, final, cortes, fuentes) para auditar cualquier fila.

## Cuándo parar y preguntar
Banco o formato no reconocido, cuenta sin identificar, PDF que no se pudo leer o de baja confianza, cortes de saldo,
un período con huecos que no sea un cierre de cuenta, o cualquier duda sobre si algo es extracto o mayor.

## Material de apoyo (leer solo si hace falta)
- `references/principios_y_lecciones.md`: por qué cada regla existe (errores reales que ya ocurrieron).
- `references/configuracion.md`: todos los campos de `proyecto.json`, con ejemplos.
- `references/formatos_y_bancos_nuevos.md`: formatos ya vistos y cómo sumar un banco que no se lee.
- `references/resolver_problemas.md`: síntoma -> causa -> qué hacer.
- `tests/test_flujo.py`: prueba con datos inventados. Correrla después de tocar los scripts.
