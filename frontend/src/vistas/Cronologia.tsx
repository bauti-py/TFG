import type { EventoCronologia } from "../tipos";

const fechaHora = (f: string) =>
  new Date(f).toLocaleString("es-AR", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });

const ESTADO_LEGIBLE: Record<string, string> = {
  ASIGNADA: "Asignada",
  EN_PROGRESO: "En progreso",
  BLOQUEADA: "Bloqueada",
  COMPLETADA: "Completada",
};

const legible = (e: string | null) => ESTADO_LEGIBLE[e ?? ""] ?? e ?? "—";

export default function Cronologia({ eventos }: { eventos: EventoCronologia[] }) {
  const estados = eventos.filter((e) => e.tipo === "estado");
  if (estados.length === 0) return <p className="muted chico">Todavía no hay actividad registrada.</p>;
  return (
    <ul className="cronologia">
      {estados.map((ev, i) => {
        const prev = i > 0 ? legible(estados[i - 1].estado) : null;
        const cur = legible(ev.estado);
        return (
          <li key={i} className="crono-estado">
            <time>{fechaHora(ev.fecha)}</time>
            <span className="crono-hito">⟳ {prev ? `${prev} → ${cur}` : cur}</span>
          </li>
        );
      })}
    </ul>
  );
}
