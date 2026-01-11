import uvicorn

from wire.router import app
from wire.wire_config import load_wire_cfg

wire_cfg = load_wire_cfg()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=wire_cfg.port, log_level=wire_cfg.log_level.lower())
