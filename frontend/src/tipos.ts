export type Rol = "LIDER_TECNICO" | "DESARROLLADOR" | "SCRUM_MASTER";
export type Prioridad = "BAJA" | "MEDIA" | "ALTA" | "CRITICA";
export type EstadoTarea =
  | "PENDIENTE"
  | "PENDIENTE_ASIGNACION"
  | "ASIGNADA"
  | "EN_PROGRESO"
  | "BLOQUEADA"
  | "COMPLETADA"
  | "ASIGNACION_FALLIDA";
export type EstadoSprint = "PLANIFICADO" | "ACTIVO" | "CERRADO";
export type EstadoBloqueo = "ABIERTO" | "RESUELTO" | "PERSISTENTE" | "ESCALADO_TL";

export interface RespuestaToken {
  access_token: string;
  token_type: string;
  rol: Rol;
  id_usuario: number;
  nombre: string;
}

export interface Sesion {
  token: string;
  rol: Rol;
  id_usuario: number;
  nombre: string;
}

export interface Usuario {
  id_usuario: number;
  nombre: string;
  email: string;
  rol: Rol;
  activo: boolean;
}

export interface PerfilSalida {
  id_usuario_postgres: number;
  lenguajes: string[];
  dominios: string[];
  frameworks: string[];
  seniority: string | null;
  historial_tareas: Record<string, unknown>;
  metricas_agregadas: Record<string, unknown>;
}

export interface Sprint {
  id_sprint: number;
  objetivo: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoSprint;
}

export interface Tarea {
  id_tarea: number;
  descripcion: string;
  prioridad: Prioridad;
  habilidades_requeridas: string[];
  estado: EstadoTarea;
  id_sprint: number;
  id_usuario_asignado: number | null;
  fecha_creacion: string;
  fecha_cierre: string | null;
}

export interface ResultadoAsignacion {
  id_tarea: number;
  id_usuario_asignado: number | null;
  estado: EstadoTarea;
  motivo: string | null;
  confianza: number | null;
}

export interface Bloqueo {
  id_bloqueo: number;
  id_tarea: number;
  descripcion_tarea: string | null;
  id_usuario_asignado: number | null;
  contexto: string;
  estado: EstadoBloqueo;
  resolucion: string | null;
  fecha_deteccion: string;
  fecha_resolucion: string | null;
}

export interface TareaElevada {
  id_tarea: number;
  descripcion: string | null;
  contexto: string;
}

export interface ResumenSeguimiento {
  id_tarea: number;
  resumen: string;
}

export interface Mensaje {
  autor: string;
  texto: string;
  fecha: string;
}

export interface ConsultaAvance {
  id_tarea: number;
  pregunta: string;
}

export interface ResultadoSeguimiento {
  id_tarea: number;
  estado_inferido: EstadoTarea;
  resumen: string;
  siguiente_pregunta: string;
  genero_bloqueo: boolean;
  diferido: boolean;
}

export interface TareaTablero {
  id_tarea: number;
  descripcion: string;
  prioridad: string;
  id_usuario_asignado: number | null;
  fecha_creacion?: string | null;
}

export interface Dashboard {
  rol?: Rol;
  sprint?: { id_sprint: number; objetivo: string; estado: string } | null;
  mensaje?: string;
  total_tareas?: number;
  completadas?: number;
  progreso?: number;
  columnas?: Record<string, TareaTablero[]>;
  tareas_activas_por_desarrollador?: Record<string, number>;
  bloqueos_pendientes?: { id_bloqueo: number; id_tarea: number; descripcion?: string | null; contexto: string }[];
}
