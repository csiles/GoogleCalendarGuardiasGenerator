import fs from "node:fs";
import path from "node:path";
import { google } from "googleapis";
import { config } from "../config";
import { calendarStore } from "./store";
import { getTecnicoNombres, loadTecnicos } from "./tecnicos";
import { generateEventId } from "./store";
import { GoogleConfig } from "../types";

const SCOPES = ["https://www.googleapis.com/auth/calendar"];

const COLOR_MAP: Record<string, string> = {
  "#3498db": "9",
  "#e74c3c": "11",
  "#2ecc71": "10",
  "#f39c12": "6",
  "#9b59b6": "3",
  "#1abc9c": "7"
};

interface CredentialsFile {
  installed?: { client_id: string; client_secret: string };
  web?: { client_id: string; client_secret: string };
}

function readJsonIfExists<T>(filePath: string): T | null {
  if (!fs.existsSync(filePath)) return null;
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return null;
  }
}

function getOAuthClient() {
  const creds = readJsonIfExists<CredentialsFile>(config.googleCredentialsFile);
  if (!creds) {
    throw new Error(
      `No se encontró el fichero de credenciales de Google en ${config.googleCredentialsFile}`
    );
  }
  const clientInfo = creds.installed || creds.web;
  if (!clientInfo) throw new Error("Fichero de credenciales de Google con formato inesperado");

  const client = new google.auth.OAuth2(
    clientInfo.client_id,
    clientInfo.client_secret,
    config.googleOAuthRedirect
  );

  const token = readJsonIfExists<Record<string, unknown>>(config.googleTokenFile);
  if (token) client.setCredentials(token);

  client.on("tokens", (tokens) => {
    const merged = { ...(token || {}), ...tokens };
    fs.mkdirSync(path.dirname(config.googleTokenFile), { recursive: true });
    fs.writeFileSync(config.googleTokenFile, JSON.stringify(merged, null, 2), "utf-8");
  });

  return client;
}

export function hasCredentialsFile(): boolean {
  return fs.existsSync(config.googleCredentialsFile);
}

export function isAuthenticated(): boolean {
  const token = readJsonIfExists<Record<string, unknown>>(config.googleTokenFile);
  return !!token && !!token.access_token;
}

export function getGoogleConfig(): GoogleConfig | null {
  return readJsonIfExists<GoogleConfig>(config.googleConfigFile);
}

export function isConfigured(): boolean {
  return getGoogleConfig() !== null;
}

export function getAuthUrl(): string {
  const client = getOAuthClient();
  return client.generateAuthUrl({
    access_type: "offline",
    prompt: "consent",
    scope: SCOPES
  });
}

export async function handleOAuthCallback(code: string): Promise<void> {
  const client = getOAuthClient();
  const { tokens } = await client.getToken(code);
  fs.mkdirSync(path.dirname(config.googleTokenFile), { recursive: true });
  fs.writeFileSync(config.googleTokenFile, JSON.stringify(tokens, null, 2), "utf-8");
}

function getCalendarClient() {
  const auth = getOAuthClient();
  return google.calendar({ version: "v3", auth });
}

export interface CalendarListItem {
  id: string;
  name: string;
  access_role: string;
  is_primary: boolean;
  description: string;
  timezone: string;
}

export async function listCalendars(): Promise<CalendarListItem[]> {
  const calendar = getCalendarClient();
  const { data } = await calendar.calendarList.list();
  const items = data.items || [];

  return items
    .filter((cal) => cal.accessRole === "owner" || cal.accessRole === "writer")
    .map((cal) => ({
      id: cal.id!,
      name: cal.summary || "(sin nombre)",
      access_role: cal.accessRole!,
      is_primary: !!cal.primary,
      description: cal.description || "",
      timezone: cal.timeZone || "Europe/Madrid"
    }));
}

export function saveGoogleConfig(calendarId: string, calendarName: string, accessRole: string): GoogleConfig {
  const cfg: GoogleConfig = {
    calendar_id: calendarId,
    calendar_name: calendarName,
    access_role: accessRole,
    configured_at: new Date().toISOString()
  };
  fs.mkdirSync(path.dirname(config.googleConfigFile), { recursive: true });
  fs.writeFileSync(config.googleConfigFile, JSON.stringify(cfg, null, 2), "utf-8");
  return cfg;
}

