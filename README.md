# Finanzas NZ — Finanzas Familia Nantón Zapata

Sistema para llevar las finanzas familiares: ingesta de estados de cuenta de
tarjeta de crédito (PDF), almacenamiento en **Firebase Firestore** y un
**dashboard** con gastos por persona, categoría y mes, comparados contra un
presupuesto mensual.

## Arquitectura

```
Estado de cuenta BAC (PDF)
        │  scripts/parse_bac.py
        ▼
transacciones.json ── scripts/upload.py ──► Firestore (finanzasnz-16d54)
                                                  │
        index.html (GitHub Pages) ◄───────────────┘
```

- **`scripts/parse_bac.py`** — extrae las transacciones de la sección
  *"B) Detalle de compras del periodo"* de un estado de cuenta BAC y las
  categoriza por palabras clave.
- **`scripts/upload.py`** — sube las transacciones (y el presupuesto) a
  Firestore usando la cuenta de servicio (SDK Admin).
- **`index.html`** — dashboard estático que lee Firestore (y usa
  `data/transacciones.json` como respaldo local si Firestore está vacío).
- **`config/categorias.json`** — reglas de categorización y tipo de cambio.
- **`config/presupuesto.json`** — presupuesto mensual de ejemplo.

## Los 4 integrantes

La tarjeta de crédito tiene 4 sub-tarjetas; cada una corresponde a un
integrante de la familia (mapeo en `config/categorias.json` → `personas`):

| Tarjeta | Persona |
|---------|---------|
| `****9704` | Matías |
| `****9712` | Karin |
| `****4613` | Iker |
| `****6687` | Daniel |

## Configuración (una sola vez)

### 1. Cuenta de servicio de Firebase (para subir datos)

1. Abre [Firebase Console](https://console.firebase.google.com) → proyecto
   `finanzasnz-16d54`.
2. **Configuración del proyecto → Cuentas de servicio → Generar nueva clave privada**.
3. Guarda el JSON descargado (NO lo subas al repo).

### 2. Reglas de Firestore

Copia el contenido de [`firestore.rules`](firestore.rules) en
**Firestore Database → Reglas**. Por defecto permite **lectura pública**
y bloquea escritura (solo escribe la cuenta de servicio). Ver nota de
privacidad abajo.

### 3. Firestore Database

Crea una base de datos **Firestore** (modo producción) si aún no existe.
Las colecciones se crean solas al subir: `transacciones` y `presupuesto`.

### 4. Publicar el dashboard (GitHub Pages)

1. Sube este repo a GitHub (`dnanton-cr/Finanzas_NZ`).
2. **Settings → Pages → Source: deploy from branch → `main` / `/ (root)`**.
3. El dashboard queda en `https://dnanton-cr.github.io/Finanzas_NZ/`.

## Uso

```bash
pip install -r requirements.txt

# 1. Parsear un estado de cuenta
python scripts/parse_bac.py "EstadodeCuenta-BAC-6687-Nov2026.pdf" \
    -o data/transacciones.json

# 2. Subir a Firestore
python scripts/upload.py data/transacciones.json \
    --service-account /ruta/a/la/cuenta-de-servicio.json

# 3. (Opcional) subir también el presupuesto
python scripts/upload.py data/transacciones.json \
    --service-account /ruta/a/la/cuenta-de-servicio.json \
    --presupuesto config/presupuesto.json
```

La subida es **idempotente**: el id de documento es un hash de los campos
clave, así que volver a subir el mismo estado no duplica transacciones.

## Personalizar categorías

Edita `config/categorias.json`. Cada categoría tiene una lista de
`keywords` (subcadenas, sin distinción de mayúsculas) que se evalúan en
orden; la primera coincidencia gana. Si ninguna coincide, la transacción
se asigna a `otros_nombre` (por defecto "Otros").

El **tipo de cambio** USD→CRC se define en dos lugares (mantenlos iguales):
`config/categorias.json` → `tasa_usd_crc` y `index.html` → `USD_CRC`.

## Presupuesto mensual

El presupuesto se guarda en Firestore como un documento `presupuesto/YYYY-MM`.
**Si un mes no tiene documento propio, el dashboard usa el presupuesto más
reciente como plantilla**, de modo que todos los meses muestran su presupuesto
(y su comparación gasto vs. presupuesto) aunque solo exista un doc. Para dar a
un mes un presupuesto distinto, basta crear su documento `presupuesto/YYYY-MM`.

```json
{
  "mes": "2026-11",
  "total": 2000000,
  "por_persona": { "Daniel": 500000, "Matías": 400000, "Karin": 500000, "Iker": 600000 },
  "por_categoria": { "Supermercado": 500000, "Restaurantes": 250000, "…": 0 }
}
```

Puedes subirlo con `--presupuesto config/presupuesto.json` o crearlo
directamente en la consola de Firestore.

## Categorías que aprenden y re-categorización

- Al subir un estado nuevo, cada descripción se compara contra las transacciones
  ya guardadas; si un comercio ya fue categorizado en meses previos, se le asigna
  la misma categoría automáticamente (ya no vuelve a caer en "Otros").
- En la tabla de transacciones, la columna **Categoría** es editable: cambiala y
  el nuevo valor se guarda en Firestore y queda aprendido para futuras subidas.
- Si el PDF no trae fecha, el parser la infiere del número de referencia BAC
  (MMDD al inicio). Es la fecha de registro; puede diferir 1-2 días de la compra.

## Ingresos y proyectos

Los aportes se guardan en la colección `ingresos`. Cada registro tiene:

```json
{ "persona": "Daniel", "proyecto": "Citi CSC", "monto_usd": 5000, "tipo": "recurrente" }
{ "persona": "Karin", "proyecto": "Administracion propiedades Trigal", "monto_usd": 2000, "tipo": "esporadico", "fecha": "2026-10-30", "mes": "2026-10" }
```

- `tipo: "recurrente"` suma ese monto a **todos** los meses.
- `tipo: "esporadico"` suma solo en el `mes` indicado (derivado de `fecha`).

El dashboard compara, por mes y persona, el **gasto** (de `transacciones`) contra el
**ingreso aportado** (recurrentes + esporádicos) y muestra el balance neto.

## ⚠️ Nota de privacidad

Las reglas por defecto permiten **lectura pública** de Firestore: cualquiera
que conozca el `projectId` puede leer las transacciones. Es lo más simple
para un dashboard sin login, pero **no es privado**.

Para cerrarlo con Firebase Auth (recomendado):

1. En la consola de Firebase habilita **Authentication → Método de acceso → Anónimo**.
2. Cambia la regla a `allow read: if request.auth != null;`.
3. En `index.html` descomenta el inicio de sesión anónimo al inicio del
   script (`firebase.auth().signInAnonymously()`).

Los datos del estado de cuenta de ejemplo quedan en `data/transacciones.json`
para que el dashboard funcione incluso antes de configurar Firebase.
