"""Registra cada invocación a Gemini como un evento en `logs_auditoria`, con el modelo"""
from app.repositorios import auditoria_repo


async def registrar_consulta_ia(
    *,
    tipo: str,
    prompt: str,
    respuesta: str | None,
    modelo: str,
    tokens_entrada: int,
    tokens_salida: int,
    tokens_json_equivalente: int | None = None,
    id_usuario: int | None = None,
    id_tarea: int | None = None,
    exito: bool = True,
    error: str | None = None,
) -> None:
    ahorro = (
        tokens_json_equivalente - tokens_entrada
        if tokens_json_equivalente is not None
        else None
    )
    await auditoria_repo.registrar_evento(
        tipo_evento=f"consulta_ia:{tipo}",
        contexto={
            "modelo": modelo,
            "prompt": prompt,
            "respuesta": respuesta,
            "tokens_entrada": tokens_entrada,
            "tokens_salida": tokens_salida,
            "tokens_json_equivalente": tokens_json_equivalente,
            "ahorro_tokens": ahorro,
            "exito": exito,
            "error": error,
        },
        id_usuario_postgres=id_usuario,
        id_tarea_postgres=id_tarea,
    )
