import fs from "node:fs";
import { config } from "../config";
import { Festivo } from "../types";

function toIso(fechaDdMmYyyy: string): string | null {
  const m = fechaDdMmYyyy.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const [, dd, mm, yyyy] = m;
  const day = Number(dd);
  const month = Number(mm);
  if (month < 1 || month > 12 || day < 1 || day > 31) return null;
  return `${yyyy}-${mm}-${dd}`;
}

/** Parsea festivos.txt: "DD/MM/YYYY, ANOTACION_OPCIONAL" por línea (tolerante a separadores raros) */
export function loadFestivos(filePath: string = config.festivosFile): Festivo[] {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, "utf-8");
  const festivos: Festivo[] = [];

  for (const rawLine of raw.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const parts = line.split(",");
    const fechaStr = parts[0].trim().replace(/\.$/, ""); // tolera "01/05/2026."
    const anotacion = parts.length > 1 ? parts[1].trim() : "";

    const iso = toIso(fechaStr);
    if (!iso) {
      console.warn(`Fecha de festivo inválida ignorada: "${fechaStr}"`);
      continue;
    }
    festivos.push({ fecha: iso, anotacion });
  }

  return festivos;
}

export function getFestivosMap(filePath: string = config.festivosFile): Map<string, string> {
  const map = new Map<string, string>();
  for (const f of loadFestivos(filePath)) map.set(f.fecha, f.anotacion);
  return map;
}
