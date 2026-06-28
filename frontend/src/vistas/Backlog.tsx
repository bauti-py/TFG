import { useEffect, useState } from "react";
import { api } from "../api";
import type { Prioridad, ResultadoAsignacion, Rol, Sprint, Tarea, Usuario } from "../tipos";
import { Avatar, BadgeEstado, BadgePrioridad, EntradaHabilidades } from "../ui";
import { cargarDirectorio, nombreDe } from "../directorio";
import { Iconos } from "../iconos";
import PanelSeguimiento from "./PanelSeguimiento";

const PRIORIDADES: Prioridad[] = ["BAJA", "MEDIA", "ALTA", "CRITICA"];

export default function Backlog({ rol }: { rol: Rol }) {
  const esTL = rol === "LIDER_TECNICO";
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [idSprint, setIdSprint] = useState<number | null>(null);
  const [tareas, setTareas] = useState<Tarea[]>([]);
  const [modal, setModal] = useState(false);
  const [descripcion, setDescripcion] = useState("");
  const [prioridad, setPrioridad] = useState<Prioridad>("MEDIA");
  const [habilidades, setHabilidades] = useState<string[]>([]);
  const [enviando, setEnviando] = useState(false);
  const [drawer, setDrawer] = useState<Tarea | null>(null);
  const [asignarModal, setAsignarModal] = useState<Tarea | null>(null);
  const [reintentando, setReintentando] = useState<number | null>(null);
  const [dir, setDir] = useState<Record<number, string>>({});
  const [dirListo, setDirListo] = useState(false);
  const [devs, setDevs] = useState<Usuario[]>([]);
  const [aviso, setAviso] = useState<{ tono: "ok" | "warn"; titulo: string; detalle?: string } | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    cargarDirectorio().then((d) => {
      setDir(d);
      setDirListo(true);
    });
    if (esTL) api.get<Usuario[]>("/usuarios").then((u) => setDevs(u.filter((d) => d.activo))).catch(() => {});
    api
      .get<Sprint[]>("/sprints")
      .then((s) => {
        setSprints(s);
        const activo = s.find((x) => x.estado === "ACTIVO") ?? s[0];
        if (activo) cargarTareas(activo.id_sprint);
      })
      .catch((e) => setError((e as Error).message));
  }, []);

  async function cargarTareas(id: number) {
    setIdSprint(id);
    setError("");
    try {
      setTareas(await api.get<Tarea[]>(`/sprints/${id}/tareas`));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function mostrarAsignacion(a: ResultadoAsignacion) {
    if (a.id_usuario_asignado) {
      setAviso({
        tono: "ok",
        titulo: `Tarea asignada a ${nombreDe(dir, a.id_usuario_asignado)}`,
        detalle: a.motivo || undefined,
      });
    } else {
      setAviso({
        tono: "warn",
        titulo: "Tarea sin asignar",
        detalle: a.motivo || undefined,
      });
    }
  }

  async function registrar(e: React.FormEvent) {
    e.preventDefault();
    if (idSprint === null) return;
    setError("");
    setAviso(null);
    setEnviando(true);
    try {
      const r = await api.post<{ tarea: Tarea; asignacion: ResultadoAsignacion }>(
        `/sprints/${idSprint}/tareas`,
        { descripcion, prioridad, habilidades_requeridas: habilidades }
      );
      mostrarAsignacion(r.asignacion);
      setDescripcion("");
      setPrioridad("MEDIA");
      setHabilidades([]);
      setModal(false);
      cargarTareas(idSprint);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function asignarManual(t: Tarea, idUsuario: number) {
    setError("");
    setAviso(null);
    try {
      const a = await api.post<ResultadoAsignacion>(`/tareas/${t.id_tarea}/asignar`, {
        id_usuario: idUsuario,
      });
      mostrarAsignacion(a);
      if (idSprint !== null) cargarTareas(idSprint);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function eliminar(t: Tarea) {
    if (!confirm(`¿Eliminar la tarea «${t.descripcion}»? No se puede deshacer.`)) return;
    setError("");
    try {
      await api.del(`/tareas/${t.id_tarea}`);
      if (idSprint !== null) cargarTareas(idSprint);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function reintentar(t: Tarea) {
    setError("");
    setAviso(null);
    setReintentando(t.id_tarea);
    try {
      const a = await api.post<ResultadoAsignacion>(`/tareas/${t.id_tarea}/reasignar`);
      mostrarAsignacion(a);
      if (idSprint !== null) cargarTareas(idSprint);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setReintentando(null);
    }
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Backlog del Proyecto</h1>
          <p className="sub">{tareas.length} tareas en el sprint seleccionado</p>
        </div>
        <div className="acciones-cabecera">
          <select value={idSprint ?? ""} onChange={(e) => cargarTareas(Number(e.target.value))}>
            <option value="" disabled>
              Elegir sprint…
            </option>
            {sprints.map((s) => (
              <option key={s.id_sprint} value={s.id_sprint}>
                #{s.id_sprint} · {s.objetivo}
              </option>
            ))}
          </select>
          {esTL && idSprint !== null && (
            <button className="boton-primario" onClick={() => setModal(true)}>
              + Nueva tarea
            </button>
          )}
        </div>
      </div>

      {aviso && (
        <div className={`aviso ${aviso.tono}`}>
          <span className="aviso-icono">{aviso.tono === "ok" ? "✓" : "!"}</span>
          <div className="aviso-texto">
            <b>{aviso.titulo}</b>
            {aviso.detalle && <p>{aviso.detalle}</p>}
          </div>
          <button className="aviso-cerrar" onClick={() => setAviso(null)}>
            ✕
          </button>
        </div>
      )}
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
              <tr key={t.id_tarea} data-prio={t.prioridad}>
                <td>
                  <div className="celda-tarea">
                    <b>{t.descripcion}</b>
                    {t.habilidades_requeridas.length > 0 && (
                      <div className="chips-mini">
                        {t.habilidades_requeridas.slice(0, 5).map((h) => (
                          <span key={h} className="chip-mini">
                            {h}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
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
                  ) : esTL ? (
                    <div className="botones-asignar">
                      <button
                        className="boton-icono"
                        title="Asignar con IA"
                        onClick={() => reintentar(t)}
                        disabled={reintentando === t.id_tarea}
                      >
                        {Iconos.robot}
                      </button>
                      <button
                        className="boton-icono"
                        title="Elegir desarrollador"
                        onClick={() => setAsignarModal(t)}
                      >
                        {Iconos.perfil}
                      </button>
                    </div>
                  ) : (
                    <span className="sin-asignar">Sin asignar</span>
                  )}
                </td>
                <td>
                  <div className="acciones-fila">
                    <button className="boton-icono" title="Seguimiento" onClick={() => setDrawer(t)}>
                      💬
                    </button>
                    {esTL && (
                      <button
                        className="boton-icono peligro"
                        title="Eliminar tarea"
                        onClick={() => eliminar(t)}
                      >
                        🗑
                      </button>
                    )}
                  </div>
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

      {modal && (
        <div className="modal-fondo" onClick={() => setModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal-cabecera">
              <h2>Nueva tarea</h2>
              <button className="cerrar-drawer" onClick={() => setModal(false)}>
                ✕
              </button>
            </header>
            <form onSubmit={registrar} className="modal-cuerpo">
              <label>
                Descripción
                <textarea
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  placeholder="Describe la tarea. La IA infiere las habilidades y asigna al mejor desarrollador."
                  rows={4}
                  required
                />
              </label>
              <label>
                Prioridad
                <div className="chips-prioridad">
                  {PRIORIDADES.map((p) => (
                    <button
                      key={p}
                      type="button"
                      data-prio={p}
                      className={`chip-prio ${prioridad === p ? "activo" : ""}`}
                      onClick={() => setPrioridad(p)}
                    >
                      {p.charAt(0) + p.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>
              </label>
              <label>
                Habilidades <small className="ayuda">(opcional; si lo dejás vacío, la IA las infiere)</small>
                <EntradaHabilidades
                  valores={habilidades}
                  onChange={setHabilidades}
                  placeholder="Escribí una habilidad y tocá +"
                />
              </label>
              <div className="modal-acciones">
                <button type="button" className="boton-secundario" onClick={() => setModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="boton-primario" disabled={enviando}>
                  {enviando ? "Creando…" : "✦ Crear y asignar con IA"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {asignarModal && (
        <div className="modal-fondo" onClick={() => setAsignarModal(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal-cabecera">
              <h2>Elegir desarrollador</h2>
              <button className="cerrar-drawer" onClick={() => setAsignarModal(null)}>
                ✕
              </button>
            </header>
            <div className="modal-cuerpo">
              <p className="sub">{asignarModal.descripcion}</p>
              <div className="lista-devs">
                {devs.map((d) => (
                  <button
                    key={d.id_usuario}
                    className="fila-dev-elegible"
                    onClick={() => {
                      asignarManual(asignarModal, d.id_usuario);
                      setAsignarModal(null);
                    }}
                  >
                    <Avatar nombre={d.nombre} id={d.id_usuario} />
                    <span>{d.nombre}</span>
                  </button>
                ))}
                {devs.length === 0 && <p className="vacio">No hay desarrolladores.</p>}
              </div>
            </div>
          </div>
        </div>
      )}

      {drawer && (
        <PanelSeguimiento
          idTarea={drawer.id_tarea}
          titulo={drawer.descripcion}
          puedeConsultar
          puedeResponder={false}
          onCerrar={() => {
            setDrawer(null);
            if (idSprint !== null) cargarTareas(idSprint);
          }}
        />
      )}
    </div>
  );
}
