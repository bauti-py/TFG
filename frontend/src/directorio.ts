import { api } from "./api";

let cache: Promise<Record<number, string>> | null = null;

export function cargarDirectorio(): Promise<Record<number, string>> {
  if (!cache) {
    cache = api
      .get<Record<string, string>>("/usuarios/directorio")
      .then((d) => {
        const mapa: Record<number, string> = {};
        for (const k in d) mapa[Number(k)] = d[k];
        return mapa;
      })
      .catch(() => {
        cache = null;
        return {};
      });
  }
  return cache;
}

export function nombreDe(mapa: Record<number, string>, id: number | null | undefined): string {
  if (id == null) return "—";
  return mapa[id] || "…";
}
