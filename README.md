# Finanzas NZ

Control de finanzas familiares para Costa Rica: se alimenta con los estados de cuenta (PDF) del banco, guarda las transacciones en **Firebase Firestore** (proyecto `finanzasnz`) y muestra un **dashboard** con gastos por persona, por categoría, por mes y comparación contra un presupuesto mensual. Familia de **4 integrantes**.

## Arquitectura

```
estado_cuenta.pdf  →  parser (Python)  →  Firestore `finanzasnz`  →  dashboard (index.html)
```

- `index.html` — dashboard publicado (GitHub Pages / Vercel). Lee Firestore en tiempo real.
- `parser/` — script que convierte el PDF del banco en transacciones y las sube a Firestore.

## Estructura de datos en Firestore

### Colección `transacciones`

Cada documento es un movimiento de la tarjeta:

| Campo | Tipo | Descripción |
|---|---|---|
| `fecha` | string `YYYY-MM-DD` | Fecha del movimiento |
| `descripcion` | string | Comercio / detalle |
| `monto` | number | Monto en colones (positivo) |
| `tipo` | string | `gasto` (default), `ingreso`, `pago` |
| `persona` | string | Nombre del integrante (de los 4) |
| `categoria` | string | Una de las categorías |
| `mes` | string `YYYY-MM` | Mes al que pertenece (para agrupar) |
| `tarjeta` | string (opcional) | Identificador de la tarjeta en el PDF |
| `fuente` | string (opcional) | Origen, p. ej. `PDF_2025-11` |

### Colección `presupuesto`

Un documento por mes, con **id = `YYYY-MM`**:

| Campo | Tipo | Descripción |
|---|---|---|
| `total` | number | Presupuesto total del mes |
| `categorias` | map<string, number> | Tope por categoría, p. ej. `{"Alimentación": 250000}` |
| `personas` | map<string, number> | (opcional) Tope por persona |

## Categorías por defecto

`Alimentación, Transporte, Vivienda, Servicios, Salud, Educación, Ocio, Restaurantes, Compras, Viajes, Otros`

## Cómo configurar

1. **Firebase**: en Firebase Console → proyecto `finanzasnz` → Configuración del proyecto → *Tus apps* → crear app **Web** y copiar los valores a `firebaseConfig` dentro de `index.html`.
2. **Integrantes**: editar el array `INTEGRANTES` en `index.html` (4 nombres + colores).
3. **Publicar**: subir `index.html` a este repo y activar **GitHub Pages** (o Vercel) apuntando a `index.html`.
4. **Alimentar datos**: correr el parser (ver `parser/`) con el PDF del estado de cuenta; escribe en `transacciones`.

## Estado

- [x] Dashboard (`index.html`): KPIs, por persona, por categoría, por mes, presupuesto y tabla de movimientos.
- [x] Esquema Firestore documentado.
- [ ] Parser del PDF del banco (pendiente: necesita el formato real del estado de cuenta).
- [ ] Carga del presupuesto inicial.

## Pendiente del usuario

1. PDF de muestra del estado de cuenta (para el parser).
2. Config de Firebase (`apiKey`, `appId`, etc.).
3. Nombres de los 4 integrantes + presupuesto mensual + categorías definitivas.
