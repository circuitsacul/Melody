from __future__ import annotations

import inspect
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, List, cast


@dataclass
class Config:
    token: str = "DISCORD TOKEN"
    owners: List[str] = field(default_factory=list)

    def save(self) -> None:
        pth = Path("config.json")

        dct = asdict(self)
        tosave: dict[str, Any] = {}
        defaults = self.__class__()
        for k, v in dct.items():
            if getattr(defaults, k) == v:
                continue

            tosave[k] = v

        with pth.open("w+") as f:
            f.write(json.dumps(tosave, indent=4))

    @classmethod
    def load(cls) -> "Config":
        pth = Path("config.json")

        if not pth.exists():
            c = Config()
        else:
            keys = set(inspect.signature(Config).parameters)
            with pth.open("r") as f:
                c = Config(
                    **{
                        k: v
                        for k, v in cast(dict, json.loads(f.read())).items()
                        if k in keys
                    }
                )

        c.save()
        return c


CONFIG = Config.load()
