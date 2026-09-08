import { Router } from "express";
import { z } from "zod";
import {
  hasCredentialsFile,
  isAuthenticated,
  isConfigured,
  getGoogleConfig,
  getAuthUrl,
  handleOAuthCallback,
  listCalendars,
  saveGoogleConfig,
  syncPush,
  syncPull
} from "../services/googleCalendar";

export const googleRouter = Router();

googleRouter.get("/status", (_req, res) => {
  res.json({
    credentials_found: hasCredentialsFile(),
    configured: isConfigured(),
    authenticated: isAuthenticated(),
    calendar: getGoogleConfig()
  });
});

googleRouter.get("/oauth/login", (_req, res) => {
  try {
    res.json({ url: getAuthUrl() });
  } catch (e: any) {
    res.status(503).json({ error: e.message });
  }
});

googleRouter.get("/oauth/callback", async (req, res) => {
  const code = typeof req.query.code === "string" ? req.query.code : undefined;
  if (!code) return res.status(400).send("Falta el parámetro 'code'");

  try {
    await handleOAuthCallback(code);
    res.send(
      "<html><body><h2>Autenticación completada</h2><p>Ya puedes cerrar esta ventana y volver a la app.</p></body></html>"
    );
  } catch (e: any) {
    res.status(500).send(`<html><body><h2>Error de autenticación</h2><p>${e.message}</p></body></html>`);
  }
});

googleRouter.get("/calendars", async (_req, res) => {
  try {
    const calendars = await listCalendars();
    res.json(calendars);
  } catch (e: any) {
    res.status(503).json({ error: e.message });
  }
});

const configSchema = z.object({
  calendar_id: z.string().min(1),
  calendar_name: z.string().min(1),
  access_role: z.string().min(1)
});

googleRouter.post("/config", (req, res) => {
  const parsed = configSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "Payload inválido", details: parsed.error.flatten() });
  }
  const { calendar_id, calendar_name, access_role } = parsed.data;
  res.json(saveGoogleConfig(calendar_id, calendar_name, access_role));
});

googleRouter.post("/sync/push", async (_req, res) => {
  try {
    res.json(await syncPush());
  } catch (e: any) {
    res.status(503).json({ error: e.message });
  }
});

googleRouter.post("/sync/pull", async (_req, res) => {
  try {
    res.json(await syncPull());
  } catch (e: any) {
    res.status(503).json({ error: e.message });
  }
});
