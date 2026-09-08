export type TipoGuardia = "guardia" | "media_guardia" | "otro";
export type OrigenEvento = "manual_edit" | "csv_import" | "google_pull" | "gpt";

export interface Evento {
  id: string;
  titulo: string;
  tecnico: string | null;
  tipo: TipoGuardia;
  descripcion: string;
  all_day: boolean;
  origen: OrigenEvento;
  fecha_edicion?: string;
  fecha_importacion?: string;
  archivo_origen?: string;
  google_event_id?: string;
  google_link?: string;
}

export interface EventoConFecha extends Evento {
  fecha: string; // YYYY-MM-DD
}

export interface DiaData {
  eventos: Evento[];
}

export interface MesData {
  dias: Record<string, DiaData>;
  estadisticas_mes: {
    total_eventos: number;
    por_tipo: Record<string, number>;
  };
}

export interface FuenteCsv {
  nombre: string;
  ruta: string;
  fecha_carga: string;
  registros_importados: number;
  hash: string;
}

export interface CalendarioData {
  version: string;
  last_updated: string;
  meses: Record<string, MesData>;
  fuentes_csv: FuenteCsv[];
}

export interface Tecnico {
  nombre: string;
  color: string;
}

export interface Festivo {
  fecha: string; // YYYY-MM-DD
  anotacion: string;
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

export interface AsignacionInput {
  fecha: string;
  tecnico: string;
  tipo?: TipoGuardia;
  anotacion?: string;
}
