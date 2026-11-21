# Guía de uso — Finanzas NZ

**Dashboard de finanzas familiares · Familia Nantón Zapata**

---

## ¿Qué es y para qué sirve?

Finanzas NZ es una página web que reúne **todos los gastos e ingresos de la familia en un solo lugar**. Consolida los estados de cuenta de las cuatro tarjetas BAC (Daniel, Karin, Iker y Matías), permite agregar los pagos que no pasan por tarjeta (colegio, casa, efectivo) y registra los ingresos de cada persona por proyecto.

Con esa información muestra, mes a mes, **en qué se está gastando, quién gasta más, cómo vamos contra el presupuesto y cuál es el balance entre lo que entra y lo que sale**.

---

## Cómo entrar

Abrí en el celular o en la computadora:

**https://finanzasnz.vercel.app/**

Se abre directo, sin usuario ni contraseña.

---

## La página tiene dos pestañas

Arriba, debajo del título:

- **📊 Resultados** → para *consultar* la información.
- **📥 Ingresar datos** → para *cargar* información nueva.

Todo lo que se carga aparece al instante en Resultados.

---

## 1) Pestaña Resultados

### Selector de mes
Arriba a la derecha. **Todo lo que ves corresponde al mes elegido.** Cambialo para consultar otro mes.

### Resumen del mes (tarjetas de arriba)
Seis indicadores rápidos:

- **Gasto del mes**
- **Ingresos del mes**
- **Balance del mes** (ingresos − gastos; verde si sobra, rojo si falta)
- **Presupuesto** (cuánto queda disponible o cuánto se excedió)
- **Top categoría** (en qué se gastó más)
- **Top persona** (quién gastó más)

### Gasto vs ingreso por persona
Gráfico de barras y una tabla con el **neto de cada integrante**: verde si le sobra, rojo si se pasó.

### Gasto por categoría y por persona
Dos gráficos para ver **en qué se va la plata** y **cómo se reparte entre los cuatro**.

### Evolución del gasto por mes
Una línea con el gasto de cada mes comparada con la **línea punteada del presupuesto**.

### Balance (ingreso − gasto) por mes
Barras **verdes** cuando hubo superávit y **rojas** cuando hubo déficit.

### Evolución del gasto por persona
Una línea por integrante, para ver tendencias a lo largo de los meses.

### Evolución de categorías prioritarias (Alta)
Las categorías que más pesan, con su **comercio más frecuente** y el promedio de transacciones por mes.

### Presupuesto por categoría
Barras de avance: cuánto se lleva gastado de cada monto asignado.

### Matriz categoría × mes
Tabla grande con todas las categorías y los meses:

- **Prioridad** (Alta = gasta más que el promedio)
- **Promedio** por mes
- **Tendencia** (verde = sube, rojo = baja)
- **Total** por categoría y totales por mes

### Tabla de transacciones
Todas las compras del mes. Podés:

- **Filtrar** por persona, categoría o buscar por texto.
- **Cambiar la categoría** de una transacción directamente en la tabla. El sistema **lo aprende** y la aplica a compras parecidas en el futuro.

---

## 2) Pestaña Ingresar datos

### a) Subir estado de cuenta (PDF)
Botón **"Subir estado de cuenta"**. Arrastrás el PDF de BAC (o hacés clic para elegirlo). El archivo **se procesa en tu navegador**, no se envía a ningún servidor.

1. Aparece la lista de transacciones detectadas.
2. Podés **desmarcar** las que no quieras y **corregir persona o categoría**.
3. Presionás **"Guardar en Firestore"**.

Si subís el mismo archivo dos veces, la app avisa y **no duplica** las transacciones.

### b) Subida masiva (CSV)
Para cargar muchos movimientos de una vez. Dos botones: **Subir gastos (CSV)** y **Subir ingresos (CSV)**. Hay una **plantilla descargable** para cada uno.

Columnas:

- **Gastos:** `fecha, persona, descripcion, categoria, moneda, monto`
- **Ingresos:** `persona, proyecto, monto, moneda, tipo, fecha`

Antes de guardar muestra una **vista previa** y marca en rojo las filas con error (esas no se guardan).

### c) Agregar un ingreso
Para registrar lo que aporta cada persona:

- **Persona**
- **Proyecto** (ej. "Citi CSC")
- **Monto** y **moneda** (USD, CRC o EUR)
- **Tipo de cambio** (si no es USD)
- **Tipo:** *Mensual* (cuenta todos los meses) o *Esporádico* (solo el mes indicado)
- **Fecha** (solo si es esporádico)

### d) Gasto manual (sin tarjeta)
Para pagos que no pasan por tarjeta: efectivo, transferencias, mensualidades del colegio, mantenimiento de la casa.

- **Persona**
- **Descripción**
- **Categoría**
- **Monto** y **moneda**
- **Tipo de cambio**
- **Fecha**

---

## Conceptos clave

- **Todo se muestra en dólares.** Si pagás en colones o euros, la app convierte: **¢445 por $1** y **€1 = $1.08**. La tasa se puede ajustar en cada registro.
- **Ingreso mensual vs esporádico:** el mensual se cuenta en todos los meses; el esporádico solo en su mes.
- **Presupuesto:** hay un presupuesto base que se aplica a cada mes y se compara automáticamente.
- **Categorías:** 13 categorías + "Otros". La app aprende de las correcciones que hagas.
- **Fechas:** salen del número de referencia del estado de cuenta BAC y pueden variar 1–2 días respecto a la compra real.
- **Nada se duplica:** al subir un estado o un archivo repetido, se actualiza en vez de duplicar.

---

## Recomendaciones de uso

1. **Subir cada estado de cuenta una vez al mes**, apenas salga el corte.
2. **Revisar la categoría de los comercios nuevos** una sola vez; después se aplica solo.
3. **Usar "Gasto manual"** para todo lo que no pasa por tarjeta.
4. **Registrar los ingresos por proyecto** para que el balance sea real.
5. **Elegir el mes correcto** antes de leer los resultados.

---

## Guion corto para presentar (30–40 segundos)

> "Les comparto Finanzas NZ, la página donde llevamos las finanzas de la familia. Ahí se juntan automáticamente los estados de cuenta de las cuatro tarjetas, los gastos que pagamos sin tarjeta y los ingresos de cada uno. En la pestaña **Resultados** ven, mes a mes, en qué se gasta, quién gasta más, cómo vamos contra el presupuesto y si el balance es positivo. En **Ingresar datos** suben el estado de cuenta o registran un gasto o ingreso. Todo se convierte a dólares y no hay que duplicar nada. El enlace es finanzasnz.vercel.app."
