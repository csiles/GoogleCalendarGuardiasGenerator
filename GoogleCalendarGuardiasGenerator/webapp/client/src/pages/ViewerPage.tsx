import { useMemo, useState } from "react";
import { DndContext, DragEndEvent } from "@dnd-kit/core";
import { useQueryClient } from "@tanstack/react-query";
import {
  useTecnicos,
  useFestivos,
  useGuardias,
  useGuardiasStats,
  useGoogleStatus
} from "../hooks/useServerData";
import { useToast } from "../hooks/useToast";
import { TechnicianChip } from "../components/TechnicianChip";
import { CalendarMonth } from "../components/CalendarMonth";
import { StatsPanel } from "../components/StatsPanel";
import { GoogleConfigModal } from "../components/GoogleConfigModal";
import {
  asignarGuardia,
  eliminarGuardiaDia,
  eliminarGuardiasMes,
  importarCsv,
  reloadGuardias,
  syncPush,
  syncPull
} from "../api/resources";
import { computeMonthStats, MESES } from "../utils/calendar";

const NUM_MESES = 7;

function addMonths(year: number, month: number, delta: number): { year: number; month: number } {
  const total = year * 12 + (month - 1) + delta;
  return { year: Math.floor(total / 12), month: ((total % 12) + 12) % 12 + 1 };
}

