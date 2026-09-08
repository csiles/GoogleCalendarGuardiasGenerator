import { DayCell } from "./DayCell";
import { EventoConFecha } from "../types";
import { getMonthMatrix, isWeekendCol, toIso, MESES } from "../utils/calendar";

interface Props {
  year: number;
  month: number;
  festivosMap: Map<string, string>;
  eventosPorDia: Map<string, EventoConFecha[]>;
  tecnicoColor: (nombre: string | null) => string;
  tecnicoEliminado: (nombre: string | null) => boolean;
  onRemoveEvento?: (fecha: string) => void;
  maxVisible?: number;
  showTitle?: boolean;
}

const DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

export function CalendarMonth({
  year,
  month,
  festivosMap,
  eventosPorDia,
  tecnicoColor,
  tecnicoEliminado,
  onRemoveEvento,
  maxVisible = 2,
  showTitle = false
}: Props) {
  const weeks = getMonthMatrix(year, month);

  return (
    <div>
      {showTitle && (
        <h3>
          {MESES[month]} {year}
        </h3>
      )}
      <div className="calendar-grid">
        {DIAS_SEMANA.map((d, i) => (
          <div key={d} className={`calendar-weekday-header${isWeekendCol(i) ? " weekend" : ""}`}>
            {d}
          </div>
        ))}
        {weeks.map((week, wi) =>
          week.map((day, di) => {
            if (day === 0) return <div key={`${wi}-${di}`} className="day-cell" style={{ background: "transparent", border: "none" }} />;

            const fecha = toIso(year, month, day);
            const weekend = isWeekendCol(di);
            const anotacion = festivosMap.get(fecha);
            const isHoliday = anotacion !== undefined;
            const isAssignable = weekend || (isHoliday && !weekend);
            const eventos = eventosPorDia.get(fecha) || [];

            return (
              <DayCell
                key={fecha}
                fecha={fecha}
                day={day}
                isWeekend={weekend}
                isHoliday={isHoliday}
                holidayLabel={anotacion}
                isAssignable={isAssignable}
                eventos={eventos}
                tecnicoColor={tecnicoColor}
                tecnicoEliminado={tecnicoEliminado}
                onRemoveEvento={onRemoveEvento}
                maxVisible={maxVisible}
              />
            );
          })
        )}
      </div>
    </div>
  );
}
