import { useState } from "react";

const COLORES_AVATAR = ["#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#6366f1", "#60a5fa"];

export function EntradaHabilidades({
  valores,
  onChange,
  placeholder,
}: {
  valores: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [texto, setTexto] = useState("");

  function agregar() {
    const v = texto.trim().toLowerCase();
    if (v && !valores.includes(v)) onChange([...valores, v]);
    setTexto("");
  }

  return (
    <div className="entrada-chips">
      <div className="entrada-chips-fila">
        <input
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              agregar();
            }
          }}
          placeholder={placeholder}
        />
        <button type="button" className="boton-secundario" onClick={agregar} title="Agregar">
          +
        </button>
      </div>
      {valores.length > 0 && (
        <div className="chips">
          {valores.map((v) => (
            <span
              key={v}
              className="badge gris chip-quitable"
              onClick={() => onChange(valores.filter((x) => x !== v))}
              title="Quitar"
            >
              {v} ✕
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function Avatar({ nombre, id }: { nombre: string; id?: number }) {
  const semilla = id ?? nombre.length;
  const color = COLORES_AVATAR[Math.abs(semilla) % COLORES_AVATAR.length];
  const iniciales = nombre
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <span className="avatar" style={{ background: color }}>
      {iniciales}
    </span>
  );
}

const COLOR_PRIORIDAD: Record<string, string> = {
  CRITICA: "rojo",
  ALTA: "rojo",
  MEDIA: "ambar",
  BAJA: "verde",
};

const COLOR_ESTADO: Record<string, string> = {
  PENDIENTE: "gris",
  PENDIENTE_ASIGNACION: "ambar",
  ASIGNADA: "azul",
  EN_PROGRESO: "ambar",
  BLOQUEADA: "rojo",
  COMPLETADA: "verde",
  ASIGNACION_FALLIDA: "rojo",
};

export function BadgePrioridad({ valor }: { valor: string }) {
  return <span className={`badge ${COLOR_PRIORIDAD[valor] || "gris"}`}>{valor}</span>;
}

export function BadgeEstado({ valor }: { valor: string }) {
  return <span className={`badge ${COLOR_ESTADO[valor] || "gris"}`}>{valor.replace(/_/g, " ")}</span>;
}

export function Badge({ valor, tono = "azul" }: { valor: string; tono?: string }) {
  return <span className={`badge ${tono}`}>{valor}</span>;
}

export function BarraCarga({ porcentaje }: { porcentaje: number }) {
  const tono = porcentaje >= 85 ? "rojo" : porcentaje >= 60 ? "ambar" : "verde";
  return (
    <div className="barra-carga">
      <div className={`relleno ${tono}`} style={{ width: `${Math.min(porcentaje, 100)}%` }} />
    </div>
  );
}
