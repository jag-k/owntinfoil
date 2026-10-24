import os
from pathlib import Path
from urllib.parse import quote

from app.config import settings


def _normalize_path(path: Path | str) -> str:
    """Normalize path"""
    return "../" + quote(Path(path).as_posix(), safe="/")


def generate_tfl_file(path: Path | str | None = None, message: str | None = None) -> dict:
    """Generate tfl file from NPSdir"""
    path = Path(path) if path is not None else settings.nps_dir
    message = message if message is not None else settings.success_message
    files_result: list[dict] = []
    dirs_result: set[str] = set()
    for directory, dirs, files in os.walk(path):
        directory_path = Path(directory)
        dirname = directory_path.relative_to(path)
        for d in dirs:
            dirs_result.add(str(dirname / d))
        for f in files:
            if f.endswith(".part"):
                continue
            files_result.append(
                {
                    "url": _normalize_path(dirname / f),
                    "size": (directory_path / f).stat().st_size,
                },
            )
    return {
        "files": files_result,
        "directories": sorted(dirs_result, reverse=True),
        "message": message,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(generate_tfl_file(), indent=4, ensure_ascii=False))
