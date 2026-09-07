# Guardias Web App — Punto de entrada para el agente

> **Para el agente (Sonnet): lee este fichero primero y luego construye la app.**
> Tienes toda la información necesaria en `webapp/docs/`. **No preguntes al usuario**;
> toma las decisiones que falten siguiendo estos documentos y el criterio "igual o mejor
> que la app de escritorio actual".

Esta carpeta contendrá la **versión web** del *Generador de Guardias de Soporte*, que
sustituye a la app de escritorio en `../desktop/` (Python + Tkinter). La app de escritorio
sigue funcionando y es la **fuente de verdad funcional**: la web debe replicar TODO lo que
hace, con la misma lógica de datos, y puede mejorar la UX aprovechando el stack web.

## Orden de lectura de la documentación

1. `docs/00-OVERVIEW.md` — Qué es la app, alcance y objetivos.
2. `docs/01-STACK-AND-ARCHITECTURE.md` — Stack elegido, estructura de carpetas, cómo arrancar.
3. `docs/02-DATA-MODELS.md` — Formatos de datos y ficheros (compatibles con la app de escritorio).
4. `docs/03-FUNCTIONAL-SPEC.md` — Especificación funcional completa, pantalla por pantalla.
5. `docs/04-BACKEND-API.md` — Contrato REST completo del backend.
6. `docs/05-GOOGLE-CALENDAR.md` — Integración OAuth2 + sincronización bidireccional.
7. `docs/06-GPT-INTEGRATION.md` — Generación de guardias con GPT (prompt y parsing).
8. `docs/07-UI-UX.md` — Guía visual (colores, layout) para parecerse a la de escritorio.
9. `docs/08-BUILD-PLAN.md` — Plan de construcción paso a paso (síguelo en orden).

## Regla de oro

Cualquier duda de comportamiento se resuelve mirando el código de referencia en
`../desktop/` (indicado en cada documento con rutas concretas) y respetando los
**formatos de datos existentes** para que ambas apps puedan convivir sobre los mismos
ficheros JSON si se desea.
