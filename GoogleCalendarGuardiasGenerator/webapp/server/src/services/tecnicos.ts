import fs from "node:fs";
import { config } from "../config";
import { Tecnico } from "../types";

/** Parsea tecnicos.txt: "Nombre,#color" por línea, el orden importa (rotación) */
export function loadTecnicos(filePath: string = config.tecnicosFile): Tecnico[] {
  if (!fs.existsSync(filePath)) return [];
  const raw = fs.readFileSync(filePath, "utf-8");
  const tecnicos: Tecnico[] = [];

  for (const rawLine of raw.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    const parts = line.split(",");
    const nombre = parts[0].trim();
    if (!nombre) continue;
    const color = parts.length > 1 && parts[1].trim() ? parts[1].trim() : "#3498db";
    tecnicos.push({ nombre, color });
  }

  return tecnicos;
}

export function getTecnicoNombres(filePath: string = config.tecnicosFile): string[] {
  return loadTecnicos(filePath).map((t) => t.nombre);
}
