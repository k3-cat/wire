import pickle
from pathlib import Path


class CacheDict:
    path: Path
    db: dict[str, float] = None  # type: ignore

    @classmethod
    def init(cls, path: Path | str):
        if cls.db is not None:
            return

        if isinstance(path, str):
            path = Path(path)

        cls.path = path
        if not path.exists():
            path.write_bytes(pickle.dumps(dict()))

        with path.open("rb") as fp:
            cls.db = pickle.load(fp)

    @classmethod
    def close(cls):
        with cls.path.open("wb") as fp:
            pickle.dump(cls.db, fp, pickle.HIGHEST_PROTOCOL)
