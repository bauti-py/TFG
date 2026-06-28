import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Dashboard, Mensaje, ResultadoSeguimiento, TareaTablero } from "../tipos";

// Pendiente = el sistema dijo algo que el desarrollador todavía no respondió.
const esPendiente = (c: Mensaje[]) =>
  c.filter((m) => m.autor === "sistema").length > c.filter((m) => m.autor === "desarrollador").length;

export default function ChatAvance() {
  const [abierto, setAbierto] = useState(false);
  const [tareas, setTareas] = useState<TareaTablero[]>([]);
  const [convs, setConvs] = useState<Record<number, Mensaje[]>>({});
  const [sel, setSel] = useState<number | null>(null);
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const finRef = useRef<HTMLDivElement>(null);

  const mensajes = sel != null ? convs[sel] ?? [] : [];
  const pendienteGlobal = tareas.some((t) => esPendiente(convs[t.id_tarea] ?? []));

  async function cargarTodo() {
    try {
      const d = await api.get<Dashboard>("/dashboard");
      const ts = Object.values(d.columnas || {}).flat();
      setTareas(ts);
      const pares = await Promise.all(
        ts.map(
          async (t) =>
            [t.id_tarea, await api.get<Mensaje[]>(`/tareas/${t.id_tarea}/seguimiento/conversacion`).catch(() => [] as Mensaje[])] as const
        )
      );
      const mapa = Object.fromEntries(pares);
      setConvs(mapa);
      return { ts, mapa };
    } catch (e) {
      setError((e as Error).message);
      return { ts: [] as TareaTablero[], mapa: {} as Record<number, Mensaje[]> };
    }
  }

  // Carga inicial: alimenta el badge del FAB aunque el chat esté cerrado.
  useEffect(() => {
    cargarTodo();
  }, []);

  // Al abrir, refresca y abre la primera conversación con algo pendiente.
  useEffect(() => {
    if (!abierto) return;
    cargarTodo().then(({ ts, mapa }) => {
      if (sel != null) return;
      const pend = ts.find((t) => esPendiente(mapa[t.id_tarea] ?? []));
      setSel((pend ?? ts[0])?.id_tarea ?? null);
    });
  }, [abierto]);

  // Si la conversación elegida está vacía, genera la consulta inicial.
  useEffect(() => {
    if (sel == null || (convs[sel] ?? []).length > 0) return;
    let cancelado = false;
    (async () => {
      await api.post(`/tareas/${sel}/seguimiento/consulta`).catch(() => {});
      const conv = await api.get<Mensaje[]>(`/tareas/${sel}/seguimiento/conversacion`).catch(() => [] as Mensaje[]);
      if (!cancelado) setConvs((c) => ({ ...c, [sel]: conv }));
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
    const id = sel;
    setTexto("");
    setCargando(true);
    setError("");
    setConvs((c) => ({
      ...c,
      [id]: [...(c[id] ?? []), { autor: "desarrollador", texto: mio, fecha: new Date().toISOString() }],
    }));
    try {
      const r = await api.post<ResultadoSeguimiento>(`/tareas/${id}/seguimiento/respuesta`, { texto: mio });
      const reply = r.siguiente_pregunta || r.resumen;
      setConvs((c) => ({ ...c, [id]: [...(c[id] ?? []), { autor: "sistema", texto: reply, fecha: new Date().toISOString() }] }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setCargando(false);
    }
  }

  const tareaSel = tareas.find((t) => t.id_tarea === sel);

  return (
    <>
      <button
        className={`fab-chat ${pendienteGlobal && !abierto ? "tiene-pendiente" : ""}`}
        title={pendienteGlobal ? "Tenés una consulta de avance sin responder" : "Asistente de avance"}
        onClick={() => setAbierto((v) => !v)}
      >
        {abierto ? "✕" : <img className="fab-mascota" src="/mascotin.svg" alt="Asistente" />}
        {pendienteGlobal && !abierto && <span className="punto-chat" />}
      </button>

      {abierto && (
        <div className="chat-flotante">
          <header className="chat-cabecera">
            <img className="chat-cabecera-mascota" src="/mascotin.svg" alt="" />
            <div>
              <b>Asistente de avance</b>
              <small>Seguimiento de tus tareas</small>
            </div>
          </header>

          {tareas.length === 0 ? (
            <div className="chat-cuerpo">
              <p className="vacio">No tenés tareas asignadas todavía.</p>
            </div>
          ) : (
            <div className="chat-split">
              <aside className="chat-lista-col">
                <p className="chat-col-titulo">Conversaciones</p>
                <ul className="chat-lista">
                  {tareas.map((t) => (
                    <li
                      key={t.id_tarea}
                      className={`${t.id_tarea === sel ? "activa" : ""} ${
                        esPendiente(convs[t.id_tarea] ?? []) ? "pendiente" : ""
                      }`}
                      onClick={() => setSel(t.id_tarea)}
                    >
                      <span className="chat-lista-num">Tarea #{t.id_tarea}</span>
                      <span className="chat-lista-desc">{t.descripcion}</span>
                    </li>
                  ))}
                </ul>
              </aside>

              <div className="chat-panel">
                {tareaSel && (
                  <div className="chat-panel-cabecera">
                    <span className="chat-panel-num">Tarea #{tareaSel.id_tarea}</span>
                    <b>{tareaSel.descripcion}</b>
                    <span className={`chat-estado ${esPendiente(mensajes) ? "pend" : "ok"}`}>
                      {esPendiente(mensajes) ? "Esperando tu respuesta" : "Al día"}
                    </span>
                  </div>
                )}

                <div className="chat-cuerpo">
                  {mensajes.map((m, i) => (
                    <div key={i} className={`burbuja ${m.autor === "sistema" ? "ia" : "dev"}`}>
                      <span>{m.texto}</span>
                    </div>
                  ))}
                  {cargando && <div className="burbuja ia escribiendo">escribiendo…</div>}
                  <div ref={finRef} />
                </div>

                {error && <p className="error chat-error">{error}</p>}

                <form className="chat-pie" onSubmit={responder}>
                  <input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Escribí tu respuesta…" />
                  <button type="submit" className="boton-primario" disabled={cargando}>
                    ➤
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
