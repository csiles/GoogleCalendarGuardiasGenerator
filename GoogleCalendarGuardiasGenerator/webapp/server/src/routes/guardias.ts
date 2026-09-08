import { Router } from "express";
import { z } from "zod";
import { calendarStore, generateEventId } from "../services/store";
import { Evento, TipoGuardia } from "../types";

export const guardiasRouter = Router();

const fechaRegex = /^\d{4}-\d{2}-\d{2}$/;

function tituloPrefix(tipo: TipoGuardia | undefined): string {
  return tipo === "media_guardia" ? "Media Guardia" : "Guardia";
}

guardiasRouter.get("/raw", (_req, res) => {
  res.json(calendarStore.getRaw());
});

guardiasRouter.get("/stats", (_req, res) => {
  res.json(calendarStore.getStatistics());
});

guardiasRouter.get("/", (req, res) => {
  const from = typeof req.query.from === "string" ? req.query.from : undefined;
  const to = typeof req.query.to === "string" ? req.query.to : undefined;
  res.json(calendarStore.getEventsInRange(from, to));
});

const asignacionSchema = z.object({
  fecha: z.string().regex(fechaRegex, "fecha debe ser YYYY-MM-DD"),
  tecnico: z.string().min(1),
  tipo: z.enum(["guardia", "media_guardia", "otro"]).optional(),
  anotacion: z.string().optional()
});

guardiasRouter.post("/", (req, res) => {
  const parsed = asignacionSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Payload inválido", details: parsed.error.flatten() });
  }
  const { fecha, tecnico, tipo = "guardia", anotacion } = parsed.data;

  const prefix = tituloPrefix(tipo);
  const titulo = anotacion?.trim()
    ? `${prefix} ${anotacion.trim()} - ${tecnico}`
    : `${prefix} - ${tecnico}`;

  const evento: Evento = {
    id: generateEventId(fecha, titulo),
    titulo,
    tecnico,
    tipo,
    descripcion: "",
    all_day: true,
    origen: "manual_edit",
    fecha_edicion: new Date().toISOString()
  };

  calendarStore.clearDay(fecha);
  calendarStore.addEvent(fecha, evento);
  calendarStore.save();

  res.json({ ...evento, fecha });
});

guardiasRouter.delete("/mes/:yyyymm", (req, res) => {
  const { yyyymm } = req.params;
  if (!/^\d{4}-\d{2}$/.test(yyyymm)) {
    return res.status(400).json({ error: "Formato de mes inválido, use YYYY-MM" });
  }
  calendarStore.deleteMonth(yyyymm);
  calendarStore.save();
  res.json({ ok: true });
});

guardiasRouter.delete("/:fecha", (req, res) => {
  const { fecha } = req.params;
  if (!fechaRegex.test(fecha)) {
    return res.status(400).json({ error: "Formato de fecha inválido, use YYYY-MM-DD" });
  }
  calendarStore.deleteDay(fecha);
  calendarStore.save();
  res.json({ ok: true });
});

const bulkSchema = z.object({
  asignaciones: z.array(asignacionSchema),
  sobrescribirDia: z.boolean().optional().default(true),
  origen: z.enum(["manual_edit", "csv_import", "google_pull", "gpt"]).optional().default("gpt")
});

guardiasRouter.post("/bulk", (req, res) => {
  const parsed = bulkSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Payload inválido", details: parsed.error.flatten() });
  }
  const { asignaciones, sobrescribirDia, origen } = parsed.data;

  let guardados = 0;
  let ignorados = 0;

  for (const asignacion of asignaciones) {
    const { fecha, tecnico, tipo = "guardia" } = asignacion;
    if (!fechaRegex.test(fecha) || !tecnico) {
      ignorados += 1;
      continue;
    }

    const prefix = tituloPrefix(tipo);
    const titulo = `${prefix} - ${tecnico}`;

    if (sobrescribirDia) calendarStore.clearDay(fecha);

    const evento: Evento = {
      id: generateEventId(fecha, titulo),
      titulo,
      tecnico,
      tipo,
      descripcion: "",
      all_day: true,
      origen,
      fecha_edicion: new Date().toISOString()
    };

    if (calendarStore.addEvent(fecha, evento)) {
      guardados += 1;
    } else {
      ignorados += 1;
    }
  }

  calendarStore.save();
  res.json({ guardados, ignorados });
});

guardiasRouter.post("/reload", (_req, res) => {
  calendarStore.reload();
  res.json(calendarStore.getStatistics());
});
