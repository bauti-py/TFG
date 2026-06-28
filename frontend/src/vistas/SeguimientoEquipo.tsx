import { useEffect, useState } from "react";
import { api } from "../api";
import type { ActividadDev, EventoCronologia, ResumenDev } from "../tipos";
import { Avatar, BadgeEstado } from "../ui";
import Cronologia from "./Cronologia";

const fechaCorta = (f: string | null) =>
  f ? new Date(f).toLocaleDateString("es-AR", { day: "2-digit", month: "short" }) : null;

export default function SeguimientoEquipo() {
  const [equipo, setEquipo] = useState<ActividadDev[]>([]);
  const [abiertos, setAbiertos] = useState<Set<number>>(new Set());
  const [genDev, setGenDev] = useState<number | null>(null);
  const [genTarea, setGenTarea] = useState<number | null>(null);
  const [cronoTarea, setCronoTarea] = useState<Record<number, EventoCronologia[]>>({});
  const [aviso, setAviso] = useState<Record<number, string>>({});
  const [error, setError] = useState("");

  useEffect(() => {
    api.get<ActividadDev[]>("/equipo/actividad").then(setEquipo).catch((e) => setError((e as Error).message));
  }, []);

  function toggle(id: number) {
    setAbiertos((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  }

  async function resumenDev(id: number) {
    setGenDev(id);
    setAviso((a) => ({ ...a, [id]: "" }));
    setAbiertos((s) => new Set(s).add(id));
    try {
      const r = await api.post<ResumenDev>(`/equipo/${id}/resumen`);
      if (r.sin_servicio) {
        setAviso((a) => ({ ...a, [id]: "El asistente está sin servicio por ahora (cuota agotada)." }));
      } else {
        setEquipo((eq) => eq.map((d) => (d.id_usuario === id ? { ...d, resumen: r.resumen, resumen_fecha: r.fecha } : d)));
      }
    } catch (e) {
      setAviso((a) => ({ ...a, [id]: (e as Error).message }));
    } finally {
      setGenDev(null);
    }
  }

  async function cronologia(idTarea: number) {
    // Toggle: si ya está abierta, la cierro.
    if (cronoTarea[idTarea]) {
      setCronoTarea((m) => {
        const n = { ...m };
        delete n[idTarea];
        return n;
      });
      return;
    }
    setGenTarea(idTarea);
    try {
      const ev = await api.get<EventoCronologia[]>(`/tareas/${idTarea}/seguimiento/cronologia`);
      setCronoTarea((m) => ({ ...m, [idTarea]: ev }));
    } catch (e) {
      setAviso((a) => ({ ...a, [idTarea]: (e as Error).message }));
    } finally {
      setGenTarea(null);
    }
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Seguimiento</h1>
          <p className="sub">Cada desarrollador, su avance y el de cada tarea del sprint activo</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {!error && equipo.length === 0 && (
        <p className="vacio-grande">No hay desarrolladores o no hay un sprint activo.</p>
      )}

      <div className="lista-equipo">
        {equipo.map((d) => {
          const abierto = abiertos.has(d.id_usuario);
          return (
            <div key={d.id_usuario} className={`card-dev-seguimiento ${abierto ? "abierta" : ""}`}>
              <div className="card-dev-cabecera" onClick={() => toggle(d.id_usuario)} role="button">
                <span className="chevron">{abierto ? "▾" : "▸"}</span>
                <Avatar nombre={d.nombre} id={d.id_usuario} />
                <div className="card-dev-info">
                  <b>{d.nombre}</b>
                  <small>{d.seniority} · {d.tareas.length} tarea{d.tareas.length === 1 ? "" : "s"}</small>
                </div>
                <button
                  className="boton-icono libro"
                  title="Resumen general del dev"
                  onClick={(e) => {
                    e.stopPropagation();
                    resumenDev(d.id_usuario);
                  }}
                  disabled={genDev === d.id_usuario}
                >
                  📖
                </button>
              </div>

              {abierto && (
                <div className="card-dev-cuerpo">
                  <div className="resumen-ia">
                    <span className="resumen-ia-titulo">✦ Panorama del dev</span>
                    {genDev === d.id_usuario ? (
                      <p className="muted">Generando…</p>
                    ) : d.resumen ? (
                      <>
                        <p>{d.resumen}</p>
                        {d.resumen_fecha && (
                          <time className="resumen-ia-fecha">Actualizado {new Date(d.resumen_fecha).toLocaleString("es-AR")}</time>
                        )}
                      </>
                    ) : (
                      <p className="muted">Tocá 📖 (arriba) para generar el panorama general.</p>
                    )}
                    {aviso[d.id_usuario] && <p className="error chico">{aviso[d.id_usuario]}</p>}
                  </div>

                  {d.tareas.length === 0 ? (
                    <p className="vacio">Sin tareas asignadas en este sprint.</p>
                  ) : (
                    <div className="tareas-dev-detalle">
                      {d.tareas.map((t) => (
                        <div key={t.id_tarea} className="tarea-status">
                          <div className="tarea-status-cab">
                            <span className="tarea-dev-desc">{t.descripcion}</span>
                            <BadgeEstado valor={t.estado} />
                            <button
                              className="boton-icono libro"
                              title="Ver cronología de la tarea"
                              onClick={() => cronologia(t.id_tarea)}
                              disabled={genTarea === t.id_tarea}
                            >
                              📖
                            </button>
                          </div>
                          <div className="tarea-status-fechas">
                            {fechaCorta(t.fecha_inicio) ? `inició ${fechaCorta(t.fecha_inicio)}` : "no arrancada"}
                            {t.fecha_cierre ? ` · cerró ${fechaCorta(t.fecha_cierre)}` : ""}
                          </div>
                          {aviso[t.id_tarea] && <p className="error chico">{aviso[t.id_tarea]}</p>}
                          {genTarea === t.id_tarea && <p className="muted chico">Cargando cronología…</p>}
                          {cronoTarea[t.id_tarea] && <Cronologia eventos={cronoTarea[t.id_tarea]} />}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
