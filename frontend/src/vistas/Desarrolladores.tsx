import { useEffect, useState } from "react";
import { api } from "../api";
import type { Dashboard, PerfilSalida, Usuario } from "../tipos";
import { Avatar, Badge, BarraCarga, EntradaHabilidades } from "../ui";

const CAP_CARGA = 5;

export default function Desarrolladores() {
  const [devs, setDevs] = useState<Usuario[]>([]);
  const [seniority, setSeniority] = useState<Record<number, string>>({});
  const [carga, setCarga] = useState<Record<string, number>>({});
  const [modal, setModal] = useState(false);
  const [perfilVer, setPerfilVer] = useState<{ nombre: string; perfil: PerfilSalida } | null>(null);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [lenguajes, setLenguajes] = useState<string[]>([]);
  const [nivel, setNivel] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState("");

  async function cargar() {
    setError("");
    try {
      const lista = await api.get<Usuario[]>("/usuarios");
      setDevs(lista);
      const perfiles = await Promise.all(
        lista.map((d) =>
          api.get<PerfilSalida>(`/usuarios/${d.id_usuario}/perfil`).catch(() => null)
        )
      );
      const mapa: Record<number, string> = {};
      perfiles.forEach((p, i) => {
        if (p?.seniority) mapa[lista[i].id_usuario] = p.seniority;
      });
      setSeniority(mapa);
      const dash = await api.get<Dashboard>("/dashboard");
      setCarga(dash.tareas_activas_por_desarrollador || {});
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
      await api.post("/usuarios", {
        nombre,
        email,
        password,
        rol: "DESARROLLADOR",
        perfil: {
          lenguajes,
          seniority: nivel || null,
        },
      });
      setNombre("");
      setEmail("");
      setPassword("");
      setLenguajes([]);
      setNivel("");
      setModal(false);
      cargar();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setEnviando(false);
    }
  }

  async function verPerfil(d: Usuario) {
    setError("");
    try {
      const perfil = await api.get<PerfilSalida>(`/usuarios/${d.id_usuario}/perfil`);
      setPerfilVer({ nombre: d.nombre, perfil });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function alternarActivo(d: Usuario) {
    if (
      d.activo &&
      !confirm(`¿Dar de baja a ${d.nombre}? Sus tareas activas quedarán sin asignar para reasignar.`)
    )
      return;
    setError("");
    try {
      if (d.activo) await api.del(`/usuarios/${d.id_usuario}`);
      else await api.put(`/usuarios/${d.id_usuario}`, { activo: true });
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  const activos = devs.filter((d) => d.activo).length;

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Desarrolladores del equipo</h1>
          <p className="sub">{activos} desarrolladores activos en el sprint actual</p>
        </div>
        <button className="boton-primario" onClick={() => setModal(true)}>
          + Nuevo desarrollador
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <div className="tabla-tarjeta">
        <table>
          <thead>
            <tr>
              <th>Desarrollador</th>
              <th>Email</th>
              <th>Seniority</th>
              <th>Carga</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {devs.map((d) => {
              const activas = carga[String(d.id_usuario)] || 0;
              return (
                <tr key={d.id_usuario} className={d.activo ? "" : "inactivo"}>
                  <td>
                    <div className="celda-dev">
                      <Avatar nombre={d.nombre} id={d.id_usuario} />
                      <span>{d.nombre}</span>
                    </div>
                  </td>
                  <td>{d.email}</td>
                  <td>{seniority[d.id_usuario] ? <Badge valor={seniority[d.id_usuario]} /> : "—"}</td>
                  <td>
                    <div className="celda-carga">
                      <BarraCarga porcentaje={(activas / CAP_CARGA) * 100} />
                      <small>{activas}</small>
                    </div>
                  </td>
                  <td>
                    <Badge valor={d.activo ? "Activo" : "Inactivo"} tono={d.activo ? "verde" : "gris"} />
                  </td>
                  <td>
                    <div className="acciones-fila">
                      <button className="boton-secundario" onClick={() => verPerfil(d)}>
                        Ver perfil
                      </button>
                      <button className="boton-secundario" onClick={() => alternarActivo(d)}>
                        {d.activo ? "Dar de baja" : "Reactivar"}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {devs.length === 0 && (
              <tr>
                <td colSpan={6} className="vacio">
                  No hay desarrolladores todavía.
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
              <h2>Nuevo desarrollador</h2>
              <button className="cerrar-drawer" onClick={() => setModal(false)}>
                ✕
              </button>
            </header>
            <form onSubmit={crear} className="modal-cuerpo">
              <label>
                Nombre
                <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
              </label>
              <label>
                Email
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
              </label>
              <label>
                Contraseña
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
              </label>
              <label>
                Lenguajes <small className="ayuda">(escribí cada uno y tocá +)</small>
                <EntradaHabilidades
                  valores={lenguajes}
                  onChange={setLenguajes}
                  placeholder="python, react, sql…"
                />
              </label>
              <label>
                Seniority
                <select value={nivel} onChange={(e) => setNivel(e.target.value)}>
                  <option value="">Sin especificar</option>
                  <option value="Junior">Junior</option>
                  <option value="Semi Senior">Semi Senior</option>
                  <option value="Senior">Senior</option>
                </select>
              </label>
              <div className="modal-acciones">
                <button type="button" className="boton-secundario" onClick={() => setModal(false)}>
                  Cancelar
                </button>
                <button type="submit" className="boton-primario" disabled={enviando}>
                  {enviando ? "Creando…" : "Dar de alta"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {perfilVer && (
        <div className="modal-fondo" onClick={() => setPerfilVer(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <header className="modal-cabecera">
              <h2>Perfil de {perfilVer.nombre}</h2>
              <button className="cerrar-drawer" onClick={() => setPerfilVer(null)}>
                ✕
              </button>
            </header>
            <div className="modal-cuerpo perfil-detalle">
              <div className="perfil-fila">
                <span className="perfil-etiqueta">Seniority</span>
                <span>{perfilVer.perfil.seniority || "—"}</span>
              </div>
              <ListaChips titulo="Lenguajes" items={perfilVer.perfil.lenguajes} />
              <ListaChips titulo="Dominios" items={perfilVer.perfil.dominios} />
              <ListaChips titulo="Frameworks" items={perfilVer.perfil.frameworks} />
              <div className="perfil-bloque">
                <span className="perfil-etiqueta">
                  Histórico aprendido <small className="ayuda">(suma 1 por cada tarea completada con esa tecnología)</small>
                </span>
                {Object.keys(perfilVer.perfil.metricas_agregadas || {}).length === 0 ? (
                  <p className="vacio">Todavía no completó tareas que aporten al histórico.</p>
                ) : (
                  <div className="chips">
                    {Object.entries(perfilVer.perfil.metricas_agregadas as Record<string, number>)
                      .sort((a, b) => b[1] - a[1])
                      .map(([tec, n]) => (
                        <span key={tec} className="badge azul">
                          {tec} · {n}
                        </span>
                      ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ListaChips({ titulo, items }: { titulo: string; items: string[] }) {
  return (
    <div className="perfil-bloque">
      <span className="perfil-etiqueta">{titulo}</span>
      {items && items.length > 0 ? (
        <div className="chips">
          {items.map((it) => (
            <span key={it} className="badge gris">
              {it}
            </span>
          ))}
        </div>
      ) : (
        <p className="vacio">—</p>
      )}
    </div>
  );
}
