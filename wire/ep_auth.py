import logging
import time
from base64 import standard_b64decode

from cachetools import TTLCache, cached
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_der_public_key
from pydantic import BaseModel

from wire.cache_dict import CacheDict
from wire.http_pool import HttpPool
from wire.wire_config import WireConfig

ttl_cache = TTLCache(maxsize=1024, ttl=10)


class Keys:
    key_ring: list[Ed25519PublicKey] = []

    @classmethod
    def init(cls, wire_cfg: WireConfig):
        if cls.key_ring:
            return

        rsrp = HttpPool.pool.request("GET", f"{wire_cfg.bulb_base_url}/.well-known/keys.json")
        if rsrp.status != 200:
            raise Exception()

        keys = rsrp.json()
        for key in keys:
            cls.key_ring.append(load_der_public_key(standard_b64decode(key)))  # type: ignore


class HyTokenPayload(BaseModel):
    id: str
    rx: int
    exp: int
    tts: float


class AuthRes(BaseModel):
    ok: bool
    id: str


@cached(cache=ttl_cache)
def verify_hy_token(*, addr: str, auth: str, tx: int):
    msg, sig = auth.split(":")
    msg_raw = standard_b64decode(msg)
    sig_raw = standard_b64decode(sig)

    public_key = Keys.key_ring[0]
    try:
        public_key.verify(sig_raw, msg_raw)
    except InvalidSignature:
        logging.info(f"[{addr}] - invalid signature")
        return AuthRes(ok=False, id="invalid sig")

    payload = HyTokenPayload.model_validate_json(msg_raw)
    if time.time() > payload.exp:
        logging.info(f"exp: {payload.id} ({payload.exp})")
        return AuthRes(ok=False, id=payload.id)

    if tx > payload.rx:
        logging.info(f"rx: {payload.id} ({payload.rx})")
        return AuthRes(ok=False, id=payload.id)

    id = payload.id
    try:
        recorded_tts = CacheDict.db[id]
    except KeyError:
        recorded_tts = 0

    if recorded_tts < payload.tts:
        CacheDict.db[id] = payload.tts

    elif payload.tts < recorded_tts:
        logging.info(f"tts: {payload.id} ({payload.tts})")
        return AuthRes(ok=False, id=payload.id)

    return AuthRes(ok=True, id=id)
