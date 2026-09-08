import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { config } from "../config";
import { CalendarioData, Evento, EventoConFecha, Estadisticas, MesData } from "../types";

function emptyStructure(): CalendarioData {
  return {
    version: "1.0",
    last_updated: new Date().toISOString(),
    meses: {},
    fuentes_csv: []
  };
}

function emptyMes(): MesData {
  return { dias: {}, estadisticas_mes: { total_eventos: 0, por_tipo: {} } };
}

/** Genera el mismo id determinista que la app de escritorio: MD5(`${fecha}_${titulo}`)[:16] */
export function generateEventId(fecha: string, titulo: string): string {
  return crypto.createHash("md5").update(`${fecha}_${titulo}`).digest("hex").slice(0, 16);
}

class CalendarStore {
  private data: CalendarioData;

  constructor(private filePath: string = config.calendariosFile) {
    this.data = this.load();
  }

  private load(): CalendarioData {
    if (!fs.existsSync(this.filePath)) return emptyStructure();
    try {
      const raw = fs.readFileSync(this.filePath, "utf-8");
      const parsed = JSON.parse(raw) as Partial<CalendarioData>;
      if (!parsed.meses || !parsed.fuentes_csv) return emptyStructure();
      return parsed as CalendarioData;
    } catch (e) {
      console.error(`Error cargando ${this.filePath}:`, e);
      return emptyStructure();
    }
  }

  reload(): void {
    this.data = this.load();
  }

  save(): void {
    this.data.last_updated = new Date().toISOString();
    fs.mkdirSync(path.dirname(this.filePath), { recursive: true });
    fs.writeFileSync(this.filePath, JSON.stringify(this.data, null, 2), "utf-8");
  }

  getRaw(): CalendarioData {
    return this.data;
  }

  private recomputeMonthStats(yearMonth: string): void {
    const mes = this.data.meses[yearMonth];
    if (!mes) return;
    let total = 0;
    const porTipo: Record<string, number> = {};
    for (const dia of Object.values(mes.dias)) {
      for (const ev of dia.eventos) {
        total += 1;
        const tipo = ev.tipo || "otro";
        porTipo[tipo] = (porTipo[tipo] || 0) + 1;
      }
    }
    mes.estadisticas_mes = { total_eventos: total, por_tipo: porTipo };
  }

  /** Añade un evento a un día. Evita duplicados por id. No vacía el día (usar clearDay antes si se quiere sobrescribir). */
  addEvent(fecha: string, evento: Evento): boolean {
    const yearMonth = fecha.slice(0, 7);
    const day = fecha.slice(8, 10);

    if (!this.data.meses[yearMonth]) this.data.meses[yearMonth] = emptyMes();
    const mes = this.data.meses[yearMonth];
    if (!mes.dias[day]) mes.dias[day] = { eventos: [] };

    const existingIds = mes.dias[day].eventos.map((e) => e.id);
    if (existingIds.includes(evento.id)) return false;

    mes.dias[day].eventos.push(evento);
    this.recomputeMonthStats(yearMonth);
    return true;
  }

  /** Vacía los eventos de un día concreto (usado antes de reasignar, para sobrescribir) */
  clearDay(fecha: string): void {
    const yearMonth = fecha.slice(0, 7);
    const day = fecha.slice(8, 10);
    if (this.data.meses[yearMonth]?.dias[day]) {
      this.data.meses[yearMonth].dias[day].eventos = [];
      this.recomputeMonthStats(yearMonth);
    }
  }

  deleteDay(fecha: string): void {
    this.clearDay(fecha);
  }

  deleteMonth(yearMonth: string): void {
    if (this.data.meses[yearMonth]) {
      this.data.meses[yearMonth] = emptyMes();
    }
  }

  getAllEvents(): EventoConFecha[] {
    const all: EventoConFecha[] = [];
    for (const [yearMonth, mes] of Object.entries(this.data.meses)) {
      for (const [day, diaData] of Object.entries(mes.dias)) {
        for (const ev of diaData.eventos) {
          all.push({ ...ev, fecha: `${yearMonth}-${day}` });
        }
      }
    }
    return all;
  }

  getEventsInRange(from?: string, to?: string): EventoConFecha[] {
    let events = this.getAllEvents();
    if (from) events = events.filter((e) => e.fecha >= from);
    if (to) events = events.filter((e) => e.fecha <= to);
    return events;
  }

  updateGoogleEventId(fecha: string, id: string, googleEventId: string, googleLink?: string): boolean {
    const yearMonth = fecha.slice(0, 7);
    const day = fecha.slice(8, 10);
    const dia = this.data.meses[yearMonth]?.dias[day];
    if (!dia) return false;
    const ev = dia.eventos.find((e) => e.id === id);
    if (!ev) return false;
    ev.google_event_id = googleEventId;
    if (googleLink) ev.google_link = googleLink;
    return true;
  }

  getStatistics(): Estadisticas {
    const meses = Object.values(this.data.meses);
    const totalEventos = meses.reduce((acc, m) => acc + (m.estadisticas_mes?.total_eventos || 0), 0);
    const eventosPorTipo: Record<string, number> = {};
    for (const m of meses) {
      for (const [tipo, count] of Object.entries(m.estadisticas_mes?.por_tipo || {})) {
        eventosPorTipo[tipo] = (eventosPorTipo[tipo] || 0) + count;
      }
    }
    return {
      total_meses_con_datos: Object.keys(this.data.meses).length,
      total_eventos: totalEventos,
      eventos_por_tipo: eventosPorTipo,
      fuentes_csv: this.data.fuentes_csv.length,
      ultima_actualizacion: this.data.last_updated
    };
  }

  registerCsvSource(fuente: CalendarioData["fuentes_csv"][number]): void {
    this.data.fuentes_csv.push(fuente);
  }

  isCsvImported(hash: string): boolean {
    return this.data.fuentes_csv.some((f) => f.hash === hash);
  }
}

export const calendarStore = new CalendarStore();
