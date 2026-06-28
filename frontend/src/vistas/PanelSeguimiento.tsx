import { useEffect, useState } from "react";
import { api } from "../api";
import type { ConsultaAvance, Mensaje, ResultadoSeguimiento } from "../tipos";

export default function PanelSeguimiento({
  idTarea,
  titulo,
  puedeConsultar,
  puedeResponder,
  onCerrar,
}: {
  idTarea: number;
  titulo: string;
  puedeConsultar: boolean;
  puedeResponder: boolean;
  onCerrar: () => void;
}) {
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [texto, setTexto] = useState("");
  const [info, setInfo] = useState("");
  const [error, setError] = useState("");

  async function cargar() {
    try {
      setMensajes(await api.get<Mensaje[]>(`/tareas/${idTarea}/seguimiento/conversacion`));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  useEffect(() => {
    cargar();
  }, [idTarea]);

  async function consultar() {
    setError("");
    setInfo("");
    try {
      const c = await api.post<ConsultaAvance>(`/tareas/${idTarea}/seguimiento/consulta`);
      setInfo(`Consulta generada: ${c.pregunta}`);
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function responder(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setInfo("");
    try {
      const r = await api.post<ResultadoSeguimiento>(`/tareas/${idTarea}/seguimiento/respuesta`, {
        texto,
      });
      setInfo(
        `Estado inferido: ${r.estado_inferido}. ${r.resumen}` +
          (r.genero_bloqueo ? " · se notificó un bloqueo al SM" : "") +
          (r.diferido ? " · la IA no respondió (diferido)" : "")
      );
      setTexto("");
      cargar();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="drawer-fondo" onClick={onCerrar}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <header className="drawer-cabecera">
          <div>
            <b>Asistente de avance</b>
            <small>{titulo}</small>
          </div>
          <button className="cerrar-drawer" onClick={onCerrar}>
            ✕
          </button>
        </header>

        <div className="conversacion">
          {mensajes.length === 0 && <p className="vacio">Sin conversación todavía.</p>}
          {mensajes.map((m, i) => (
            <div key={i} className={`burbuja ${m.autor === "sistema" ? "ia" : "dev"}`}>
              <span>{m.texto}</span>
              <time>{new Date(m.fecha).toLocaleString()}</time>
            </div>
          ))}
        </div>

        {info && <p className="info">{info}</p>}
        {error && <p className="error">{error}</p>}

        <footer className="drawer-pie">
          {puedeConsultar && (
            <button className="boton-secundario ancho" onClick={consultar}>
              Generar consulta de avance
            </button>
          )}
          {puedeResponder && (
            <form onSubmit={responder} className="responder">
              <input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Escribe tu respuesta aquí…"
                required
              />
              <button type="submit" className="boton-primario">
                Enviar
              </button>
            </form>
          )}
        </footer>
      </aside>
    </div>
  );
}
