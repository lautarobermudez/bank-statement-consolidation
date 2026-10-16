# Resolver problemas

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `Banco sin identificar` en el inventario | Nombre de archivo con error o banco fuera de la lista | Regla en `bancos`. Preguntar si hay duda. |
| Cuenta `(sin identificar)` | El archivo no informa su cuenta | Preguntar al usuario y agregar regla en `cuentas`. |
| `cortes_saldo` > 0 en un archivo | Archivo parcial, pegado de dos extractos, o lectura mal alineada | Abrir el archivo; no seguir hasta entenderlo. |
| Cortes en `cortes.csv` tras unificar | Día partido que no se pudo encadenar, o un archivo con filas distintas | Ver `fuentes.csv` y el día indicado; comparar los archivos de ese día. Informar, no corregir. |
| Filas "nuevas" de un PDF que parecen repetidas | El PDF se leyó con otro signo o importe | Revisar el PDF a mano. Si el PDF no cierra su propio saldo, no sumarlo. |
| Un PDF dice "no se pudo leer ninguna fila" | Escaneado o formato nuevo | Pedir el Excel/csv al banco. |
| Se perdió un período completo | No hay archivo de esos días | Confirmar con el usuario si es cierre de cuenta (movimiento "CIERRE" y saldo 0) o si falta el archivo. |
| Mismas operaciones con saldos distintos entre dos archivos | Orden distinto dentro del día | Normal. El flujo usa un solo archivo por día. |
| El total de débitos del Excel no coincide | Se editó el Excel o cambió `final.csv` | Volver a correr `excel` y `verificar`. |
| `verificar` da PROBLEMAS | Algo cambió después de generar | No entregar. Rehacer desde `unificar`. |
| Un `.xls` no abre | Falta `xlrd`, o el "xls" es en realidad HTML | `pip install xlrd`; si es HTML, pedirlo de nuevo en xlsx. |