function addDaysIso(fecha: string, days: number): string {
  const d = new Date(`${fecha}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export interface PushStats {
  total: number;
  created: number;
  updated: number;
  errors: number;
  errores_detalle: { evento: string; fecha?: string; error: string }[];
  calendar_url: string | null;
}

export async function syncPush(): Promise<PushStats> {
  const cfg = getGoogleConfig();
  if (!cfg) throw new Error("Debe configurar un calendario primero");

  const calendar = getCalendarClient();
  const eventos = calendarStore.getAllEvents();
  const tecnicoColores = new Map(loadTecnicos().map((t) => [t.nombre, t.color] as const));

  const stats: PushStats = { total: eventos.length, created: 0, updated: 0, errors: 0, errores_detalle: [], calendar_url: null };

  for (const evento of eventos) {
    try {
      const colorHex = evento.tecnico ? tecnicoColores.get(evento.tecnico) : undefined;
      const colorId = colorHex ? COLOR_MAP[colorHex.toLowerCase()] : undefined;

      const body = {
        summary: evento.titulo,
        description: evento.descripcion || "",
        start: { date: evento.fecha, timeZone: "Europe/Madrid" },
        end: { date: addDaysIso(evento.fecha, 1), timeZone: "Europe/Madrid" },
        source: {
          title: "Guardias Generator",
          url: "https://github.com/csiles/GoogleCalendarGuardiasGenerator"
        },
        ...(colorId ? { colorId } : {})
      };

      let result;
      if (evento.google_event_id) {
        const { data } = await calendar.events.update({
          calendarId: cfg.calendar_id,
          eventId: evento.google_event_id,
          requestBody: body
        });
        result = data;
        stats.updated += 1;
      } else {
        const existingId = await findExistingEvent(calendar, cfg.calendar_id, evento.fecha, evento.titulo);
        if (existingId) {
          const { data } = await calendar.events.update({
            calendarId: cfg.calendar_id,
            eventId: existingId,
            requestBody: body
          });
          result = data;
          stats.updated += 1;
        } else {
          const { data } = await calendar.events.insert({ calendarId: cfg.calendar_id, requestBody: body });
          result = data;
          stats.created += 1;
        }
      }

      calendarStore.updateGoogleEventId(evento.fecha, evento.id, result.id!, result.htmlLink || undefined);
    } catch (e: any) {
      stats.errors += 1;
      stats.errores_detalle.push({ evento: evento.titulo, fecha: evento.fecha, error: e.message || String(e) });
    }
  }

  calendarStore.save();
  stats.calendar_url = `https://calendar.google.com/calendar/embed?src=${encodeURIComponent(cfg.calendar_id)}`;
  return stats;
}

async function findExistingEvent(
  calendar: ReturnType<typeof getCalendarClient>,
  calendarId: string,
  fecha: string,
  titulo: string
): Promise<string | null> {
  try {
    const timeMin = `${fecha}T00:00:00Z`;
    const timeMax = `${addDaysIso(fecha, 1)}T00:00:00Z`;
    const { data } = await calendar.events.list({
      calendarId,
      timeMin,
      timeMax,
      singleEvents: true
    });
    const match = (data.items || []).find((ev) => (ev.summary || "").toLowerCase() === titulo.toLowerCase());
    return match?.id || null;
  } catch {
    return null;
  }
}

export interface PullStats {
  total_descargados: number;
  importados_tecnico_activo: number;
  importados_tecnico_eliminado: number;
  importados_genericos: number;
}

export async function syncPull(): Promise<PullStats> {
  const cfg = getGoogleConfig();
  if (!cfg) throw new Error("Debe configurar un calendario primero");

  const calendar = getCalendarClient();

  const now = new Date();
  const timeMin = new Date(now);
  timeMin.setDate(timeMin.getDate() - 365);
  const timeMax = new Date(now);
  timeMax.setDate(timeMax.getDate() + 180);

  const { data } = await calendar.events.list({
    calendarId: cfg.calendar_id,
    timeMin: timeMin.toISOString(),
    timeMax: timeMax.toISOString(),
    maxResults: 2500,
    singleEvents: true,
    orderBy: "startTime"
  });

  const items = data.items || [];
  const tecnicosActivos = new Set(getTecnicoNombres());

  const stats: PullStats = {
    total_descargados: items.length,
    importados_tecnico_activo: 0,
    importados_tecnico_eliminado: 0,
    importados_genericos: 0
  };

  for (const ev of items) {
    const fecha = ev.start?.date || (ev.start?.dateTime ? ev.start.dateTime.slice(0, 10) : null);
    if (!fecha) continue;

    const titulo = ev.summary || "Sin título";
    const match = titulo.trim().match(/^Guardia\s*-\s*(.+)$/);
    const tecnico = match ? match[1].trim() : null;
    const tipo = tecnico ? "guardia" : "otro";

    const evento = {
      id: generateEventId(fecha, titulo),
      titulo,
      tecnico,
      tipo: tipo as "guardia" | "otro",
      descripcion: ev.description || "",
      all_day: true,
      origen: "google_pull" as const,
      google_event_id: ev.id || undefined,
      google_link: ev.htmlLink || undefined
    };

    calendarStore.addEvent(fecha, evento);

    if (tecnico && tecnicosActivos.has(tecnico)) stats.importados_tecnico_activo += 1;
    else if (tecnico) stats.importados_tecnico_eliminado += 1;
    else stats.importados_genericos += 1;
  }

  calendarStore.save();
  return stats;
}
