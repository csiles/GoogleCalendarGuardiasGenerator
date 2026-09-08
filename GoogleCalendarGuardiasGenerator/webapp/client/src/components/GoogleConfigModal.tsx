import { useEffect, useState } from "react";
import { getGoogleLoginUrl, getGoogleCalendars, setGoogleConfig, getGoogleStatus } from "../api/resources";
import { GoogleCalendarListItem } from "../types";
import { useToast } from "../hooks/useToast";

interface Props {
  onClose: () => void;
  onConfigured: () => void;
}

export function GoogleConfigModal({ onClose, onConfigured }: Props) {
  const { push } = useToast();
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [calendars, setCalendars] = useState<GoogleCalendarListItem[]>([]);
  const [seleccionado, setSeleccionado] = useState<GoogleCalendarListItem | null>(null);
  const [needsLogin, setNeedsLogin] = useState(false);

  async function cargar() {
    setCargando(true);
    setError(null);
    try {
      const status = await getGoogleStatus();
      if (!status.authenticated) {
        setNeedsLogin(true);
        setCargando(false);
        return;
      }
      setNeedsLogin(false);
      const cals = await getGoogleCalendars();
      setCalendars(cals);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleLogin() {
    try {
      const { url } = await getGoogleLoginUrl();
      window.open(url, "_blank", "noopener,noreferrer");
      push("info", "Completa el login en la pestaña de Google y vuelve aquí para reintentar.");
    } catch (e: any) {
      push("error", e.message);
    }
  }

  async function handleSeleccionar() {
    if (!seleccionado) return;
    try {
      await setGoogleConfig({
        calendar_id: seleccionado.id,
        calendar_name: seleccionado.name,
        access_role: seleccionado.access_role
      });
      push("success", `Calendario configurado correctamente:\n${seleccionado.name}`);
      onConfigured();
      onClose();
    } catch (e: any) {
      push("error", e.message);
    }
  }

  return (
    <div className="overlay-backdrop">
      <div className="overlay-card" style={{ width: 600 }}>
        <div className="overlay-header">
          <strong>🗓️ Seleccionar Calendario de Google</strong>
          <button onClick={onClose}>✕</button>
        </div>
        <div className="overlay-body">
          <p style={{ fontSize: 12, color: "#555" }}>
            Selecciona el calendario de Google donde quieres sincronizar las guardias. Puedes elegir tu
            calendario personal o cualquier calendario compartido donde tengas permisos de escritura.
          </p>

          {cargando && <p>⏳ Cargando calendarios disponibles...</p>}

          {!cargando && needsLogin && (
            <div>
              <p>Necesitas iniciar sesión con Google antes de poder listar tus calendarios.</p>
              <button className="btn btn-gpt" onClick={handleLogin}>
                Iniciar sesión con Google
              </button>
              <button className="btn btn-neutral" style={{ marginLeft: 8 }} onClick={cargar}>
                Ya inicié sesión, reintentar
              </button>
            </div>
          )}

          {!cargando && error && (
            <div>
              <p style={{ color: "#c0392b" }}>❌ Error al cargar calendarios:\n{error}</p>
              <button className="btn btn-neutral" onClick={cargar}>
                🔄 Reintentar
              </button>
            </div>
          )}

          {!cargando && !needsLogin && !error && (
            <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 320, overflow: "auto" }}>
              {calendars.map((cal) => {
                const icon = cal.is_primary ? "👤" : "👥";
                const roleIcon = cal.access_role === "owner" ? "🔒" : "✏️";
                const isSelected = seleccionado?.id === cal.id;
                return (
                  <div
                    key={cal.id}
                    onClick={() => setSeleccionado(cal)}
                    style={{
                      padding: 8,
                      border: isSelected ? "2px solid #3498db" : "1px solid #ddd",
                      borderRadius: 4,
                      cursor: "pointer",
                      background: cal.is_primary ? "#e3f2fd" : cal.access_role === "owner" ? "#f3e5f5" : "#fff3e0"
                    }}
                  >
                    {icon} {cal.name} {roleIcon}
                    {cal.is_primary ? " [PRINCIPAL]" : ""}
                  </div>
                );
              })}
              {seleccionado && (
                <div className="card" style={{ marginTop: 8 }}>
                  <div>📛 Nombre: {seleccionado.name}</div>
                  <div>🔑 Permisos: {seleccionado.access_role.toUpperCase()}</div>
                  <div>🌍 Zona horaria: {seleccionado.timezone}</div>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="overlay-footer">
          <button className="btn btn-success" disabled={!seleccionado} onClick={handleSeleccionar}>
            ✅ Seleccionar
          </button>
          <button className="btn btn-neutral" onClick={onClose}>
            ❌ Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
