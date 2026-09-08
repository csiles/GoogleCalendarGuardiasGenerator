import { Router } from "express";
import { z } from "zod";
import { config } from "../config";
import { loadFestivos } from "../services/festivos";
import {
  REGLAS_TEXT_DEFAULT,
  isConfigured,
  buildPrompt,
  generarGuardias,
  parseRespuesta
} from "../services/gpt";

export const gptRouter = Router();

gptRouter.get("/status", (_req, res) => {
  res.json({ configured: isConfigured(), model: config.openaiModel });
});

gptRouter.get("/reglas-default", (_req, res) => {
  res.json({ reglas: REGLAS_TEXT_DEFAULT });
});

const generarSchema = z.object({
  instrucciones: z.string().min(1),
  fecha_inicio: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  fecha_fin: z.string().regex(/^\d{4}-\d{2}-\d{2}$/)
});

gptRouter.post("/generar", async (req, res) => {
  const parsed = generarSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Payload inválido", details: parsed.error.flatten() });
  }
  const { instrucciones, fecha_inicio, fecha_fin } = parsed.data;

  if (!isConfigured()) {
    return res.status(503).json({ error: "OPENAI_API_KEY no configurada" });
  }

  try {
    const festivosRango = loadFestivos().filter((f) => f.fecha >= fecha_inicio && f.fecha <= fecha_fin);
    const prompt = buildPrompt(instrucciones, festivosRango, fecha_inicio, fecha_fin);
    const respuestaTexto = await generarGuardias(prompt);
    const asignaciones = parseRespuesta(respuestaTexto);

    res.json({ asignaciones, prompt_enviado: prompt });
  } catch (e: any) {
    res.status(502).json({ error: e.message || "Error generando guardias con GPT" });
  }
});
