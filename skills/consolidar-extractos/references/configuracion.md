# proyecto.json

| Campo | Obligatorio | Qué es |
|---|---|---|
| `empresa` | sí | Nombre para títulos y nombres de archivo. |
| `entrada` | sí | Carpeta con los extractos (se recorre completa, con subcarpetas). |
| `salida` | sí | Carpeta donde quedan los Excel (`trabajo/` e `interno/` se crean adentro). |
| `cuit` | no | Se muestra en el título del Resumen. |
| `idioma` | no | `es` (por defecto) o `en` para encabezados del Excel. |
| `periodo_texto` | no | Frase para el subtítulo del Resumen, p. ej. "Año fiscal oct 2025 - oct 2026." |
| `bancos` | no | Reglas para reconocer el banco: `{"contiene": "texto en la ruta", "banco": "Nombre"}`. |
| `bancos_conocidos` | no | Lista extra de nombres de bancos a buscar en rutas (además de la lista incluida). |
| `cuentas` | no | Reglas para nombrar cuentas (abajo). |
| `mayores` | no | Libros mayores que suplen tramos sin extracto (abajo). |
| `notas` | no | `{"Banco": ["frase para el Resumen", ...]}`: contexto útil para quien lee (cierres de cuenta, etc.). |

## Reglas de `cuentas` (la primera que coincide gana)
Cada regla puede tener: `banco`, `contiene_archivo` (texto en la ruta del archivo), `contiene_cuenta` (texto en la
cuenta detectada del contenido), y siempre `cuenta` (nombre final) y opcionalmente `solapa` (nombre de la hoja,
máx. 31 caracteres). Ejemplo:
```json
"cuentas": [
  {"banco": "Galicia", "contiene_archivo": "012-9", "cuenta": "CC 0005-012-9", "solapa": "CC 012-9"},
  {"banco": "Galicia", "cuenta": "CC principal"},
  {"banco": "Macro", "contiene_cuenta": "Especial", "cuenta": "Cta. Especial 4528", "solapa": "Cta Especial"}
]
```
Si ninguna regla coincide se usa la cuenta que el archivo informa (p. ej. número de cuenta en el encabezado, o una
columna "Cuenta"); si el archivo no dice nada queda `(sin identificar)` y **hay que preguntar al usuario**.

Los PDFs de un mismo banco muchas veces nombran la cuenta distinto que los Excel: la regla por defecto del banco
(sin `contiene_*`) las junta en una sola cuenta. Confirmar con el usuario que es la misma cuenta.

## `mayores` (opcional: tramos sin extracto)
```json
"mayores": [
  {"archivo": "/ruta/Mayor Banco X Cta Cte.csv", "banco": "Banco X", "cuenta": "CC principal",
   "solapa": "CC principal (mayor ene)", "desde": "2026-01-01", "hasta": "2026-01-31"}
]
```
`archivo` va **fuera** de `entrada` (si no, se lo leería como si fuera un extracto). `desde`/`hasta` limitan el período:
lo que quede afuera se informa y se guarda en `trabajo/mayor_excluidas.csv`. `solapa` es el nombre de la hoja (máx. 31
caracteres; conviene que termine en "(mayor)"). Formato esperado del CSV: `Cuenta;Fecha;Comprobante;CUIT;Razon Social;
Concepto;Monto Debe;Monto Haber;Saldo;...`. Salida: hojas rotuladas en el Excel del banco + una sección aparte en el
Resumen. Si el sistema contable exporta otro formato, ver `references/formatos_y_bancos_nuevos.md`.
