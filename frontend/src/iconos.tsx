const P = { width: 18, height: 18, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export const Iconos: Record<string, JSX.Element> = {
  dashboard: (
    <svg {...P}>
      <rect x="3" y="3" width="7" height="9" />
      <rect x="14" y="3" width="7" height="5" />
      <rect x="14" y="12" width="7" height="9" />
      <rect x="3" y="16" width="7" height="5" />
    </svg>
  ),
  backlog: (
    <svg {...P}>
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <circle cx="3.5" cy="6" r="1" />
      <circle cx="3.5" cy="12" r="1" />
      <circle cx="3.5" cy="18" r="1" />
    </svg>
  ),
  sprint: (
    <svg {...P}>
      <path d="M4 4v16" />
      <path d="M4 4h13l-2 4 2 4H4" />
    </svg>
  ),
  devs: (
    <svg {...P}>
      <circle cx="9" cy="7" r="3" />
      <path d="M3 21v-1a5 5 0 0 1 10 0v1" />
      <path d="M16 3.5a3 3 0 0 1 0 7" />
      <path d="M21 21v-1a5 5 0 0 0-3-4.5" />
    </svg>
  ),
  tareas: (
    <svg {...P}>
      <path d="M9 11l3 3L22 4" />
      <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
    </svg>
  ),
  bloqueos: (
    <svg {...P}>
      <path d="M10.3 3.6 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.6a2 2 0 0 0-3.4 0Z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12" y2="17" />
    </svg>
  ),
  perfil: (
    <svg {...P}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21v-1a8 8 0 0 1 16 0v1" />
    </svg>
  ),
  refrescar: (
    <svg {...P}>
      <path d="M21 12a9 9 0 1 1-2.64-6.36" />
      <path d="M21 3v5h-5" />
    </svg>
  ),
  robot: (
    <svg {...P}>
      <rect x="4" y="8" width="16" height="11" rx="2" />
      <path d="M12 8V4" />
      <circle cx="12" cy="3" r="1.2" />
      <circle cx="9" cy="13" r="1.1" />
      <circle cx="15" cy="13" r="1.1" />
      <path d="M2 12v3" />
      <path d="M22 12v3" />
    </svg>
  ),
  filtro: (
    <svg {...P}>
      <path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z" />
    </svg>
  ),
  ojo: (
    <svg {...P}>
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ),
  ojoCerrado: (
    <svg {...P}>
      <path d="M9.9 4.2A11 11 0 0 1 12 5c7 0 11 7 11 7a18 18 0 0 1-2.2 3M6.6 6.6A18 18 0 0 0 1 12s4 7 11 7a11 11 0 0 0 5.4-1.4" />
      <line x1="2" y1="2" x2="22" y2="22" />
    </svg>
  ),
  seguimiento: (
    <svg {...P}>
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      <line x1="8" y1="9" x2="16" y2="9" />
      <line x1="8" y1="13" x2="13" y2="13" />
    </svg>
  ),
  salir: (
    <svg {...P}>
      <path d="M6 3h9a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6z" />
      <circle cx="12.5" cy="12" r="1" />
    </svg>
  ),
};
