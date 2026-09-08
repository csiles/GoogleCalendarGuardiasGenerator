import { TecnicoStat } from "../utils/calendar";

interface Props {
  stats: Map<string, TecnicoStat>;
  tecnicoColor: (nombre: string | null) => string;
  tecnicoEliminado: (nombre: string | null) => boolean;
  title?: string;
}

export function StatsPanel({ stats, tecnicoColor, tecnicoEliminado, title = "Técnicos" }: Props) {
  const entries = Array.from(stats.entries()).sort((a, b) => a[0].localeCompare(b[0]));

  return (
    <div className="card" style={{ minWidth: 180 }}>
      <strong style={{ fontSize: 12 }}>{title}</strong>
      {entries.length === 0 ? (
        <p style={{ fontSize: 12, color: "#999", fontStyle: "italic" }}>Sin guardias</p>
      ) : (
        <table className="stats-table">
          <thead>
            <tr>
              <th>Técnico</th>
              <th>Días</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([tecnico, info]) => {
              const eliminado = tecnicoEliminado(tecnico);
              const totalStr = info.total % 1 !== 0 ? String(info.total) : String(Math.trunc(info.total));
              return (
                <tr key={tecnico}>
                  <td
                    className="tecnico-cell"
                    style={{ background: eliminado ? "#000000" : tecnicoColor(tecnico) }}
                  >
                    {eliminado ? "💀 " : ""}
                    {tecnico}
                  </td>
                  <td>{info.dias.join(",")}</td>
                  <td>{totalStr}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
}
