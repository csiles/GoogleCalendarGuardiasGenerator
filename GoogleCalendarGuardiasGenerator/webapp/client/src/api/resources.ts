import { api } from "./client";
import {
  Tecnico,
  Festivo,
  EventoConFecha,
  Estadisticas,
  GoogleStatus,
  GoogleCalendarListItem,
  GoogleConfig,
  PushStats,
  PullStats,
  GptStatus,
  GptGenerarResponse,
  ImportCsvStats,
  AsignacionGpt
} from "../types";

export const getTecnicos = () => api.get<Tecnico[]>("/tecnicos");
export const getFestivos = () => api.get<Festivo[]>("/festivos");

export const getGuardias = (from?: string, to?: string) => {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString();
  return api.get<EventoConFecha[]>(`/guardias${qs ? `?${qs}` : ""}`);
};

export const getGuardiasStats = () => api.get<Estadisticas>("/guardias/stats");

export const asignarGuardia = (payload: {
  fecha: string;
  tecnico: string;
  tipo?: string;
  anotacion?: string;
}) => api.post<EventoConFecha>("/guardias", payload);

export const eliminarGuardiaDia = (fecha: string) => api.delete<{ ok: boolean }>(`/guardias/${fecha}`);

export const eliminarGuardiasMes = (yyyymm: string) =>
  api.delete<{ ok: boolean }>(`/guardias/mes/${yyyymm}`);

export const guardarBulk = (asignaciones: AsignacionGpt[], origen = "gpt") =>
  api.post<{ guardados: number; ignorados: number }>("/guardias/bulk", {
    asignaciones,
    sobrescribirDia: true,
    origen
  });

export const reloadGuardias = () => api.post<Estadisticas>("/guardias/reload");

export const importarCsv = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.postForm<ImportCsvStats>("/csv/import", form);
};

export const exportarCsvUrl = "/api/csv/export";

export const getGoogleStatus = () => api.get<GoogleStatus>("/google/status");
export const getGoogleLoginUrl = () => api.get<{ url: string }>("/google/oauth/login");
export const getGoogleCalendars = () => api.get<GoogleCalendarListItem[]>("/google/calendars");
export const setGoogleConfig = (payload: { calendar_id: string; calendar_name: string; access_role: string }) =>
  api.post<GoogleConfig>("/google/config", payload);
export const syncPush = () => api.post<PushStats>("/google/sync/push");
export const syncPull = () => api.post<PullStats>("/google/sync/pull");

export const getGptStatus = () => api.get<GptStatus>("/gpt/status");
export const getGptReglasDefault = () => api.get<{ reglas: string }>("/gpt/reglas-default");
export const generarConGpt = (payload: { instrucciones: string; fecha_inicio: string; fecha_fin: string }) =>
  api.post<GptGenerarResponse>("/gpt/generar", payload);
