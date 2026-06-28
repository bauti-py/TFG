import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dashboard as DatosDashboard, Rol, TareaTablero } from "../tipos";
import { Avatar, BadgePrioridad } from "../ui";
import { cargarDirectorio, nombreDe } from "../directorio";
import { Iconos } from "../iconos";

const COLUMNAS: { titulo: string; estados: string[]; tono: string }[] = [
  { titulo: "Backlog", estados: ["PENDIENTE", "PENDIENTE_ASIGNACION", "ASIGNACION_FALLIDA"], tono: "gris" },
  { titulo: "Asignado", estados: ["ASIGNADA"], tono: "azul" },
  { titulo: "En Progreso", estados: ["EN_PROGRESO"], tono: "ambar" },
  { titulo: "Bloqueada", estados: ["BLOQUEADA"], tono: "rojo" },
  { titulo: "Completado", estados: ["COMPLETADA"], tono: "verde" },
];

function tarjetas(col: Record<string, TareaTablero[]>, estados: string[]): TareaTablero[] {
  return estados.flatMap((e) => col[e] || []);
}

export default function Dashboard({
  rol,
  onSprint,
}: {
  rol: Rol;
  onSprint?: (objetivo: string | null) => void;
}) {
  const [datos, setDatos] = useState<DatosDashboard | null>(null);
  const [dir, setDir] = useState<Record<number, string>>({});
  const [dirListo, setDirListo] = useState(false);
  const [error, setError] = useState("");
  const [mostrarMetricas, setMostrarMetricas] = useState(true);
  const [filtroDev, setFiltroDev] = useState("");
  const [filtroEstado, setFiltroEstado] = useState("");
  const [mostrarFiltros, setMostrarFiltros] = useState(false);

  async function cargar() {
    setError("");
    try {
      const d = await api.get<DatosDashboard>("/dashboard");
      setDatos(d);
      onSprint?.(d.sprint?.objetivo ?? null);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    cargarDirectorio().then((d) => {
      setDir(d);
      setDirListo(true);
    });
    cargar();
    const id = setInterval(cargar, 8000); // refresco automático; /dashboard no usa IA
    return () => {
      clearInterval(id);
      onSprint?.(null);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!datos || !dirListo) return <p className="cargando">Cargando…</p>;
  if (datos.sprint === null && datos.mensaje)
    return <p className="vacio-grande">{datos.mensaje}</p>;

  const col = datos.columnas || {};
  const cuenta = (e: string) => (col[e] || []).length;
  const esGlobal = rol !== "DESARROLLADOR";

  const idsEnTablero = Array.from(
    new Set(
      Object.values(col)
        .flat()
        .map((t) => t.id_usuario_asignado)
        .filter((x): x is number => x != null)
    )
  );
  const pasaFiltros = (t: TareaTablero) =>
    !filtroDev || String(t.id_usuario_asignado) === filtroDev;
  const columnasVisibles = filtroEstado
    ? COLUMNAS.filter((c) => c.titulo === filtroEstado)
    : COLUMNAS;
  const hayFiltro = Boolean(filtroDev || filtroEstado);

  return (
    <div className="dashboard">
      {esGlobal && (
        <section className="bloque panel-metricas">
          <div className="cabecera-bloque">
            <h3>Resumen del sprint</h3>
            <button
              className="boton-icono"
              title={mostrarMetricas ? "Ocultar" : "Mostrar"}
              onClick={() => setMostrarMetricas((v) => !v)}
            >
              {mostrarMetricas ? Iconos.ojo : Iconos.ojoCerrado}
            </button>
          </div>
          <div className={`metricas-wrap ${mostrarMetricas ? "abierto" : ""}`}>
            <div className="cards-metricas">
              <div className="card-metrica gris">
                <span className="numero">{datos.total_tareas ?? 0}</span>
                <span className="etiqueta">Tareas totales</span>
              </div>
              <div className="card-metrica ambar">
                <span className="numero">{cuenta("EN_PROGRESO")}</span>
                <span className="etiqueta">En progreso</span>
              </div>
              <div className="card-metrica rojo">
                <span className="numero">{cuenta("BLOQUEADA")}</span>
                <span className="etiqueta">Bloqueadas</span>
              </div>
              <div className="card-metrica verde">
                <span className="numero">{datos.completadas ?? cuenta("COMPLETADA")}</span>
                <span className="etiqueta">Completadas</span>
              </div>
            </div>
          </div>
        </section>
      )}

      <section className="bloque">
        <div className="cabecera-bloque">
          <h3>Tablero del sprint</h3>
          <div className="acciones-bloque">
            {esGlobal && (
              <button
                className={`boton-icono ${hayFiltro ? "filtro-activo" : ""}`}
                title="Filtrar"
                onClick={() => setMostrarFiltros(true)}
              >
                {Iconos.filtro}
              </button>
            )}
            <button className="boton-icono" title="Refrescar" onClick={cargar}>
              {Iconos.refrescar}
            </button>
          </div>
        </div>
        {esGlobal && mostrarFiltros && (
          <div className="drawer-fondo" onClick={() => setMostrarFiltros(false)}>
            <aside className="drawer drawer-filtros" onClick={(e) => e.stopPropagation()}>
              <header className="drawer-cabecera">
                <b>Filtros</b>
                <button className="cerrar-drawer" onClick={() => setMostrarFiltros(false)}>
                  ✕
                </button>
              </header>
              <div className="filtros-cuerpo">
                <label>
                  Desarrollador
                  <select value={filtroDev} onChange={(e) => setFiltroDev(e.target.value)}>
                    <option value="">Todos</option>
                    {idsEnTablero.map((id) => (
                      <option key={id} value={id}>
                        {nombreDe(dir, id)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Estado
                  <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
                    <option value="">Todos</option>
                    {COLUMNAS.map((c) => (
                      <option key={c.titulo} value={c.titulo}>
                        {c.titulo}
                      </option>
                    ))}
                  </select>
                </label>
                <button
                  className="boton-secundario"
                  onClick={() => {
                    setFiltroDev("");
                    setFiltroEstado("");
                  }}
                  disabled={!hayFiltro}
                >
                  Resetear filtros
                </button>
              </div>
            </aside>
          </div>
        )}
        <div className="tablero">
          {columnasVisibles.map((c) => {
            const ts = tarjetas(col, c.estados).filter(pasaFiltros);
            return (
              <div key={c.titulo} className={`columna ${c.tono}`}>
                <header>
                  {c.titulo} <span className="cuenta">{ts.length}</span>
                </header>
                {ts.map((t) => (
                  <div key={t.id_tarea} className="tarjeta-tarea">
                    <BadgePrioridad valor={t.prioridad} />
                    <p>{t.descripcion}</p>
                    {t.id_usuario_asignado && (
                      <div className="pie-tarjeta">
                        <Avatar nombre={nombreDe(dir, t.id_usuario_asignado)} id={t.id_usuario_asignado} />
                        <small>{nombreDe(dir, t.id_usuario_asignado)}</small>
                      </div>
                    )}
                  </div>
                ))}
                {ts.length === 0 && <p className="col-vacia">—</p>}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