export function ViewerPage() {
  const { data: tecnicos = [] } = useTecnicos();
  const { data: festivos = [] } = useFestivos();
  const { data: eventos = [], refetch: refetchGuardias } = useGuardias();
  const { data: stats, refetch: refetchStats } = useGuardiasStats();
  const { data: googleStatus, refetch: refetchGoogleStatus } = useGoogleStatus();
  const { push } = useToast();
  const queryClient = useQueryClient();

  const [offsetMonths, setOffsetMonths] = useState(0);
  const [showGoogleModal, setShowGoogleModal] = useState(false);

  const today = new Date();
  const baseMonth = addMonths(today.getFullYear(), today.getMonth() + 1, offsetMonths - 3);
  const meses = useMemo(
    () => Array.from({ length: NUM_MESES }, (_, i) => addMonths(baseMonth.year, baseMonth.month, i)),
    [baseMonth.year, baseMonth.month]
  );

  const festivosMap = useMemo(() => new Map(festivos.map((f) => [f.fecha, f.anotacion])), [festivos]);
  const tecnicoColorMap = useMemo(() => new Map(tecnicos.map((t) => [t.nombre, t.color])), [tecnicos]);
  const tecnicosActivos = useMemo(() => new Set(tecnicos.map((t) => t.nombre)), [tecnicos]);

  const tecnicoColor = (nombre: string | null) => (nombre && tecnicoColorMap.get(nombre)) || "#3498db";
  const tecnicoEliminado = (nombre: string | null) => !!nombre && !tecnicosActivos.has(nombre);

  const eventosPorDia = useMemo(() => {
    const map = new Map<string, typeof eventos>();
    for (const ev of eventos) {
      const list = map.get(ev.fecha) || [];
      list.push(ev);
      map.set(ev.fecha, list);
    }
    return map;
  }, [eventos]);

  function invalidateAll() {
    queryClient.invalidateQueries({ queryKey: ["guardias"] });
    queryClient.invalidateQueries({ queryKey: ["guardias-stats"] });
  }

  async function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;
    const tecnico = active.data.current?.tecnico as string | undefined;
    const fecha = over.data.current?.fecha as string | undefined;
    if (!tecnico || !fecha) return;

    try {
      await asignarGuardia({ fecha, tecnico, tipo: "guardia" });
      invalidateAll();
    } catch (e: any) {
      push("error", `No se pudo asignar: ${e.message}`);
    }
  }

  async function handleRemoveEvento(fecha: string) {
    try {
      await eliminarGuardiaDia(fecha);
      invalidateAll();
    } catch (e: any) {
      push("error", `No se pudo eliminar: ${e.message}`);
    }
  }

  async function handleBorrarMes(year: number, month: number) {
    const yyyymm = `${year}-${String(month).padStart(2, "0")}`;
    if (
      !window.confirm(
        `¿Borrar todas las guardias de ${MESES[month]} ${year}?\n\nEsto solo afecta al calendario local.`
      )
    ) {
      return;
    }
    try {
      await eliminarGuardiasMes(yyyymm);
      invalidateAll();
    } catch (e: any) {
      push("error", `No se pudo borrar el mes: ${e.message}`);
    }
  }

  async function handleImportarCsv(file: File) {
    try {
      const res = await importarCsv(file);
      push(
        "success",
        `✅ Importación completada\n\nTotal registros: ${res.total}\nImportados: ${res.importados}\nDuplicados: ${res.duplicados}\nErrores: ${res.errores}`
      );
      invalidateAll();
    } catch (e: any) {
      push("error", `Error al importar CSV:\n${e.message}`);
    }
  }

  async function handleActualizar() {
    try {
      await reloadGuardias();
      setOffsetMonths(0);
      invalidateAll();
    } catch (e: any) {
      push("error", `Error al actualizar: ${e.message}`);
    }
  }

  async function handleSyncPush() {
    if (
      !window.confirm(
        "¿Deseas sincronizar todas las guardias locales hacia Google Calendar?\n\nEsto creará/actualizará los eventos en el calendario configurado."
      )
    ) {
      return;
    }
    try {
      const res = await syncPush();
      push(
        "success",
        `✅ Sincronización completada\n\nTotal eventos: ${res.total}\nCreados: ${res.created}\nActualizados: ${res.updated}\nErrores: ${res.errors}` +
          (res.calendar_url ? `\n\n🔗 ${res.calendar_url}` : "")
      );
      invalidateAll();
    } catch (e: any) {
      push("error", `Error de sincronización:\n${e.message}`);
    }
  }

  async function handleSyncPull() {
    if (
      !window.confirm(
        "¿Deseas descargar los eventos de Google Calendar hacia el calendario local?\n\nRango: 12 meses atrás, 6 meses adelante.\nSe importarán tal cual vengan de Google."
      )
    ) {
      return;
    }
    try {
      const res = await syncPull();
      push(
        "success",
        `✅ Descarga completada\n\nTotal descargados: ${res.total_descargados}\nImportados (técnico activo): ${res.importados_tecnico_activo}\nImportados (técnico ya no existe 💀): ${res.importados_tecnico_eliminado}\nImportados (genéricos): ${res.importados_genericos}`
      );
      invalidateAll();
    } catch (e: any) {
      push("error", `Error de sincronización:\n${e.message}`);
    }
  }

  const googleLabel = googleStatus?.configured
    ? `Calendario seleccionado: ${googleStatus.calendar?.calendar_name}`
    : "Calendario seleccionado: No configurado";

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="toolbar">
        <div className="toolbar-left">
          <span>{googleLabel}</span>
          <button className="btn btn-gpt" onClick={() => setShowGoogleModal(true)}>
            Login/config
          </button>
        </div>
        <div className="toolbar-center">
          <label className="btn btn-primary" style={{ display: "inline-block" }}>
            Importar CSV
            <input
              type="file"
              accept=".csv"
              style={{ display: "none" }}
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleImportarCsv(file);
                e.target.value = "";
              }}
            />
          </label>
          <button className="btn btn-success" onClick={handleActualizar}>
            Actualizar
          </button>
          <button className="btn btn-push" disabled={!googleStatus?.configured} onClick={handleSyncPush}>
            Sincro: Local → Google
          </button>
          <button className="btn btn-pull" disabled={!googleStatus?.configured} onClick={handleSyncPull}>
            Sincro: Google → Local
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8, alignItems: "center", padding: "8px 16px", flexWrap: "wrap" }}>
        <span style={{ fontWeight: "bold", fontSize: 12 }}>Técnicos:</span>
        {tecnicos.map((t) => (
          <TechnicianChip key={t.nombre} nombre={t.nombre} color={t.color} />
        ))}
        <div style={{ flex: 1 }} />
        <button className="btn btn-neutral" onClick={() => setOffsetMonths((o) => o - 12)}>
          ◀◀ -1 Año
        </button>
        <button className="btn btn-neutral" onClick={() => setOffsetMonths((o) => o - 1)}>
          ◀ -1 Mes
        </button>
        <button className="btn btn-danger" onClick={() => setOffsetMonths(0)}>
          HOY
        </button>
        <button className="btn btn-neutral" onClick={() => setOffsetMonths((o) => o + 1)}>
          ► +1 Mes
        </button>
        <button className="btn btn-neutral" onClick={() => setOffsetMonths((o) => o + 12)}>
          ►► +1 Año
        </button>
      </div>

      <div className="months-grid" style={{ padding: "0 16px" }}>
        {meses.map(({ year, month }) => {
          const monthStats = computeMonthStats(eventos, year, month);
          return (
            <div key={`${year}-${month}`} className="card month-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3>
                  {MESES[month]} {year}
                </h3>
                <button
                  className="btn btn-danger"
                  style={{ fontSize: 10, padding: "2px 6px" }}
                  onClick={() => handleBorrarMes(year, month)}
                >
                  🗑
                </button>
              </div>
              <CalendarMonth
                year={year}
                month={month}
                festivosMap={festivosMap}
                eventosPorDia={eventosPorDia}
                tecnicoColor={tecnicoColor}
                tecnicoEliminado={tecnicoEliminado}
                onRemoveEvento={handleRemoveEvento}
              />
              <div style={{ marginTop: 8 }}>
                <StatsPanel stats={monthStats} tecnicoColor={tecnicoColor} tecnicoEliminado={tecnicoEliminado} />
              </div>
            </div>
          );
        })}
      </div>

      <div className="status-bar">
        Total eventos: {stats?.total_eventos ?? 0} | Meses: {stats?.total_meses_con_datos ?? 0} | Última
        actualización: {stats?.ultima_actualizacion?.slice(0, 19) ?? "-"} | Google:{" "}
        {googleStatus?.configured ? googleStatus.calendar?.calendar_name : "No configurado"}
      </div>

      {showGoogleModal && (
        <GoogleConfigModal
          onClose={() => setShowGoogleModal(false)}
          onConfigured={() => {
            refetchGoogleStatus();
            refetchGuardias();
            refetchStats();
          }}
        />
      )}
    </DndContext>
  );
}
