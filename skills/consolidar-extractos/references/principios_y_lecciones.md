# Principios y lecciones (por qué cada regla existe)

Todas salen de un caso real (empresa argentina, año fiscal, 4 bancos, 7 cuentas, 87 archivos, ~7.000 movimientos).

## Principios
1. **No inventar ni tapar.** Un saldo que no empalma se informa en la hoja `Avisos`; no se "arregla". El usuario pidió
   esto explícitamente tras un error mío. Lo que no se pueda leer con certeza se dice.
2. **Extracto del banco != libro mayor.** El mayor contable (de un sistema como un ERP) es lo que la empresa
   registró; el extracto es lo que el banco informa. Se parecen y se confunden. Para presentar movimientos bancarios
   se usa el extracto. Señales de que es un mayor: columnas "Comprobante", "Razón social", "Centro de costo", "Monto Debe/Haber".
3. **Todo local y los originales intactos.** Datos bancarios sensibles; se trabaja sobre copias de resultados en otra carpeta.
4. **Cada paso deja un CSV auditable** (`trabajo/`). Cualquier fila del Excel se puede rastrear a su archivo de origen.
5. **El control de saldo corrido manda.** Para cada cuenta, `saldo anterior + crédito - débito = saldo`. Si cierra en
   toda la cadena, no se perdió ni se duplicó nada. Se verifica por archivo, al unir y de nuevo desde el Excel final.
6. **Los cortes cuando el banco cierra la cuenta no son huecos.** Un archivo que "termina" suele ser un cierre
   de cuenta (hay un movimiento "CIERRE DE CUENTA" y saldo 0). Confirmarlo con el usuario, no perseguirlo.

## Lecciones (errores reales)
- **Comparar filas por texto duplicó movimientos.** El mismo banco escribe la descripción y la referencia distinto
  en una descarga mensual y en una agrupada ("... | CUIT" vs "... MT"). Resultado: dos transferencias de millones
  parecieron "faltantes" y se las sumó de nuevo, rompiendo el saldo. **Se compara por fecha + débito + crédito**
  (y por saldo solo cuando ambas lo traen), nunca por descripción.
- **El orden dentro de un mismo día cambia entre descargas.** El saldo fila a fila entonces difiere aunque las
  operaciones sean las mismas. Solución: por día y cuenta se usa **un solo archivo** (el que tiene saldo, luego el de
  más filas ese día, luego el más grande) y lo que otro archivo tenga de más se agrega y se marca.
- **Un día puede venir partido entre dos archivos** (semanal que corta a mitad de día). Las filas extra se ordenan
  siguiendo el saldo. Si no se puede encadenar, queda el corte informado.
- **Hay archivos que listan lo más nuevo primero** (xls de algunos bancos, PDFs). Se detecta por el saldo corrido,
  o por las fechas si no hay saldo.
- **Un xls viejo con celdas combinadas** corre las columnas; los datos no están donde dice el encabezado de la
  primera columna. Se mapean las columnas por la posición del encabezado, no por orden.
- **HTML dentro de CSV**: entidades como `&#243;` contienen `;` y parten las filas. Si aparecen, leer con cuidado
  o pedir la descarga de nuevo.
- **Un mensual puede no traer saldo.** Se lo usa igual, pero con menor prioridad que los que sí lo traen.
- **Nombres de archivo con errores** ("Galica"): el banco no se reconoce y se avisa. Se resuelve con una regla en
  `bancos`, no cambiando la lógica.
- **PDF con versión Excel/csv:** se ignora el PDF. Solo se leen los PDFs sin versión estructurada, y se comparan
  contra lo ya unificado: de 13 PDFs, 9 estaban completos y 4 aportaron filas.
- **Cada PDF se compara por separado** contra lo unificado (no consumir el mismo contador de filas con varios PDFs
  que cubren el mismo tramo, o el segundo parecerá "nuevo").
- **El libro mayor puede suplir un extracto perdido, pero no se mezcla.** Se agrega en hojas aparte y rotuladas:
  el mayor es el registro de la empresa (p. ej. un cheque aparece el día que se emitió, no el día que el banco lo
  debitó) y su saldo es relativo al período exportado. Se cruza el signo: Haber = débito del banco, Debe = crédito.
  Pasó que un asiento cargado meses después (fecha de abril en un mayor de enero) venía en el archivo: se excluye
  por período y se informa, no se descarta en silencio.
- **Un archivo "nuevo" puede ser uno ya cargado.** Antes de procesar un PDF que llega, comparar el `md5` con los ya
  leídos: el de 20-31/07 que llegó de nuevo era idéntico y no aportaba nada.
