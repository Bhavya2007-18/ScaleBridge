import os
import shutil
from typing import BinaryIO

class LocalStorageService:
    """Manages file storage for uploaded raw datasets and generated reports."""

    def __init__(self, base_dir: str = "storage"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_file(self, filename: str, content_stream: BinaryIO) -> str:
        filepath = os.path.join(self.base_dir, filename)
        with open(filepath, "wb") as f:
            shutil.copyfileobj(content_stream, f)
        return filepath

    def get_file_path(self, filename: str) -> str:
        return os.path.join(self.base_dir, filename)

    def exists(self, filename: str) -> bool:
        return os.path.exists(self.get_file_path(filename))
