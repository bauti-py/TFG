from typing import Any


def _es_lista_tabular(valor: Any) -> bool:
    if not isinstance(valor, list) or not valor:
        return False
    if not all(isinstance(x, dict) for x in valor):
        return False
    claves = list(valor[0].keys())
    for x in valor:
        if list(x.keys()) != claves:
            return False
        if any(isinstance(v, (dict, list)) for v in x.values()):
            return False
    return True


def _formatear(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float)):
        return str(valor)
    texto = str(valor)
    if any(c in texto for c in (",", ":", "\n", '"')):
        return '"' + texto.replace('"', '\\"') + '"'
    return texto


def _codificar(valor: Any, nivel: int, clave: str | None) -> list[str]:
    sangria = "  " * nivel
    lineas: list[str] = []

    if isinstance(valor, dict):
        if clave is not None:
            lineas.append(f"{sangria}{clave}:")
        for k, v in valor.items():
            if isinstance(v, (dict, list)):
                lineas.extend(_codificar(v, nivel + 1, k))
            else:
                lineas.append(f"{'  ' * (nivel + 1)}{k}: {_formatear(v)}")
        return lineas

    if isinstance(valor, list):
        if _es_lista_tabular(valor):
            claves = list(valor[0].keys())
            lineas.append(f"{sangria}{clave}[{len(valor)}]{{{','.join(claves)}}}:")
            for x in valor:
                lineas.append(f"{'  ' * (nivel + 1)}{','.join(_formatear(x[c]) for c in claves)}")
        else:
            lineas.append(f"{sangria}{clave}[{len(valor)}]:")
            for x in valor:
                if isinstance(x, (dict, list)):
                    lineas.extend(_codificar(x, nivel + 1, "-"))
                else:
                    lineas.append(f"{'  ' * (nivel + 1)}{_formatear(x)}")
        return lineas

    lineas.append(f"{sangria}{_formatear(valor)}")
    return lineas


def codificar(data: Any) -> str:
    if isinstance(data, dict):
        lineas: list[str] = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lineas.extend(_codificar(v, 0, k))
            else:
                lineas.append(f"{k}: {_formatear(v)}")
        return "\n".join(lineas)
    return "\n".join(_codificar(data, 0, None))


def estimar_tokens(texto: str) -> int:
    return max(1, len(texto) // 4)
