import os
from abc import ABC, abstractmethod
from typing import Optional


class BaseStorageService(ABC):
    @abstractmethod
    async def save_file(self, file_content: bytes, destination_path: str) -> str:
        """Save file bytes to destination_path and return absolute or stored path."""
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> bytes:
        """Read and return file bytes."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete file if it exists."""
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = "storage/documents"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, file_content: bytes, destination_path: str) -> str:
        full_path = os.path.join(self.base_dir, destination_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "wb") as f:
            f.write(file_content)
        return full_path

    async def read_file(self, file_path: str) -> bytes:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_file(self, file_path: str) -> bool:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except OSError:
                return False
        return False

    async def file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)
