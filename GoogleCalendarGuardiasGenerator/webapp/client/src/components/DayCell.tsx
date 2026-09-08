import { useDroppable } from "@dnd-kit/core";
import { EventoConFecha } from "../types";

interface Props {
  fecha: string;
  day: number;
  isWeekend: boolean;
  isHoliday: boolean;
  holidayLabel?: string;
  isAssignable: boolean;
  eventos: EventoConFecha[];
  tecnicoColor: (nombre: string | null) => string;
  tecnicoEliminado: (nombre: string | null) => boolean;
  onRemoveEvento?: (fecha: string) => void;
  maxVisible?: number;
}

export function DayCell({
  fecha,
  day,
  isWeekend,
  isHoliday,
  holidayLabel,
  isAssignable,
  eventos,
  tecnicoColor,
  tecnicoEliminado,
  onRemoveEvento,
  maxVisible = 2
}: Props) {
  const { setNodeRef, isOver } = useDroppable({
    id: `day:${fecha}`,
    data: { fecha },
    disabled: !isAssignable
  });

  const visibles = eventos.slice(0, maxVisible);
  const restantes = eventos.length - visibles.length;

  const classes = ["day-cell"];
  if (isWeekend) classes.push("weekend");
  if (isHoliday) classes.push("holiday");
  if (isOver && isAssignable) classes.push("drop-target");

  return (
    <div ref={setNodeRef} className={classes.join(" ")}>
      <div className="day-number">{day}</div>
      {isHoliday && <div className="holiday-label">{holidayLabel || "Festivo"}</div>}
      {visibles.map((ev) => {
        const eliminado = tecnicoEliminado(ev.tecnico);
        return (
          <span
            key={ev.id}
            className={`event-badge${eliminado ? " removed-tecnico" : ""}`}
            style={eliminado ? undefined : { background: tecnicoColor(ev.tecnico) }}
            onClick={() => onRemoveEvento?.(fecha)}
            title="Click para eliminar (solo local)"
          >
            {eliminado ? "💀 " : ""}
            {ev.tecnico || ev.titulo}
          </span>
        );
      })}
      {restantes > 0 && <div style={{ fontSize: 10, color: "#888" }}>+{restantes} más</div>}
    </div>
  );
}
