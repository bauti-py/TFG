"""Check de la rotación de modelos con cooldown (sin framework: corré `python` este archivo).

    docker compose exec -T api python - < backend/tests/test_rotacion_gemini.py
"""
from app.core.config import config
from app.ia import cliente_gemini as cg


def main() -> None:
    modelos = config.gemini_modelos
    assert modelos, "gemini_modelos no debería estar vacío"

    # Sin cooldown: están todos disponibles, en el orden configurado.
    cg._tmp_out_hasta.clear()
    assert cg._modelos_disponibles() == modelos

    if len(modelos) > 1:
        # Marco el primero como tmp_out: deja de ofrecerse, el resto sigue.
        cg._marcar_tmp_out(modelos[0])
        disponibles = cg._modelos_disponibles()
        assert modelos[0] not in disponibles, "el modelo en cooldown no debería ofrecerse"
        assert modelos[1] in disponibles

    # Con todos en cooldown igual devuelve alguno (mejor intentar que rendirse).
    for m in modelos:
        cg._marcar_tmp_out(m)
    assert cg._modelos_disponibles(), "si todos están out, igual debe proponer uno"

    cg._tmp_out_hasta.clear()
    print("OK rotacion gemini:", modelos)


if __name__ == "__main__":
    main()
