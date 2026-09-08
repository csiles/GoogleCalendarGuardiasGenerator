import { useMemo, useState } from "react";
import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { useTecnicos, useFestivos } from "../hooks/useServerData";
import { useToast } from "../hooks/useToast";
import { TechnicianChip } from "../components/TechnicianChip";
import { CalendarMonth } from "../components/CalendarMonth";
import { StatsPanel } from "../components/StatsPanel";
import { GptOverlay } from "../components/GptOverlay";
import { EventoConFecha, TipoGuardia } from "../types";
import { computeMonthStats, formatDdMmYyyy, parseDdMmYyyy } from "../utils/calendar";
import { exportarCsvUrl } from "../api/resources";

interface Asignacion {
  tecnico: string;
  tipo: TipoGuardia;
  titulo: string;
}

function defaultRango(): { inicio: string; fin: string } {
  const now = new Date();
  const inicioDate = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  const finDate = new Date(inicioDate.getFullYear(), inicioDate.getMonth() + 3, 0);
  return {
    inicio: formatDdMmYyyy(inicioDate.toISOString().slice(0, 10)),
    fin: formatDdMmYyyy(finDate.toISOString().slice(0, 10))
  };
}

export function GeneratorPage() {
  const { data: tecnicos = [] } = useTecnicos();
  const { data: festivos = [] } = useFestivos();
  const { push } = useToast();

  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [tipoGuardia, setTipoGuardia] = useState<TipoGuardia>("guardia");
  const [ultimoTecnico, setUltimoTecnico] = useState<string>("");
  const rangoDefault = useMemo(defaultRango, []);
  const [fechaInicioStr, setFechaInicioStr] = useState(rangoDefault.inicio);
  const [fechaFinStr, setFechaFinStr] = useState(rangoDefault.fin);
  const [asignaciones, setAsignaciones] = useState<Record<string, Asignacion>>({});
  const [showGpt, setShowGpt] = useState(false);
  const [gptRango, setGptRango] = useState<{ inicio: string; fin: string } | null>(null);

  const festivosMap = useMemo(() => new Map(festivos.map((f) => [f.fecha, f.anotacion])), [festivos]);
  const tecnicoColorMap = useMemo(() => new Map(tecnicos.map((t) => [t.nombre, t.color])), [tecnicos]);

  const tecnicoColor = (nombre: string | null) => (nombre && tecnicoColorMap.get(nombre)) || "#3498db";
  const tecnicoEliminado = () => false; // en el Generador todos los técnicos son de la lista activa

  const eventosPorDia = useMemo(() => {
    const map = new Map<string, EventoConFecha[]>();
    for (const [fecha, a] of Object.entries(asignaciones)) {
      map.set(fecha, [
        { id: fecha, fecha, titulo: a.titulo, tecnico: a.tecnico, tipo: a.tipo }
      ]);
    }
    return map;
  }, [asignaciones]);

  const eventosComoLista: EventoConFecha[] = useMemo(
    () => Array.from(eventosPorDia.values()).flat(),
    [eventosPorDia]
  );

  const stats = useMemo(() => computeMonthStats(eventosComoLista, year, month), [eventosComoLista, year, month]);

  function navigate(delta: number) {
    let m = month + delta;
    let y = year;
    while (m > 12) {
      m -= 12;
      y += 1;
    }
    while (m < 1) {
      m += 12;
      y -= 1;
    }
    setMonth(m);
    setYear(y);
  }

  function assign(fecha: string, tecnico: string) {
    const anotacion = festivosMap.get(fecha);
    const prefix = tipoGuardia === "media_guardia" ? "Media Guardia" : "Guardia";
    const titulo = anotacion?.trim() ? `${prefix} ${anotacion.trim()} - ${tecnico}` : `${prefix} - ${tecnico}`;
    setAsignaciones((prev) => ({ ...prev, [fecha]: { tecnico, tipo: tipoGuardia, titulo } }));
  }

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const tecnico = active.data.current?.tecnico as string | undefined;
    const fecha = over.data.current?.fecha as string | undefined;
    if (!tecnico || !fecha) return;

    const esFestivoFinde = festivosMap.has(fecha) && (new Date(`${fecha}T00:00:00Z`).getUTCDay() === 0 || new Date(`${fecha}T00:00:00Z`).getUTCDay() === 6);
    if (esFestivoFinde) {
      if (!window.confirm(`Este festivo cae en fin de semana.\n¿Asignar guardia de fin de semana a ${tecnico}?`)) {
        return;
      }
    }

    assign(fecha, tecnico);
  }

  function removeAsignacion(fecha: string) {
    setAsignaciones((prev) => {
      const next = { ...prev };
      delete next[fecha];
      return next;
    });
  }

  function handleLimpiar() {
    if (window.confirm("¿Borrar todas las asignaciones?")) {
      setAsignaciones({});
    }
  }

  async function handleExportarCsv() {
    const lista = Object.entries(asignaciones).map(([fecha, a]) => ({
      fecha,
      tecnico: a.tecnico,
      tipo: a.tipo,
      titulo: a.titulo
    }));
    if (lista.length === 0) {
      push("error", "No hay asignaciones para exportar");
      return;
    }
    try {
      const res = await fetch(exportarCsvUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ asignaciones: lista })
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "guardias-support.csv";
      a.click();
      URL.revokeObjectURL(url);
      push("success", "✅ CSV exportado correctamente");
    } catch (e: any) {
      push("error", `Error al exportar CSV:\n${e.message}`);
    }
  }

  function handleCrearDesdeGpt() {
    const inicioIso = parseDdMmYyyy(fechaInicioStr);
    const finIso = parseDdMmYyyy(fechaFinStr);
    if (!inicioIso || !finIso) {
      push("error", "Formato de fecha inválido.\nUse DD/MM/AAAA");
      return;
    }
    if (finIso < inicioIso) {
      push("error", "La fecha de fin debe ser posterior a la fecha de inicio");
      return;
    }
    setGptRango({ inicio: inicioIso, fin: finIso });
    setShowGpt(true);
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="control-panel">
        <div className="control-block">
          <label>Último técnico</label>
          <select value={ultimoTecnico} onChange={(e) => setUltimoTecnico(e.target.value)}>
            <option value="">-</option>
            {tecnicos.map((t) => (
              <option key={t.nombre} value={t.nombre}>
                {t.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="control-block">
          <label>Período</label>
          <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
            <span style={{ fontSize: 11 }}>Inicio:</span>
            <input
              style={{ width: 90 }}
              value={fechaInicioStr}
              onChange={(e) => setFechaInicioStr(e.target.value)}
            />
          </div>
          <div style={{ display: "flex", gap: 4, alignItems: "center", marginTop: 4 }}>
            <span style={{ fontSize: 11 }}>Fin:</span>
            <input style={{ width: 90 }} value={fechaFinStr} onChange={(e) => setFechaFinStr(e.target.value)} />
          </div>
        </div>

        <div className="control-block">
          <label>Tipo guardia</label>
          <label style={{ fontWeight: "normal", display: "block" }}>
            <input
              type="radio"
              checked={tipoGuardia === "guardia"}
              onChange={() => setTipoGuardia("guardia")}
            />{" "}
            Completa
          </label>
          <label style={{ fontWeight: "normal", display: "block" }}>
            <input
              type="radio"
              checked={tipoGuardia === "media_guardia"}
              onChange={() => setTipoGuardia("media_guardia")}
            />{" "}
            Media
          </label>
        </div>

        <div className="control-block" style={{ flex: 1 }}>
          <label>Técnicos (arrastra al calendario)</label>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {tecnicos.map((t) => (
              <TechnicianChip key={t.nombre} nombre={t.nombre} color={t.color} />
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: "#34495e", color: "white", padding: 8, borderRadius: 4 }}>
            <button className="btn btn-neutral" onClick={() => navigate(-1)}>
              ◀
            </button>
            <strong>
              {month}/{year}
            </strong>
            <button className="btn btn-neutral" onClick={() => navigate(1)}>
              ▶
            </button>
          </div>
          <CalendarMonth
            year={year}
            month={month}
            festivosMap={festivosMap}
            eventosPorDia={eventosPorDia}
            tecnicoColor={tecnicoColor}
            tecnicoEliminado={tecnicoEliminado}
            onRemoveEvento={removeAsignacion}
          />
        </div>

        <div style={{ width: 260, display: "flex", flexDirection: "column", gap: 10 }}>
          <StatsPanel stats={stats} tecnicoColor={tecnicoColor} tecnicoEliminado={tecnicoEliminado} title="Guardias del mes" />
          <button className="btn btn-gpt" onClick={handleCrearDesdeGpt}>
            Crear desde GPT
          </button>
          <button className="btn btn-danger" onClick={handleLimpiar}>
            Limpiar
          </button>
          <button className="btn btn-success" onClick={handleExportarCsv}>
            Exportar CSV
          </button>
        </div>
      </div>

      {showGpt && gptRango && (
        <GptOverlay
          fechaInicio={gptRango.inicio}
          fechaFin={gptRango.fin}
          onClose={() => setShowGpt(false)}
          onSaved={() => push("info", "Revisa la pestaña Ver Calendarios para ver las guardias guardadas.")}
        />
      )}
    </DndContext>
  );
}
