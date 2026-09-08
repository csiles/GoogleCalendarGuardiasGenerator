export type TipoGuardia = "guardia" | "media_guardia" | "otro";

export interface Tecnico {
  nombre: string;
  color: string;
}

export interface Festivo {
  fecha: string;
  anotacion: string;
}

export interface EventoConFecha {
  id: string;
  fecha: string;
  titulo: string;
  tecnico: string | null;
  tipo: TipoGuardia;
  descripcion?: string;
  all_day?: boolean;
  origen?: string;
  google_event_id?: string;
  google_link?: string;
}

export interface Estadisticas {
  total_meses_con_datos: number;
  total_eventos: number;
  eventos_por_tipo: Record<string, number>;
  fuentes_csv: number;
  ultima_actualizacion: string;
}

export interface GoogleConfig {
  calendar_id: string;
  calendar_name: string;
  access_role: string;
  configured_at: string;
}

export interface GoogleStatus {
  credentials_found: boolean;
  configured: boolean;
  authenticated: boolean;
  calendar: GoogleConfig | null;
}

export interface GoogleCalendarListItem {
  id: string;
  name: string;
  access_role: string;
  is_primary: boolean;
  description: string;
  timezone: string;
}

export interface PushStats {
  total: number;
  created: number;
  updated: number;
  errors: number;
  errores_detalle: { evento: string; fecha?: string; error: string }[];
  calendar_url: string | null;
}

export interface PullStats {
  total_descargados: number;
  importados_tecnico_activo: number;
  importados_tecnico_eliminado: number;
  importados_genericos: number;
}

export interface GptStatus {
  configured: boolean;
  model: string;
}

export interface AsignacionGpt {
  fecha: string;
  tecnico: string;
  tipo?: TipoGuardia;
}

export interface GptGenerarResponse {
  asignaciones: AsignacionGpt[];
  prompt_enviado: string;
}

export interface ImportCsvStats {
  total: number;
  importados: number;
  duplicados: number;
  errores: number;
  errores_detalle: { fila?: number; error: string }[];
}
