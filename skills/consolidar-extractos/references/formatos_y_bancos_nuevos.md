# Formatos ya vistos y cómo sumar un banco nuevo

El lector `tabla` reconoce encabezados por sinónimos en español y en inglés, sin importar el banco. Casi todo lo que sea una tabla con fecha,
descripción, débito/crédito (o importe firmado) y saldo se lee solo.

| Formato | Cómo viene | Detalles |
|---|---|---|
| xlsx tipo "Office Banking" (Galicia) | Fecha, Descripción, Débitos, Créditos, varias columnas de detalle, Saldo | Uno por mes o por semana según cómo se descargó. |
| xls viejo (Macro) | Importe firmado en una sola columna + Saldo; encabezado con tipo y número de cuenta; celdas combinadas | Viene del más nuevo al más viejo; xlrd. |
| csv con `;` (Hipotecario) | FECHA;DESCRIPCION;SUCURSAL;REFERENCIA;DEBITO EN $;CREDITO EN $;SALDO EN $ | Números "1.234,56". Algún archivo sin saldo. |
| xlsx tipo estado de cuenta digital (Brubank) | Importes como texto "$ 1.300.000,00", saldo "- $ 1.283.940,77" | Columna "Cuenta" con el tipo; el orden del día cambia entre descargas. |
| PDF Office Banking / Resumen de cuenta / extracto de últimos movimientos | Texto con una fila por línea y líneas de detalle | Tres lectores específicos; uno genérico de baja confianza. |

## Sumar un banco que no se lee
1. Correr `inventario`. Mirar la columna `formato` y `avisos` del banco nuevo.
2. Si dice "no reconocido": abrir el archivo y ver cómo se llaman las columnas. Si son sinónimos razonables de fecha,
   débito/crédito/importe, saldo, agregar el sinónimo en `_mapear` (`scripts/extractos/adaptadores.py`).
3. Si la estructura es distinta (varias hojas, filas en bloques, PDF raro): escribir una función chica en
   `adaptadores.py` que devuelva filas con el esquema de `comunes.py`, y registrarla en `leer_archivo`.
4. **Probarla con un archivo real del banco y con el control de saldo corrido**: si `cortes_saldo` da 0, lee bien.
   Agregar un caso en `tests/test_flujo.py` con datos inventados.
5. PDFs escaneados (imágenes) no se leen con estos scripts: pedir al usuario el Excel/csv al banco, o consultar si
   quiere hacer OCR (es otro proyecto, con otros riesgos de error).

Todo cambio de scripts: correr `python tests/test_flujo.py` y volver a probar con el caso real.
