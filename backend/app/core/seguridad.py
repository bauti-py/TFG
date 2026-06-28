"""Seguridad transversal: hash de contraseñas, política de robustez y JWT."""
import re
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import config

_contexto = CryptContext(schemes=["bcrypt"], deprecated="auto")

_REGEX_PASSWORD = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")


def hashear_password(password: str) -> str:
    return _contexto.hash(password)


def verificar_password(plano: str, hasheado: str) -> bool:
    return _contexto.verify(plano, hasheado)


def password_es_robusta(password: str) -> bool:
    """≥8 caracteres con mayúscula, minúscula, dígito y carácter especial (Seguridad)."""
    return bool(_REGEX_PASSWORD.match(password))


def crear_token(*, id_usuario: int, rol: str) -> str:
    """Emite un JWT firmado con el id del usuario y su rol embebido (para RBAC)."""
    expira = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(id_usuario), "rol": rol, "exp": expira}
    return jwt.encode(payload, config.JWT_SECRET, algorithm=config.JWT_ALGORITMO)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITMO])
    except JWTError:
        return None
