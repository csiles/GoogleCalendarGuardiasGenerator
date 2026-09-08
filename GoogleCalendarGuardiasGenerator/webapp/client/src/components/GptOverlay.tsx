import { useEffect, useState } from "react";
import { getGptReglasDefault, generarConGpt, guardarBulk } from "../api/resources";
import { AsignacionGpt } from "../types";
import { useToast } from "../hooks/useToast";

interface Props {
  fechaInicio: string;
  fechaFin: string;
  onClose: () => void;
  onSaved: () => void;
}

type Vista = "instrucciones" | "revision";

export function GptOverlay({ fechaInicio, fechaFin, onClose, onSaved }: Props) {
  const { push } = useToast();
  const [vista, setVista] = useState<Vista>("instrucciones");
  const [instrucciones, setInstrucciones] = useState("");
  const [cargando, setCargando] = useState(false);
  const [asignaciones, setAsignaciones] = useState<AsignacionGpt[]>([]);
  const [guardando, setGuardando] = useState(false);

  useEffect(() => {
    getGptReglasDefault()
      .then((r) => setInstrucciones(r.reglas))
      .catch(() => push("error", "No se pudieron cargar las reglas por defecto"));
  }, [push]);

  async function handleEnviar() {
    if (!instrucciones.trim()) {
      push("error", "El texto de instrucciones está vacío.");
      return;
    }
    setCargando(true);
    try {
      const res = await generarConGpt({ instrucciones, fecha_inicio: fechaInicio, fecha_fin: fechaFin });
      setAsignaciones(res.asignaciones);
      setVista("revision");
    } catch (e: any) {
      push("error", `No se pudo generar la propuesta:\n${e.message}`);
    } finally {
      setCargando(false);
    }
  }

  async function handleGuardar() {
    setGuardando(true);
    try {
      const res = await guardarBulk(asignaciones, "gpt");
      push(
        "success",
        `Guardado en el calendario local\n\nGuardias guardadas: ${res.guardados}` +
          (res.ignorados ? `\nEntradas inválidas ignoradas: ${res.ignorados}` : "") +
          "\n\nVe al Visualizador y pulsa 'Sincro: Local → Google' para subirlas a Google Calendar."
      );
      onSaved();
      onClose();
    } catch (e: any) {
      push("error", `No se pudo guardar: ${e.message}`);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <div className="overlay-backdrop">
      <div className="overlay-card">
        <div className="overlay-header">
          <strong>{vista === "instrucciones" ? "Crear guardias con GPT" : "Propuesta de guardias generada por GPT"}</strong>
          <button onClick={onClose}>✕</button>
        </div>

        {vista === "instrucciones" ? (
          <>
            <div className="overlay-body">
              <p style={{ fontSize: 12, color: "#555", margin: 0 }}>
                Rango a asignar: {fechaInicio} - {fechaFin}. Completa "REGLAS PARTICULARES" si aplica.
              </p>
              <textarea
                className="gpt-textarea"
                value={instrucciones}
                onChange={(e) => setInstrucciones(e.target.value)}
              />
              {cargando && <p style={{ fontSize: 12, fontStyle: "italic" }}>Consultando a GPT, esto puede tardar unos segundos...</p>}
            </div>
            <div className="overlay-footer">
              <button className="btn btn-gpt" disabled={cargando} onClick={handleEnviar}>
                {cargando ? "Generando..." : "Enviar a GPT"}
              </button>
              <button className="btn btn-neutral" onClick={onClose}>
                Cancelar
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="overlay-body">
              <p style={{ fontSize: 12, color: "#555", margin: 0 }}>
                Revisa la propuesta antes de guardarla en el calendario local.
              </p>
              {asignaciones.length === 0 ? (
                <p style={{ color: "#c0392b", fontStyle: "italic" }}>GPT no ha devuelto ninguna asignación.</p>
              ) : (
                <table className="stats-table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Técnico</th>
                      <th>Tipo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...asignaciones]
                      .sort((a, b) => a.fecha.localeCompare(b.fecha))
                      .map((a, i) => (
                        <tr key={i}>
                          <td>{a.fecha}</td>
                          <td>{a.tecnico}</td>
                          <td>{a.tipo || "guardia"}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="overlay-footer">
              {asignaciones.length > 0 ? (
                <>
                  <button className="btn btn-success" disabled={guardando} onClick={handleGuardar}>
                    {guardando ? "Guardando..." : "Guardar en calendario local"}
                  </button>
                  <button className="btn btn-danger" onClick={onClose}>
                    Descartar
                  </button>
                </>
              ) : (
                <button className="btn btn-neutral" onClick={onClose}>
                  Cerrar
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
