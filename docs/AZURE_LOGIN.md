# Marcador WIG en Azure — acceso con login de empresa

Reemplaza la restricción por IP por **login de Microsoft (Entra ID)**: el sitio
queda publicado en internet, pero solo entran cuentas **@caobagroup.com**.
Supersede los pasos de IP de `PUESTA-EN-MARCHA-AZURE.md` (Paso 3 y la prueba de
403). El resto de ese documento (publicar cada lunes, proceso semanal) no cambia.

> **Requiere el tier Standard** de Static Web Apps (el plan Free no permite
> proveedores de identidad personalizados ni rutas con roles).

---

## La decisión a tomar antes de empezar: ¿cómo se ven las pantallas de la oficina?

El login es ideal para **acceso remoto** (alguien abre el marcador desde casa o
el celular). Pero una **TV de pared 24/7** con login es incómoda: la sesión de
Azure caduca (~8 h) y habría que volver a iniciar sesión.

- **Recomendado:** las TVs de la oficina leen del **PGX por la LAN** (nginx, sin
  login, como en la arquitectura original); Azure con login es la copia para ver
  el marcador **fuera** de la oficina. Cero fricción en las pantallas.
- **Alternativa (Azure-para-todo):** las TVs también usan Azure; se crea una
  cuenta de “display” dedicada y se acepta volver a iniciar sesión cada tantas
  horas (o se mantiene la sesión con un kiosko que no se reinicie).

Este documento configura el login en Azure; sirve para ambos modelos.

---

## Pasos en el portal (una sola vez, ~20 min)

### 1. Anotar el Tenant ID
Portal → **Microsoft Entra ID** → **Overview** → copiar **Tenant ID**.

### 2. Registrar la app de login
Entra ID → **App registrations** → **New registration**:
- **Name:** `Marcador WIG`
- **Supported account types:** *Accounts in this organizational directory only*
  (un solo tenant = solo caobagroup; esto es lo que bloquea cuentas externas).
- **Redirect URI:** tipo **Web** →
  `https://<TU-SITIO>.azurestaticapps.net/.auth/login/aad/callback`
- **Register.** Copiar el **Application (client) ID**.

### 3. Crear el secreto
En la app recién creada → **Certificates & secrets** → **New client secret** →
copiar el **Value** (no el Secret ID; el Value solo se ve una vez).

### 4. Guardar id y secreto en la Static Web App
Portal → tu **Static Web App** → **Settings → Environment variables**
(Application settings) → agregar dos:
- `AAD_CLIENT_ID` = el Application (client) ID del paso 2
- `AAD_CLIENT_SECRET` = el Value del paso 3

### 5. Poner el Tenant ID en el repo
En `web/staticwebapp.config.json`, reemplazar `REEMPLAZAR-TENANT-ID` por el
Tenant ID del paso 1 (queda el issuer
`https://login.microsoftonline.com/<TENANT_ID>/v2.0`). Commit + push a `main`.
El workflow se niega a publicar mientras el placeholder siga ahí (a propósito).

### 6. Probar
- Abrir la URL del sitio en una ventana de incógnito → debe redirigir al login
  de Microsoft → una cuenta **@caobagroup.com** entra y ve el marcador.
- Probar con una cuenta personal (gmail/outlook ajeno): debe **rechazarla**.
- Cerrar sesión: `https://<TU-SITIO>.azurestaticapps.net/logout`.

---

## Limitar a personas específicas (opcional)

Por defecto entra **cualquier** cuenta del tenant (@caobagroup.com). Para
restringir a una lista concreta:

1. Entra ID → **Enterprise applications** → `Marcador WIG` → **Properties** →
   *Assignment required?* = **Yes**.
2. **Users and groups** → **Add user/group** → agregar solo a quienes deben ver
   el marcador (o un grupo de seguridad, p. ej. `WIG-Viewers`).

Quien no esté asignado verá “necesita aprobación / no tiene acceso” tras el login.

---

## Notas

- **Costo:** ~$9/mes (Standard), contra el crédito de la suscripción.
- **La TV de la oficina (modelo recomendado):** sin cambios — sigue leyendo del
  PGX por LAN, sin login. Ver `deploy/setup-wig.sh`.
- **Si una cuenta no entra:** revisar que el redirect URI del paso 2 coincida
  exactamente con el dominio real del sitio, y que `AAD_CLIENT_ID/SECRET` estén
  en las Application settings (no en GitHub).
- **Rotar el secreto:** los client secrets de Entra caducan (máx. 24 meses).
  Antes de que venza, crear uno nuevo (paso 3) y actualizar `AAD_CLIENT_SECRET`.
