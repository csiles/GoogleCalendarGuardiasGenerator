# Guardias Web App

Versión web (Node.js + React) del *Generador de Guardias de Soporte*, que sustituye a la app de
escritorio en `../desktop/`. **Estado: implementada y verificada en local** (backend, frontend,
integración Google Calendar y GPT).

## ⚠️ Importante: instalar dependencias en disco local

Este proyecto puede vivir dentro de una unidad de red/compartida (p.ej. una Unidad compartida de
Google Drive). `npm install` crea decenas de miles de ficheros pequeños, lo cual es **extremadamente
lento o puede colgarse sin remedio** sobre unidades sincronizadas. Si tu carpeta de trabajo está en
una unidad así:

1. Copia (o trabaja directamente sobre) una réplica local del proyecto en disco local
   (p.ej. `C:\...\GoogleCalendarGuardiasGenerator`).
2. Ejecuta ahí `npm install` (ver pasos abajo).
3. `node_modules` está en `.gitignore`, así que no afecta al control de versiones; puedes
   sincronizar el resto del código con la unidad compartida con normalidad.

## Requisitos

- Node.js 20+ y npm.
- Opcional para Google Calendar: credenciales OAuth de Google Cloud Console.
- Opcional para "Crear desde GPT": una API key de OpenAI.

## Instalación

```powershell
cd webapp
npm run install:all
copy .env.example .env
# Edita .env y rellena OPENAI_API_KEY si vas a usar "Crear desde GPT"
```

Para Google Calendar (opcional): coloca el fichero de credenciales OAuth descargado de Google
Cloud Console en `server/data/google_credentials.json`, y registra como "Authorized redirect URI"
la URL `http://localhost:3001/api/google/oauth/callback` (o la que configures en `.env`).

## Desarrollo

```powershell
npm run dev
```

Levanta backend (`http://localhost:3001`) y frontend (`http://localhost:5173`, con proxy de
`/api` hacia el backend). Abre `http://localhost:5173`.

## Producción

```powershell
npm run build
npm start
```

`npm start` levanta el backend en `http://localhost:3001`, sirviendo también el build estático
del frontend (`client/dist`) para esa misma URL.

## Estructura

Ver `docs/01-STACK-AND-ARCHITECTURE.md` para el detalle completo. Resumen:

- `server/` — API REST en Express + TypeScript. Datos en `server/data/` (tecnicos.txt,
  festivos.txt, calendarios.json, y ficheros de Google generados en tiempo de ejecución).
- `client/` — SPA en React + Vite + TypeScript.
- `docs/` — especificación funcional y técnica completa usada para construir esta app.

## Documentación

1. `docs/00-OVERVIEW.md` — Qué es la app, alcance y objetivos.
2. `docs/01-STACK-AND-ARCHITECTURE.md` — Stack, estructura de carpetas, cómo arrancar.
3. `docs/02-DATA-MODELS.md` — Formatos de datos y ficheros.
4. `docs/03-FUNCTIONAL-SPEC.md` — Especificación funcional completa, pantalla por pantalla.
5. `docs/04-BACKEND-API.md` — Contrato REST completo del backend.
6. `docs/05-GOOGLE-CALENDAR.md` — Integración OAuth2 + sincronización bidireccional.
7. `docs/06-GPT-INTEGRATION.md` — Generación de guardias con GPT (prompt y parsing).
8. `docs/07-UI-UX.md` — Guía visual (colores, layout).
9. `docs/08-BUILD-PLAN.md` — Plan de construcción por fases (ya ejecutado).

