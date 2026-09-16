import json
from functools import lru_cache
from typing import Any

from app.core.config import settings


@lru_cache
def _external_secret_bundle() -> dict[str, Any]:
    provider = settings.secret_provider.lower().strip()
    if provider == "env":
        return {}
    if provider != "aws":
        raise RuntimeError(f"Unsupported SECRET_PROVIDER: {settings.secret_provider}")
    if not settings.aws_secret_name:
        raise RuntimeError("AWS_SECRET_NAME is required when SECRET_PROVIDER=aws")

    import boto3

    client = boto3.client("secretsmanager", region_name=settings.aws_region)
    response = client.get_secret_value(SecretId=settings.aws_secret_name)
    raw = response.get("SecretString")
    if not raw:
        raise RuntimeError("AWS Secrets Manager secret does not contain SecretString")
    bundle = json.loads(raw)
    if not isinstance(bundle, dict):
        raise RuntimeError("Secret bundle must be a JSON object")
    return bundle


def get_jwt_key_ring() -> dict[str, str]:
    bundle = _external_secret_bundle()
    raw_keys = bundle.get("jwt_keys")
    if raw_keys is None:
        raw_keys = json.loads(settings.jwt_keys_json)
    if not isinstance(raw_keys, dict) or not raw_keys:
        raise RuntimeError("JWT key ring must contain at least one key")
    key_ring = {str(k): str(v) for k, v in raw_keys.items() if str(v)}
    if not key_ring:
        raise RuntimeError("JWT key ring contains no usable keys")
    return key_ring


def get_active_jwt_kid() -> str:
    bundle = _external_secret_bundle()
    active_kid = str(bundle.get("jwt_active_kid") or settings.jwt_active_kid)
    if active_kid not in get_jwt_key_ring():
        raise RuntimeError("JWT active kid is not present in the key ring")
    return active_kid


def get_data_encryption_material() -> str:
    bundle = _external_secret_bundle()
    value = bundle.get("data_encryption_key") or settings.data_encryption_key
    return str(value or settings.app_secret_key)


def jwt_key_status() -> dict[str, object]:
    ring = get_jwt_key_ring()
    return {
        "active_kid": get_active_jwt_kid(),
        "accepted_kids": sorted(ring.keys()),
        "provider": settings.secret_provider,
    }
