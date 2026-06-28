import { useState } from "react";
import { api } from "../api";
import type { RespuestaToken, Sesion } from "../tipos";

export default function Login({ onEntrar }: { onEntrar: (s: Sesion) => void }) {
  const [email, setEmail] = useState("lider@demo.com");
  const [password, setPassword] = useState("Lider123!");
  const [verPass, setVerPass] = useState(false);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCargando(true);
    try {
      const r = await api.post<RespuestaToken>("/auth/login", { email, password });
      onEntrar({ token: r.access_token, rol: r.rol, id_usuario: r.id_usuario, nombre: r.nombre });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="login">
      <form onSubmit={enviar} className="tarjeta-login">
        <img
          className="logo-login"
          src="/logo_taskflow.svg"
          alt="TaskFlow AI"
          style={{ width: 56, height: 56, borderRadius: 14, display: "block", margin: "0 auto" }}
        />
        <h1>TaskFlow AI</h1>
        <p className="tagline">Gestión inteligente para equipos</p>

        <h2>Iniciar sesión</h2>
        <p className="sub">Accede a tu espacio de trabajo</p>

        <label>
          Correo electrónico
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="nombre@empresa.com"
            required
          />
        </label>

        <label>
          Contraseña
          <div className="campo-pass">
            <input
              type={verPass ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
            <button type="button" className="ojo" onClick={() => setVerPass(!verPass)}>
              {verPass ? "Ocultar" : "Ver"}
            </button>
          </div>
        </label>

        {error && <p className="error">{error}</p>}

        <button type="submit" className="boton-primario ancho" disabled={cargando}>
          {cargando ? "Entrando…" : "Iniciar sesión"}
        </button>

        <p className="pie-login">TaskFlow AI · Plataforma de gestión inteligente para equipos</p>
      </form>
    </div>
  );
}
