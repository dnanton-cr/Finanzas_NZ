# Módulo de seguridad — Finanzas NZ

Roles con **Firebase Authentication** (correo y contraseña) + reglas de Firestore.

## Roles

| Rol | Puede... |
|---|---|
| **admin** | Ver todo **y** cargar/editar datos (estados de cuenta, CSV, ingresos, gastos manuales, re-categorizar, cambiar el corte de ingresos). |
| **lector** | Solo **ver** resultados y la guía. No ve la pestaña "Ingresar datos" ni puede modificar nada. |

La seguridad real está en **`firestore.rules`** (el servidor). Lo que hace la app es solo
cosmético (ocultar botones); aunque alguien abra la consola del navegador, las reglas
rechazan cualquier escritura de un `lector`.

## Estado actual

El módulo está **construido pero inactivo**: en `index.html` está

```js
const SEGURIDAD_ACTIVA = false;
```

Con `false` la app funciona como siempre (sin login). Se activa cuando completes los pasos
de abajo y cambies ese valor a `true`.

> ⚠️ **Por qué no se activa solo:** las reglas nuevas exigen sesión y un doc `usuarios/{uid}`
> por cada persona. Si se publican antes de crear los usuarios, **nadie puede entrar**.

---

## Activación (una sola vez)

### 1. Habilitar el método de acceso
Firebase Console → **Authentication** → *Sign-in method* → **Email/Password** → *Enable* → Save.

### 2. Crear los usuarios
Firebase Console → **Authentication** → **Users** → *Add user*.
Cargá correo y contraseña para cada integrante. Anotá el **UID** de cada uno
(la columna `User UID`).

### 3. Crear el perfil con el rol
Firebase Console → **Firestore Database** → *Start collection* → ID: `usuarios`
→ *Document ID*: el **UID** del usuario → campos:

| Campo | Tipo | Valor |
|---|---|---|
| `rol` | string | `admin` o `lector` |
| `email` | string | el correo del usuario |
| `nombre` | string | nombre para mostrar (opcional) |

Repetí para cada usuario. **Sin este doc el usuario entra pero queda como `lector`** (y,
con las reglas publicadas, no podrá leer nada porque el perfil es la base del permiso).

Al menos uno tiene que ser `admin` para poder administrar el resto.

### 4. Publicar las reglas
Firebase Console → **Firestore Database** → pestaña **Rules** → pegá el contenido de
`firestore.rules` → **Publish**.

### 5. Activar en la app
En `index.html` cambiar:

```js
const SEGURIDAD_ACTIVA = false;   // → true
```

y desplegar (push a `main`, Vercel redeploya). A partir de ahí la web pide correo y
contraseña.

---

## Uso diario

- **Entrar:** correo + contraseña. Si no hay sesión, aparece la pantalla de login.
- **Salir:** botón **Salir** arriba a la derecha (muestra correo y rol).
- El rol se lee de `usuarios/{uid}` al iniciar sesión.

## Administrar usuarios después

- **Nuevo integrante:** pasos 2 y 3 (crear en Authentication + doc en `usuarios`).
- **Pasar a alguien de lector a admin:** editar su doc `usuarios/{uid}` y cambiar `rol`.
- **Quitar acceso:** borrar el usuario en Authentication (y su doc en `usuarios`).
- El cambio de rol aplica al **volver a iniciar sesión** (o al recargar la página).

## Notas técnicas

- Las reglas usan `get()`/`exists()` sobre `usuarios/{uid}`: cada lectura cuenta como
  lectura de documento facturable (una por request). A esta escala es despreciable.
- **Todo** usuario necesita su doc en `usuarios`; si falta, cae a `lector` y, con las
  reglas activas, no puede leer los datos.
- El módulo **no** toca los datos existentes: no hay migración. Los datos ya cargados
  siguen ahí y se ven igual.
- El plan gratuito de Firestore tiene cuota diaria de lecturas/escrituras. Si se agota
  (error `429` / `resource-exhausted`), esperá el reinicio de la cuota; el módulo no
  cambia nada de eso.

## Volver atrás (rollback)

Si algo sale mal y necesitás abrir de nuevo:

1. Cambiar `SEGURIDAD_ACTIVA = true` → `false` y desplegar.
2. En Firestore → Rules, volver a la versión abierta:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} { allow read, write: if true; }
  }
}
```

> Ese modo abierto es inseguro: cualquiera con el project ID puede leer y escribir.
> Usalo solo como puente mientras arreglás el acceso.
