const BASE = "/api";

export function obtenerToken(): string | null {
  return localStorage.getItem("token");
}

export function guardarSesion(token: string) {
  localStorage.setItem("token", token);
}

export function cerrarSesion() {
  localStorage.removeItem("token");
}

async function pedir<T>(metodo: string, ruta: string, cuerpo?: unknown): Promise<T> {
  const cabeceras: Record<string, string> = { "Content-Type": "application/json" };
  const token = obtenerToken();
  if (token) cabeceras.Authorization = `Bearer ${token}`;

  const resp = await fetch(BASE + ruta, {
    method: metodo,
    headers: cabeceras,
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  });

  if (resp.status === 204) return undefined as T;
  const datos = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error((datos as { detail?: string }).detail || `Error ${resp.status}`);
  }
  return datos as T;
}

export const api = {
  get: <T>(ruta: string) => pedir<T>("GET", ruta),
  post: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("POST", ruta, cuerpo),
  put: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("PUT", ruta, cuerpo),
  patch: <T>(ruta: string, cuerpo?: unknown) => pedir<T>("PATCH", ruta, cuerpo),
  del: <T>(ruta: string) => pedir<T>("DELETE", ruta),
};
