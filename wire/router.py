import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from pydantic import BaseModel

from wire.cache_dict import CacheDict
from wire.ep_auth import AuthRes, Keys, verify_hy_token
from wire.wire_config import load_wire_cfg

wire_cfg = load_wire_cfg()

sentry_sdk.init(
    dsn=wire_cfg.sentry_dsn,
    send_default_pii=True,
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profile_lifecycle="trace",
    enable_logs=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ------------------
    # --- Config Ext ---
    # ------------------

    # cache
    CacheDict.init("/ep-auth.pickle")

    # bulb
    Keys.init(wire_cfg)

    logging.basicConfig(level=wire_cfg.log_level.upper())

    # --------------------------
    # --- Config & Start App ---
    # --------------------------

    app.title = wire_cfg.app_name
    # app.include_router(load_routers())

    yield

    # ------------------
    # ---  Clean Up  ---
    # ------------------

    CacheDict.close()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"Hello": "World"}


class AuthReq(BaseModel):
    addr: str
    auth: str
    tx: int  # bytes per sec, from server's pov


@app.post("/auth/hy2")
def hy2_auth(req: AuthReq) -> AuthRes:
    return verify_hy_token(**req.model_dump())
