import { useEffect, useState } from "react";
import { api } from "../api";
import type { Bloqueo, EventoCronologia, ResumenSeguimiento, Rol, Sprint, Tarea } from "../tipos";
import { Avatar, Badge, BadgeEstado, BadgePrioridad } from "../ui";
import { cargarDirectorio, nombreDe } from "../directorio";
import PanelSeguimiento from "./PanelSeguimiento";
import Cronologia from "./Cronologia";

export default function Seguimiento({ rol }: { rol: Rol }) {
  return rol === "LIDER_TECNICO" ? <Informes /> : <SeguimientoSprint />;
}

function Informes() {
  const [elevados, setElevados] = useState<Bloqueo[]>([]);
  const [resumenes, setResumenes] = useState<Record<number, string>>({});
  const [cronos, setCronos] = useState<Record<number, EventoCronologia[]>>({});
  const [textos, setTextos] = useState<Record<number, string>>({});
  const [resolviendo, setResolviendo] = useState<number | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    cargar();
  }, []);

  async function cargar() {
    try {
      const lista = await api.get<Bloqueo[]>("/bloqueos/elevados");
      setElevados(lista);
      lista.forEach(async (b) => {
        try {
          const r = await api.post<ResumenSeguimiento>(`/tareas/${b.id_tarea}/seguimiento/resumen`);
          setResumenes((m) => ({ ...m, [b.id_bloqueo]: r.resumen }));
        } catch {
          /* resumen best-effort */
        }
        try {
          const ev = await api.get<EventoCronologia[]>(`/tareas/${b.id_tarea}/seguimiento/cronologia`);
          setCronos((m) => ({ ...m, [b.id_tarea]: ev }));
        } catch {
          /* cronología best-effort */
        }
      });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function resolver(b: Bloqueo) {
    const resolucion = textos[b.id_bloqueo] || "";
    if (!resolucion) {
      setError("Indicá cómo se resuelve antes de cerrar.");
      return;
    }
    setError("");
    setResolviendo(b.id_bloqueo);
    try {
      await api.post(`/bloqueos/${b.id_bloqueo}/resolver-tl`, { resolucion });
      cargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setResolviendo(null);
    }
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Informes</h1>
          <p className="sub">Bloqueos que el Scrum Master elevó para tu resolución</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {elevados.length === 0 && !error && (
        <p className="vacio-grande">El Scrum Master todavía no elevó ningún bloqueo.</p>
      )}

      <div className="lista-bloqueos">
        {elevados.map((b) => (
          <div key={b.id_bloqueo} className="card-bloqueo">
            <div className="card-bloqueo-cabecera">
              <span className="badge ambar">Elevado por el SM</span>
              <b>{b.descripcion_tarea || `Tarea #${b.id_tarea}`}</b>
              <Badge valor={b.estado} tono="ambar" />
            </div>
            <p className="contexto-bloqueo">{b.contexto}</p>

            {b.resolucion && (
              <div className="nota-sm">
                <span className="nota-sm-titulo">🗣️ Observación del Scrum Master</span>
                <p>{b.resolucion}</p>
              </div>
            )}

            <div className="resumen-ia">
              <span className="resumen-ia-titulo">✦ Resumen de la IA</span>
              <p>{resumenes[b.id_bloqueo] ?? "Generando resumen…"}</p>
            </div>

            <details className="informe-cronologia">
              <summary>Ver actividad de la tarea</summary>
              <Cronologia eventos={cronos[b.id_tarea] ?? []} />
            </details>

            <textarea
              placeholder="Describí la resolución para el desarrollador…"
              value={textos[b.id_bloqueo] || ""}
              onChange={(e) => setTextos({ ...textos, [b.id_bloqueo]: e.target.value })}
            />
            <div className="acciones">
              <button
                className="boton-exito"
                onClick={() => resolver(b)}
                disabled={resolviendo === b.id_bloqueo}
              >
                {resolviendo === b.id_bloqueo ? "Resolviendo…" : "✓ Marcar resuelto"}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SeguimientoSprint() {
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [idSprint, setIdSprint] = useState<number | null>(null);
  const [tareas, setTareas] = useState<Tarea[]>([]);
  const [dir, setDir] = useState<Record<number, string>>({});
  const [dirListo, setDirListo] = useState(false);
  const [drawer, setDrawer] = useState<Tarea | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    cargarDirectorio().then((d) => {
      setDir(d);
      setDirListo(true);
    });
    api
      .get<Sprint[]>("/sprints")
      .then((s) => {
        setSprints(s);
        const activo = s.find((x) => x.estado === "ACTIVO") ?? s[0];
        if (activo) cargar(activo.id_sprint);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  async function cargar(id: number) {
    setIdSprint(id);
    setError("");
    try {
      setTareas(await api.get<Tarea[]>(`/sprints/${id}/tareas`));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Seguimiento</h1>
          <p className="sub">Seguí el avance de las tareas del sprint</p>
        </div>
        <div className="acciones-cabecera">
          <select value={idSprint ?? ""} onChange={(e) => cargar(Number(e.target.value))}>
            <option value="" disabled>
              Elegir sprint…
            </option>
            {sprints.map((s) => (
              <option key={s.id_sprint} value={s.id_sprint}>
                #{s.id_sprint} · {s.objetivo}
              </option>
            ))}
          </select>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      <div className="tabla-tarjeta">
        <table>
          <thead>
            <tr>
              <th>Tarea</th>
              <th>Prioridad</th>
              <th>Estado</th>
              <th>Asignado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {dirListo &&
              tareas.map((t) => (
                <tr key={t.id_tarea}>
                  <td>
                    <b>{t.descripcion}</b>
                  </td>
                  <td>
                    <BadgePrioridad valor={t.prioridad} />
                  </td>
                  <td>
                    <BadgeEstado valor={t.estado} />
                  </td>
                  <td>
                    {t.id_usuario_asignado ? (
                      <div className="celda-dev">
                        <Avatar nombre={nombreDe(dir, t.id_usuario_asignado)} id={t.id_usuario_asignado} />
                        <span>{nombreDe(dir, t.id_usuario_asignado)}</span>
                      </div>
                    ) : (
                      <span className="sin-asignar">Sin asignar</span>
                    )}
                  </td>
                  <td>
                    <button className="boton-icono" title="Seguimiento" onClick={() => setDrawer(t)}>
                      💬
                    </button>
                  </td>
                </tr>
              ))}
            {dirListo && tareas.length === 0 && (
              <tr>
                <td colSpan={5} className="vacio">
                  No hay tareas en este sprint.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {drawer && (
        <PanelSeguimiento
          idTarea={drawer.id_tarea}
          titulo={drawer.descripcion}
          puedeConsultar
          puedeResponder={false}
          onCerrar={() => setDrawer(null)}
        />
      )}
    </div>
  );
}
