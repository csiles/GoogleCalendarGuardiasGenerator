import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { parse } from "csv-parse/sync";
import { stringify } from "csv-stringify/sync";
import { config } from "../config";
import { calendarStore, generateEventId } from "../services/store";
import { Evento, TipoGuardia } from "../types";

const CSV_HEADER = [
  "Subject",
  "Start Date",
  "Start Time",
  "End Date",
  "End Time",
  "All Day Event",
  "Description",
  "Location",
  "Private"
];

function addDays(fecha: string, days: number): string {
  const d = new Date(`${fecha}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function weekday(fecha: string): number {
  // 0=Domingo ... 6=Sábado (getUTCDay)
  return new Date(`${fecha}T00:00:00Z`).getUTCDay();
}

export interface AsignacionExport {
  fecha: string;
  tecnico: string;
  tipo?: TipoGuardia;
  titulo?: string;
}

/** Exporta asignaciones al formato CSV all-day de Google Calendar, agrupando sáb+dom del mismo técnico/tipo */
export function exportCsv(asignaciones: AsignacionExport[]): string {
  const ordenadas = [...asignaciones].sort((a, b) => a.fecha.localeCompare(b.fecha));
  const rows: string[][] = [CSV_HEADER];

  let i = 0;
  while (i < ordenadas.length) {
    const actual = ordenadas[i];
    const prefix = actual.tipo === "media_guardia" ? "Media Guardia" : "Guardia";
    const titulo = actual.titulo || `${prefix} - ${actual.tecnico}`;

    let fechaFinReal = actual.fecha;
    let skipNext = false;

    if (weekday(actual.fecha) === 6 && i + 1 < ordenadas.length) {
      const siguiente = ordenadas[i + 1];
      const domingoEsperado = addDays(actual.fecha, 1);
      if (
        siguiente.fecha === domingoEsperado &&
        siguiente.tecnico === actual.tecnico &&
        (siguiente.tipo || "guardia") === (actual.tipo || "guardia")
      ) {
        fechaFinReal = siguiente.fecha;
        skipNext = true;
      }
    }

    const endDateExclusivo = addDays(fechaFinReal, 1);

    rows.push([
      titulo,
      actual.fecha,
      "00:00:00",
      endDateExclusivo,
      "00:00:00",
      "True",
      "",
      "",
      "False"
    ]);

    i += skipNext ? 2 : 1;
  }

  return stringify(rows);
}

export function saveCsvExport(csvContent: string): string {
  fs.mkdirSync(config.csvDir, { recursive: true });
  fs.writeFileSync(config.csvExportFile, csvContent, "utf-8");
  return config.csvExportFile;
}

export interface ImportStats {
  total: number;
  importados: number;
  duplicados: number;
  errores: number;
  errores_detalle: { fila?: number; error: string }[];
}

/** Importa un CSV (formato Google Calendar) al store, con dedupe por hash de fichero y por día ocupado */
export function importCsv(buffer: Buffer, originalFilename: string): ImportStats {
  const stats: ImportStats = { total: 0, importados: 0, duplicados: 0, errores: 0, errores_detalle: [] };

  const fileHash = crypto.createHash("md5").update(buffer).digest("hex");
  if (calendarStore.isCsvImported(fileHash)) {
    return stats;
  }

  let rows: Record<string, string>[];
  try {
    rows = parse(buffer, { columns: true, skip_empty_lines: true, trim: true }) as Record<
      string,
      string
    >[];
  } catch (e: any) {
    stats.errores += 1;
    stats.errores_detalle.push({ error: `CSV inválido: ${e.message}` });
    return stats;
  }

  stats.total = rows.length;

  rows.forEach((row, idx) => {
    try {
      const fechaInicioStr = row["Start Date"];
      const fechaFinStr = row["End Date"];
      if (!fechaInicioStr || !fechaFinStr) throw new Error("Faltan Start Date/End Date");

      const subject = String(row["Subject"] || "");
      const tecnico = subject.includes(" - ") ? subject.split(" - ").pop()!.trim() : subject.trim();

      const isAllDay = (row["All Day Event"] || "True") === "True";
      const fechaLimite = isAllDay ? addDays(fechaFinStr, -1) : fechaFinStr;

      let fechaActual = fechaInicioStr;
      while (fechaActual <= fechaLimite) {
        const yearMonth = fechaActual.slice(0, 7);
        const day = fechaActual.slice(8, 10);

        let existingTecnico: string | null = null;
        const raw = calendarStore.getRaw();
        const eventosDia = raw.meses[yearMonth]?.dias[day]?.eventos;
        if (eventosDia && eventosDia.length > 0) {
          existingTecnico = eventosDia[0].tecnico;
        }

        if (!existingTecnico) {
          const evento: Evento = {
            id: generateEventId(fechaActual, subject),
            titulo: subject,
            tecnico,
            tipo: "guardia",
            descripcion: String(row["Description"] || ""),
            all_day: isAllDay,
            origen: "csv_import",
            fecha_importacion: new Date().toISOString(),
            archivo_origen: path.basename(originalFilename)
          };

          if (calendarStore.addEvent(fechaActual, evento)) {
            stats.importados += 1;
          } else {
            stats.duplicados += 1;
          }
        } else {
          stats.duplicados += 1;
        }

        fechaActual = addDays(fechaActual, 1);
      }
    } catch (e: any) {
      stats.errores += 1;
      stats.errores_detalle.push({ fila: idx + 2, error: e.message });
    }
  });

  calendarStore.registerCsvSource({
    nombre: path.basename(originalFilename),
    ruta: originalFilename,
    fecha_carga: new Date().toISOString(),
    registros_importados: stats.importados,
    hash: fileHash
  });

  calendarStore.save();
  return stats;
}
