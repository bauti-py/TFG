import { useEffect, useState } from "react";
import { api, cerrarSesion, guardarSesion } from "./api";
import type { Bloqueo, Rol, Sesion } from "./tipos";
import { Avatar } from "./ui";
import { Iconos } from "./iconos";
import Login from "./vistas/Login";
import Dashboard from "./vistas/Dashboard";
import Backlog from "./vistas/Backlog";
import Desarrolladores from "./vistas/Desarrolladores";
import Sprints from "./vistas/Sprints";
import Bloqueos from "./vistas/Bloqueos";
import Seguimiento from "./vistas/Seguimiento";
import SeguimientoEquipo from "./vistas/SeguimientoEquipo";
import ChatAvance from "./vistas/ChatAvance";

function cargarSesion(): Sesion | null {
  const crudo = localStorage.getItem("sesion");
  return crudo ? (JSON.parse(crudo) as Sesion) : null;
}

interface Item {
  clave: string;
  etiqueta: string;
  icono: keyof typeof Iconos;
}

const ROL_LEGIBLE: Record<Rol, string> = {
  LIDER_TECNICO: "Líder Técnico",
  SCRUM_MASTER: "Scrum Master",
  DESARROLLADOR: "Desarrollador",
};

const NAV: Record<Rol, Item[]> = {
  LIDER_TECNICO: [
    { clave: "dashboard", etiqueta: "Dashboard", icono: "dashboard" },
    { clave: "backlog", etiqueta: "Backlog del sprint", icono: "backlog" },
    { clave: "devs", etiqueta: "Gestión de Desarrolladores", icono: "devs" },
    { clave: "seguimiento", etiqueta: "Informes", icono: "seguimiento" },
  ],
  SCRUM_MASTER: [
    { clave: "dashboard", etiqueta: "Dashboard", icono: "dashboard" },
    { clave: "sprints", etiqueta: "Gestión de Sprints", icono: "sprint" },
    { clave: "bloqueos", etiqueta: "Bloqueos", icono: "bloqueos" },
    { clave: "equipo", etiqueta: "Seguimiento", icono: "seguimiento" },
  ],
  DESARROLLADOR: [{ clave: "dashboard", etiqueta: "Dashboard", icono: "dashboard" }],
};

export default function App() {
  const [sesion, setSesion] = useState<Sesion | null>(cargarSesion);
  const [vista, setVista] = useState("dashboard");
  const [bloqueosAbiertos, setBloqueosAbiertos] = useState(0);
  const [sprintActivo, setSprintActivo] = useState<string | null>(null);

  useEffect(() => {
    if (!sesion || sesion.rol !== "SCRUM_MASTER") return;
    api
      .get<Bloqueo[]>("/bloqueos")
      .then((b) => setBloqueosAbiertos(b.length))
      .catch(() => setBloqueosAbiertos(0));
  }, [sesion, vista]);

  function entrar(s: Sesion) {
    guardarSesion(s.token);
    localStorage.setItem("sesion", JSON.stringify(s));
    setSesion(s);
    setVista("dashboard");
  }

  function salir() {
    cerrarSesion();
    localStorage.removeItem("sesion");
    setSesion(null);
  }

  if (!sesion) return <Login onEntrar={entrar} />;

  const items = NAV[sesion.rol];
  const actual = items.find((i) => i.clave === vista) ?? items[0];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="marca">
          <img
            className="logo-marca"
            src="/logo_taskflow.svg"
            alt=""
            style={{ width: 28, height: 28, borderRadius: 8, display: "block" }}
          />
          <span>TaskFlow AI</span>
        </div>
        <nav>
          {items.map((it) => (
            <button
              key={it.clave}
              className={it.clave === vista ? "activa" : ""}
              onClick={() => setVista(it.clave)}
            >
              {Iconos[it.icono]}
              <span>{it.etiqueta}</span>
              {it.clave === "bloqueos" && bloqueosAbiertos > 0 && (
                <span className="punto-nav" title={`${bloqueosAbiertos} sin resolver`} />
              )}
            </button>
          ))}
        </nav>
        <div className="perfil-sidebar">
          <Avatar nombre={sesion.nombre} id={sesion.id_usuario} />
          <div className="info-perfil">
            <span className="nombre">{sesion.nombre}</span>
            <span className="rol">{ROL_LEGIBLE[sesion.rol]}</span>
          </div>
          <button className="boton-salir-perfil" title="Salir" onClick={salir}>
            {Iconos.salir}
          </button>
        </div>
      </aside>

      <div className="contenido">
        <header className="topbar">
          <h2>{actual.etiqueta}</h2>
          {vista === "dashboard" && sprintActivo && (
            <span className="sprint-topbar">
              Sprint activo · <b>{sprintActivo}</b>
            </span>
          )}
        </header>

        <main>
          {vista === "dashboard" && <Dashboard rol={sesion.rol} onSprint={setSprintActivo} />}
          {vista === "backlog" && <Backlog rol={sesion.rol} />}
          {vista === "devs" && <Desarrolladores />}
          {vista === "sprints" && <Sprints />}
          {vista === "bloqueos" && <Bloqueos />}
          {vista === "seguimiento" && <Seguimiento rol={sesion.rol} />}
          {vista === "equipo" && <SeguimientoEquipo />}
        </main>
      </div>

      {sesion.rol === "DESARROLLADOR" && <ChatAvance />}
    </div>
  );
}
