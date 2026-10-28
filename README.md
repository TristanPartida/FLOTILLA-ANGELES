
# App de control de gasolina de flotilla

Primera versión funcional construida con Streamlit + SQLite.

## Qué hace
- Catálogo de 33 camionetas.
- Registro de gasolina por fecha, placa e importe.
- Carga inicial de la tabla compartida.
- Consulta por camioneta y periodo.
- Dashboard con total, unidad con mayor gasto y gráfica por día.
- Exportación a CSV.
- Evita duplicar un gasto para la misma camioneta y fecha: lo actualiza.

## Cómo abrirla
1. Instala Python 3.10 o superior.
2. Abre una terminal en esta carpeta.
3. Ejecuta:
   pip install -r requirements.txt
4. Después ejecuta:
   streamlit run app.py

La base de datos `flotilla.db` se crea automáticamente al iniciar.

## Carga de los datos que ya tienes
En el menú "Carga inicial", selecciona la fecha que corresponde al lunes de tu tabla.
La app coloca automáticamente los importes de lunes, martes y el registro de miércoles.

Totales de referencia de la tabla:
- Lunes: $11,850
- Martes: $10,750
- Miércoles: $400
