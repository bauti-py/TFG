import { useEffect, useState } from "react";
import { api } from "../api";
import type { Bloqueo } from "../tipos";
import { Avatar, Badge } from "../ui";
import { cargarDirectorio, nombreDe } from "../directorio";

export default function Bloqueos() {
  const [bloqueos, setBloqueos] = useState<Bloqueo[]>([]);
  const [textos, setTextos] = useState<Record<number, string>>({});
  const [dir, setDir] = useState<Record<number, string>>({});
  const [dirListo, setDirListo] = useState(false);
  const [error, setError] = useState("");

  async function cargar() {
    try {
      setBloqueos(await api.get<Bloqueo[]>("/bloqueos"));
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
  }, []);

  async function resolver(b: Bloqueo, persistente: boolean, escalar: boolean) {
    setError("");
    const resolucion = (textos[b.id_bloqueo] || "").trim();
    // Ignorar no necesita texto. Resolver pide la resolución; Elevar pide la observación para el TL.
    if (!persistente && !resolucion) {
      setError(escalar ? "Escribí una observación para el Líder Técnico antes de elevar." : "Indicá una resolución para cerrar el bloqueo.");
      return;
    }
    try {
      await api.post(`/bloqueos/${b.id_bloqueo}/resolver`, {
        resolucion: resolucion || "Marcado como persistente por el SM",
        persistente,
        escalar_a_tl: escalar,
      });
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="seccion">
      <div className="cabecera-seccion">
        <div>
          <h1>Bloqueos</h1>
          <p className="sub">{bloqueos.length} bloqueos abiertos requieren atención</p>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {bloqueos.length > 0 && (
        <div className="aviso warn">
          <span className="aviso-icono">!</span>
          <div className="aviso-texto">
            <b>
              {bloqueos.length} bloqueo{bloqueos.length > 1 ? "s" : ""} sin resolver
            </b>
            <p>Resolvelos para no frenar el avance del sprint.</p>
          </div>
        </div>
      )}
      {bloqueos.length === 0 && <p className="vacio-grande">No hay bloqueos pendientes. 🎉</p>}

      <div className="lista-bloqueos">
        {bloqueos.map((b) => (
          <div key={b.id_bloqueo} className="card-bloqueo">
            <div className="card-bloqueo-cabecera">
              <span className="badge rojo">Sin resolver</span>
              <b>{b.descripcion_tarea || `Tarea #${b.id_tarea}`}</b>
              <Badge valor={b.estado} tono="ambar" />
            </div>
            {dirListo && b.id_usuario_asignado && (
              <div className="dev-bloqueo">
                <Avatar nombre={nombreDe(dir, b.id_usuario_asignado)} id={b.id_usuario_asignado} />
                <span>
                  Asignada a <b>{nombreDe(dir, b.id_usuario_asignado)}</b>
                </span>
              </div>
            )}
            <p className="contexto-bloqueo">{b.contexto}</p>
            <textarea
              placeholder="Describe la resolución o el motivo de la elevación…"
              value={textos[b.id_bloqueo] || ""}
              onChange={(e) => setTextos({ ...textos, [b.id_bloqueo]: e.target.value })}
            />
            <div className="acciones">
              <button className="boton-secundario" onClick={() => resolver(b, false, true)}>
                ↑ Elevar al TL
              </button>
              <button className="boton-secundario" onClick={() => resolver(b, true, false)}>
                Ignorar
              </button>
              <button className="boton-exito" onClick={() => resolver(b, false, false)}>
                ✓ Marcar resuelto
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
