import { useEffect, useState } from "react";
import { api } from "../api";
import type { EstadoSprint, Sprint } from "../tipos";
import { Badge } from "../ui";

const TONO_ESTADO: Record<EstadoSprint, string> = {
  PLANIFICADO: "azul",
  ACTIVO: "verde",
  CERRADO: "gris",
};

export default function Sprints() {
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [modal, setModal] = useState(false);
  const [objetivo, setObjetivo] = useState("");
  const [inicio, setInicio] = useState("");
  const [fin, setFin] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  async function cargar() {
    try {
      setSprints(await api.get<Sprint[]>("/sprints"));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    cargar();
  }, []);

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await api.post("/sprints", { objetivo, fecha_inicio: inicio, fecha_fin: fin });
      setObjetivo("");
      setInicio("");
      setFin("");
      setModal(false);
      cargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function cambiarEstado(s: Sprint, estado: EstadoSprint) {
    setError("");
    try {
      await api.put(`/sprints/${s.id_sprint}`, { estado });
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function eliminar(id: number) {
    if (!confirm("¿Eliminar el sprint?")) return;
    try {
      await api.del(`/sprints/${id}`);
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function dias(s: Sprint) {
    const d = (new Date(s.fecha_fin).getTime() - new Date(s.fecha_inicio).getTime()) / 86400000;
    return Math.max(0, Math.round(d));
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Gestión de Sprints</h1>
          <p className="sub">Planificación y configuración de los sprints del proyecto</p>
        </div>
        <button className="boton-primario" onClick={() => setModal(true)}>
          + Nuevo sprint
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="lista-sprints">
        {sprints.map((s) => (
          <div key={s.id_sprint} className="card-sprint">
            <div className="card-sprint-cabecera">
              <div>
                <h3>
                  Sprint #{s.id_sprint} <Badge valor={s.estado} tono={TONO_ESTADO[s.estado]} />
                </h3>
                <small>
                  {s.fecha_inicio} → {s.fecha_fin} · {dias(s)} días
                </small>
              </div>
              <div className="acciones">
                <select
                  value={s.estado}
                  onChange={(e) => cambiarEstado(s, e.target.value as EstadoSprint)}
                >
                  <option value="PLANIFICADO">PLANIFICADO</option>
                  <option value="ACTIVO">ACTIVO</option>
                  <option value="CERRADO">CERRADO</option>
                </select>
                <button className="boton-peligro" onClick={() => eliminar(s.id_sprint)}>
                  Eliminar
                </button>
              </div>
            </div>
            <p className="objetivo-sprint">{s.objetivo}</p>
          </div>
        ))}
        {sprints.length === 0 && <p className="vacio">No hay sprints todavía.</p>}
      </div>

      {modal && (
        <div className="modal-fondo" onClick={() => setModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal-cabecera">
              <h2>Nuevo sprint</h2>
              <button className="cerrar-drawer" onClick={() => setModal(false)}>
                ✕
              </button>
            </header>
            <form onSubmit={crear} className="modal-cuerpo">
              <label>
                Objetivo
                <input
                  value={objetivo}
                  onChange={(e) => setObjetivo(e.target.value)}
                  placeholder="Ej: Autenticación e infraestructura base"
                  required
                />
              </label>
              <label>
                Rango del sprint
                <div className="rango-fechas">
                  <input
                    type="date"
                    value={inicio}
                    onChange={(e) => setInicio(e.target.value)}
                    required
                  />
                  <span className="rango-flecha">→</span>
                  <input
                    type="date"
                    value={fin}
                    min={inicio || undefined}
                    onChange={(e) => setFin(e.target.value)}
                    required
                  />
                </div>
                {inicio && fin && (
                  <small className="ayuda">
                    {Math.max(0, Math.round((new Date(fin).getTime() - new Date(inicio).getTime()) / 86400000))} días
                  </small>
                )}
              </label>
              <div className="modal-acciones">
                <button type="button" className="boton-secundario" onClick={() => setModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="boton-primario" disabled={enviando}>
                  {enviando ? "Creando…" : "Crear sprint"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
