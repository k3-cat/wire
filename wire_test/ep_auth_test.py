import time
import uuid
from base64 import standard_b64encode
from datetime import timedelta
from pathlib import Path

import pytest
import time_machine  # noqa: F401
from cryptography.hazmat.primitives.asymmetric import ed25519

from wire.cache_dict import CacheDict
from wire.ep_auth import AuthRes, HyTokenPayload, Keys, verify_hy_token


@pytest.fixture
def resource_setup_and_teardown():
    cache_dict_path = Path("./test.pickle")
    CacheDict.init(cache_dict_path)

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    Keys.key_ring.append(public_key)

    yield private_key

    CacheDict.close()
    cache_dict_path.unlink()


def test_verify_hy_token(resource_setup_and_teardown, time_machine):  # noqa: F811
    private_key = resource_setup_and_teardown
    id = str(uuid.uuid4())
    now = int(time.time())

    # - - -
    time_machine.move_to(now)
    msg1_raw = HyTokenPayload(id=id, rx=1000, exp=now + 10, tts=1).model_dump_json().encode("utf-8")
    sig1_raw = private_key.sign(msg1_raw)
    token1 = f"{standard_b64encode(msg1_raw).decode()}:{standard_b64encode(sig1_raw).decode()}"

    outcome = verify_hy_token(addr="fake.addr", auth=token1, tx=1000)
    assert outcome == AuthRes(ok=True, id=id)

    outcome = verify_hy_token(addr="fake.addr", auth=token1, tx=1001)
    assert outcome == AuthRes(ok=False, id=id)

    time_machine.shift(timedelta(seconds=11))
    outcome = verify_hy_token(addr="fake.addr.new1", auth=token1, tx=1000)
    assert outcome == AuthRes(ok=False, id=id)

    # - - -
    time_machine.move_to(now)
    msg2_raw = HyTokenPayload(id=id, rx=1000, exp=now + 10, tts=2).model_dump_json().encode("utf-8")
    sig2_raw = private_key.sign(msg2_raw)
    token2 = f"{standard_b64encode(msg2_raw).decode()}:{standard_b64encode(sig2_raw).decode()}"

    outcome = verify_hy_token(addr="fake.addr", auth=token2, tx=1000)
    assert outcome == AuthRes(ok=True, id=id)

    outcome = verify_hy_token(addr="fake.addr.new2", auth=token1, tx=1000)
    assert outcome == AuthRes(ok=False, id=id)
