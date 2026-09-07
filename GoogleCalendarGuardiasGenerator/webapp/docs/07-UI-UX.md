# 07 — Guía visual (UI/UX)

Objetivo: **parecerse a la app de escritorio** (paleta y estructura) pero con acabado web
moderno. Aprovecha el web para mejorar microinteracciones, transiciones y responsividad.

## Paleta (extraída de la app de escritorio)

| Uso | Color |
|-----|-------|
| Cabeceras / barras oscuras | `#2c3e50` |
| Barras secundarias / navegación | `#34495e` |
| Fondo app / paneles claros | `#ecf0f1` |
| Azul primario (acciones) | `#3498db` |
| Verde (confirmar / actualizar) | `#2ecc71` |
| Rojo (borrar / peligro) | `#e74c3c` |
| Naranja (sync local→Google) | `#e67e22` |
| Verde azulado (sync Google→local) | `#16a085` |
| Morado (GPT / login config) | `#9b59b6` |
| Gris neutro (cancelar) | `#95a5a6` |
| Fin de semana (fondo celda) | `#ffe6e6` |
| Festivo (fondo celda) | `#fff3cd` (texto anotación `#856404`) |
| Técnico eliminado (💀) | fondo `#000000`, texto `#ffffff`, prefijo `💀 ` |

Colores de técnico: vienen de `tecnicos.txt` (hex por técnico). Úsalos para chips, celdas y filas
de estadísticas. Texto blanco sobre el color del técnico.

Define todo esto en `client/src/styles/theme.css` como variables CSS.

## Tipografía
- La de escritorio usa Arial/Segoe UI. En web: system font stack
  (`-apple-system, Segoe UI, Roboto, Arial, sans-serif`). Monoespaciada para el textarea de GPT.

## Layout general
- Barra superior con **título** (`Gestión de Guardias - Soporte IT-Leisure`) y **pestañas**
  "Generar Guardias" / "Ver Calendarios". Pestaña activa resaltada en azul `#3498db` con texto blanco.
- Contenido a ancho completo. Pensado para pantalla grande (la de escritorio abre a 1600×850),
  pero ✨ que sea usable en pantallas menores (scroll/colapso).

## Generador — detalles visuales
- Panel de control en tarjetas (`LabelFrame` en escritorio) con borde suave.
- Chips de técnico arrastrables con color de fondo del técnico, cursor "grab".
- Calendario grande a la izquierda, panel de estadísticas a la derecha (~250px).
- Celdas de día muestran número arriba-izquierda; asignación como bloque de color con el nombre.
- Festivo: etiqueta pequeña con anotación arriba-derecha.
- ✨ Feedback al soltar (highlight del día destino), animación breve al asignar.

## Visualizador — detalles visuales
- Barra de herramientas: **izquierda** etiqueta + botón "Login/config"; **centro** grupo de 4
  botones (Importar CSV, Actualizar, Sincro: Local → Google [naranja], Sincro: Google → Local [verde azulado]).
- Barra de navegación con paleta de técnicos arrastrables + botones de salto temporal.
- Rejilla de ~7 meses, cada uno como tarjeta con su mini-calendario + panel de estadísticas.
- Barra de estado inferior oscura con métricas.

## Overlay GPT
- Fondo oscurecido semitransparente cubriendo toda la ventana + tarjeta centrada (~720×620).
- Cabecera oscura `#2c3e50` con título y botón ✕.
- Vista 1: textarea monoespaciado grande + botones "Enviar a GPT" (morado) y "Cancelar" (gris).
  Estado "Generando…" con feedback (spinner ✨).
- Vista 2: tabla (Fecha/Técnico/Tipo) + botones "Guardar en calendario local" (verde) y "Descartar" (rojo).

## Modal de configuración Google
- Lista de calendarios con icono según tipo (propio 👤 / compartido 👥) y permiso (🔒 owner / ✏️ writer),
  marca `[PRINCIPAL]` para el primario. Detalles del seleccionado y botón "Seleccionar".
- Estado de carga con spinner. Manejo de error con botón "Reintentar".
- ✨ En web, el login OAuth abre una ventana/pestaña de Google; tras el callback, refresca el estado.

## Notificaciones
- Sustituye los `messagebox` de escritorio por **toasts**/modales web no bloqueantes cuando aplique
  (éxito, error, resúmenes de sync/import). Los resúmenes de sync pueden ir en un modal con detalle.

## Accesibilidad y toque creativo (✨ libre)
- Puedes añadir: modo oscuro, atajos de teclado, tooltips, contadores animados, arrastrar con
  teclado (dnd-kit lo permite), indicador de "cambios sin sincronizar", etc. Siempre que **no**
  se pierda ninguna funcionalidad del checklist de `03-FUNCTIONAL-SPEC.md`.
