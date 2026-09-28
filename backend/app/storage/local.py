"""Private immutable object storage. Keys are server-generated, never filenames."""

import re
from pathlib import Path
from typing import Protocol
from uuid import UUID

from app.core.config import get_settings


class Storage(Protocol):
    def put(self, project_id: UUID, key: str, content: bytes) -> None: ...
    def read(self, project_id: UUID, key: str) -> bytes: ...
    def discard_uncommitted(self, project_id: UUID, key: str) -> None: ...


def storage_key(project_id: UUID, source_id: UUID, version_id: UUID) -> str:
    return f"{project_id}/{source_id}/{version_id}.bin"


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def path(self, project_id: UUID, key: str) -> Path:
        pattern = rf"{project_id}/[0-9a-f-]{{36}}/[0-9a-f-]{{36}}\.bin"
        if not re.fullmatch(pattern, key):
            raise ValueError("Invalid storage key")
        target = (self.root / key).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("Invalid storage key")
        return target

    def put(self, project_id: UUID, key: str, content: bytes):
        target = self.path(project_id, key)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation prevents accidental version overwrite/collision.
        with target.open("xb") as output:
            try:
                output.write(content)
            except OSError:
                output.close()
                target.unlink(missing_ok=True)
                raise

    def read(self, project_id: UUID, key: str) -> bytes:
        return self.path(project_id, key).read_bytes()

    def discard_uncommitted(self, project_id: UUID, key: str):
        self.path(project_id, key).unlink(missing_ok=True)


def get_storage() -> Storage:
    return LocalStorage(get_settings().storage_root)
