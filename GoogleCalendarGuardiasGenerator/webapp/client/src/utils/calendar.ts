import { EventoConFecha } from "../types";

export function pad2(n: number): string {
  return String(n).padStart(2, "0");
}

export function toIso(year: number, month: number, day: number): string {
  return `${year}-${pad2(month)}-${pad2(day)}`;
}

/** Matriz de semanas (Lunes=0..Domingo=6) igual que Python calendar.monthcalendar, 0 = día fuera de mes */
export function getMonthMatrix(year: number, month: number): number[][] {
  const firstDay = new Date(Date.UTC(year, month - 1, 1));
  const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
  // getUTCDay(): 0=Domingo..6=Sábado -> convertir a 0=Lunes..6=Domingo
  const firstWeekday = (firstDay.getUTCDay() + 6) % 7;

  const weeks: number[][] = [];
  let week: number[] = new Array(firstWeekday).fill(0);

  for (let day = 1; day <= daysInMonth; day++) {
    week.push(day);
    if (week.length === 7) {
      weeks.push(week);
      week = [];
    }
  }
  if (week.length > 0) {
    while (week.length < 7) week.push(0);
    weeks.push(week);
  }
  return weeks;
}

/** true si col (0=Lunes..6=Domingo) es sábado o domingo */
export function isWeekendCol(col: number): boolean {
  return col >= 5;
}

export function weekdayOfIso(fecha: string): number {
  // 0=Lunes..6=Domingo
  const d = new Date(`${fecha}T00:00:00Z`);
  return (d.getUTCDay() + 6) % 7;
}

export function isWeekendIso(fecha: string): boolean {
  return weekdayOfIso(fecha) >= 5;
}

export const MESES = [
  "",
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre"
];

export interface TecnicoStat {
  dias: number[];
  total: number;
}

/** Estadísticas por técnico de un mes: TARDE en el título o tipo media_guardia suma 0.5, resto 1 */
export function computeMonthStats(eventos: EventoConFecha[], year: number, month: number): Map<string, TecnicoStat> {
  const stats = new Map<string, TecnicoStat>();
  const prefix = `${year}-${pad2(month)}-`;

  for (const ev of eventos) {
    if (!ev.fecha.startsWith(prefix) || !ev.tecnico) continue;
    const day = Number(ev.fecha.slice(8, 10));
    const esTarde = ev.titulo.toUpperCase().includes("TARDE") || ev.tipo === "media_guardia";

    const current = stats.get(ev.tecnico) || { dias: [], total: 0 };
    current.dias.push(day);
    current.total += esTarde ? 0.5 : 1;
    stats.set(ev.tecnico, current);
  }

  for (const s of stats.values()) s.dias.sort((a, b) => a - b);
  return stats;
}

export function addDaysIso(fecha: string, days: number): string {
  const d = new Date(`${fecha}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

export function formatDdMmYyyy(fecha: string): string {
  const [y, m, d] = fecha.split("-");
  return `${d}/${m}/${y}`;
}

export function parseDdMmYyyy(value: string): string | null {
  const m = value.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const [, dd, mm, yyyy] = m;
  return `${yyyy}-${mm}-${dd}`;
}
