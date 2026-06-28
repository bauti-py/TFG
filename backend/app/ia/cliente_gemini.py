import asyncio
import json
import re
import time
from app.core.config import config
from app.ia import registro_ia, toon

try:
    from google import genai
except Exception:
    genai = None

_cliente = None
if genai is not None and config.GEMINI_API_KEY:
    _cliente = genai.Client(api_key=config.GEMINI_API_KEY)

# modelo -> instante (monotonic) hasta el que queda "tmp_out". Estado por proceso.
_tmp_out_hasta: dict[str, float] = {}


def _modelos_disponibles() -> list[str]:
    ahora = time.monotonic()
    libres = [m for m in config.gemini_modelos if _tmp_out_hasta.get(m, 0.0) <= ahora]
    # Si están todos en cooldown, probamos por el que vence antes.
    return libres or sorted(config.gemini_modelos, key=lambda m: _tmp_out_hasta.get(m, 0.0))


def _marcar_tmp_out(modelo: str) -> None:
    _tmp_out_hasta[modelo] = time.monotonic() + config.GEMINI_TMP_OUT_MINUTOS * 60


async def _invocar(modelo: str, prompt: str) -> str:
    def _llamar() -> str:
        respuesta = _cliente.models.generate_content(model=modelo, contents=prompt)
        return respuesta.text or ""

    return await asyncio.wait_for(asyncio.to_thread(_llamar), timeout=config.LLM_TIMEOUT_SEGUNDOS)


async def generar(
    *,
    tipo: str,
    prompt: str,
    id_usuario: int | None = None,
    id_tarea: int | None = None,
    tokens_json_equivalente: int | None = None,
) -> str | None:
    """Genera texto rotando entre modelos. Devuelve None si la IA no está o fallan todos."""
    if not _cliente:
        return None

    ultimo_error: Exception | None = None
    modelo_usado: str | None = None
    for modelo in _modelos_disponibles():
        modelo_usado = modelo
        for intento in range(1, config.LLM_MAX_REINTENTOS + 1):
            try:
                texto = await _invocar(modelo, prompt)
                await registro_ia.registrar_consulta_ia(
                    tipo=tipo, prompt=prompt, respuesta=texto, modelo=modelo,
                    tokens_entrada=toon.estimar_tokens(prompt),
                    tokens_salida=toon.estimar_tokens(texto),
                    tokens_json_equivalente=tokens_json_equivalente,
                    id_usuario=id_usuario, id_tarea=id_tarea, exito=True,
                )
                return texto
            except Exception as exc:
                ultimo_error = exc
                es_cuota = "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc)
                if es_cuota:
                    _marcar_tmp_out(modelo)
                    break
                if intento < config.LLM_MAX_REINTENTOS:
                    await asyncio.sleep(0.5 * intento)
                else:
                    _marcar_tmp_out(modelo)

    await registro_ia.registrar_consulta_ia(
        tipo=tipo, prompt=prompt, respuesta=None, modelo=modelo_usado or "",
        tokens_entrada=toon.estimar_tokens(prompt), tokens_salida=0,
        tokens_json_equivalente=tokens_json_equivalente,
        id_usuario=id_usuario, id_tarea=id_tarea, exito=False, error=str(ultimo_error),
    )
    return None


async def generar_json(**kwargs) -> dict | None:
    texto = await generar(**kwargs)
    if texto is None:
        return None
    return _extraer_json(texto)


def _extraer_json(texto: str) -> dict | None:
    texto = texto.strip()
    coincidencia = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if coincidencia:
        texto = coincidencia.group(1)
    else:
        inicio, fin = texto.find("{"), texto.rfind("}")
        if inicio != -1 and fin != -1:
            texto = texto[inicio : fin + 1]
    try:
        return json.loads(texto)
    except (ValueError, TypeError):
        return None
