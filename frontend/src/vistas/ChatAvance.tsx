import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Dashboard, Mensaje, ResultadoSeguimiento, TareaTablero } from "../tipos";

export default function ChatAvance() {
  const [abierto, setAbierto] = useState(false);
  const [tareas, setTareas] = useState<TareaTablero[]>([]);
  const [sel, setSel] = useState<number | null>(null);
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [pendiente, setPendiente] = useState(false);
  const finRef = useRef<HTMLDivElement>(null);

  async function revisarPendientes() {
    try {
      const d = await api.get<Dashboard>("/dashboard");
      const ts = Object.values(d.columnas || {}).flat();
      const convs = await Promise.all(
        ts.map((t) =>
          api.get<Mensaje[]>(`/tareas/${t.id_tarea}/seguimiento/conversacion`).catch(() => [] as Mensaje[])
        )
      );
      const hay = convs.some(
        (c) =>
          c.filter((m) => m.autor === "sistema").length >
          c.filter((m) => m.autor === "desarrollador").length
      );
      setPendiente(hay);
    } catch {
      
    }
  }

  useEffect(() => {
    revisarPendientes();
  }, []);

  useEffect(() => {
    if (!abierto) return;
    api
      .get<Dashboard>("/dashboard")
      .then((d) => {
        const ts = Object.values(d.columnas || {}).flat();
        setTareas(ts);
        if (ts.length && sel == null) setSel(ts[0].id_tarea);
      })
      .catch((e) => setError((e as Error).message));
  }, [abierto]);

  useEffect(() => {
    if (sel == null) return;
    let cancelado = false;
    (async () => {
      setError("");
      try {
        let conv = await api.get<Mensaje[]>(`/tareas/${sel}/seguimiento/conversacion`);
        if (conv.length === 0) {
          await api.post(`/tareas/${sel}/seguimiento/consulta`).catch(() => {});
          conv = await api.get<Mensaje[]>(`/tareas/${sel}/seguimiento/conversacion`);
        }
        if (!cancelado) setMensajes(conv);
      } catch (e) {
        if (!cancelado) setError((e as Error).message);
      }
    })();
    return () => {
      cancelado = true;
    };
  }, [sel]);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, abierto]);

  async function responder(e: React.FormEvent) {
    e.preventDefault();
    if (sel == null || !texto.trim()) return;
    const mio = texto;
    setTexto("");
    setCargando(true);
    setMensajes((m) => [...m, { autor: "desarrollador", texto: mio, fecha: new Date().toISOString() }]);
    try {
      const r = await api.post<ResultadoSeguimiento>(`/tareas/${sel}/seguimiento/respuesta`, { texto: mio });
      const reply = r.siguiente_pregunta || r.resumen;
      setMensajes((m) => [...m, { autor: "sistema", texto: reply, fecha: new Date().toISOString() }]);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
      revisarPendientes();
    }
  }

  const tareaSel = tareas.find((t) => t.id_tarea === sel);

  return (
    <>
      <button
        className={`fab-chat ${pendiente && !abierto ? "tiene-pendiente" : ""}`}
        title={pendiente ? "Tenés una consulta de avance sin responder" : "Asistente de avance"}
        onClick={() => setAbierto((v) => !v)}
      >
        {abierto ? (
          "✕"
        ) : (
          <img className="fab-mascota" src="/mascotin.svg" alt="Asistente" />
        )}
        {pendiente && !abierto && <span className="punto-chat" />}
      </button>

      {abierto && (
        <div className="chat-flotante">
          <header className="chat-cabecera">
            <div>
              <b>Asistente de avance</b>
              <small>{tareaSel ? tareaSel.descripcion : "Seguimiento de tus tareas"}</small>
            </div>
          </header>

          {tareas.length > 1 && (
            <select
              className="chat-selector"
              value={sel ?? ""}
              onChange={(e) => setSel(Number(e.target.value))}
            >
              {tareas.map((t) => (
                <option key={t.id_tarea} value={t.id_tarea}>
                  {t.descripcion}
                </option>
              ))}
            </select>
          )}

          <div className="chat-cuerpo">
            {tareas.length === 0 && <p className="vacio">No tenés tareas asignadas todavía.</p>}
            {mensajes.map((m, i) => (
              <div key={i} className={`burbuja ${m.autor === "sistema" ? "ia" : "dev"}`}>
                <span>{m.texto}</span>
              </div>
            ))}
            {cargando && <div className="burbuja ia escribiendo">escribiendo…</div>}
            <div ref={finRef} />
          </div>

          {error && <p className="error chat-error">{error}</p>}

          {tareas.length > 0 && (
            <form className="chat-pie" onSubmit={responder}>
              <input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Escribí tu respuesta…"
              />
              <button type="submit" className="boton-primario" disabled={cargando}>
                ➤
              </button>
            </form>
          )}
        </div>
      )}
    </>
  );
}
