"""Perfil de conocimiento (CU8, RF2/RF23)."""
from app.repositorios import perfil_repo

_LENGUAJES_CONOCIDOS = {
    "python", "javascript", "typescript", "java", "c#", "c++", "go", "rust",
    "php", "ruby", "kotlin", "swift", "sql", "html", "css",
}


def _clasificar(habilidades: list[str]) -> tuple[list[str], list[str]]:
    lenguajes, dominios = [], []
    for habilidad in habilidades:
        destino = lenguajes if habilidad.strip().lower() in _LENGUAJES_CONOCIDOS else dominios
        destino.append(habilidad)
    return lenguajes, dominios


async def actualizar_por_tarea_completada(id_usuario: int, habilidades: list[str]) -> None:
    lenguajes, dominios = _clasificar(habilidades)
    await perfil_repo.incorporar_aprendizaje(id_usuario, lenguajes, dominios)
