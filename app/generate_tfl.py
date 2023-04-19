import os

from config import NPS_DIR, SUCCESS_MESSAGE


def _normalize_path(path: str) -> str:
    """Normalize path"""
    return "../" + str(path).lstrip(".").lstrip("/").lstrip("\\")


def generate_tfl_file(path: str = NPS_DIR, message: str = SUCCESS_MESSAGE) -> dict:
    """Generate tfl file from NPSdir"""
    files_result: list[dict] = []
    dirs_result: set[str] = set()
    for _dirname, dirs, files in os.walk(path):
        dirname = os.path.relpath(_dirname, path)
        for d in dirs:
            dirs_result.add(os.path.join(dirname, d))
        for f in files:
            if f.endswith(".part"):
                continue
            files_result.append(
                {
                    "url": _normalize_path(os.path.join(dirname, f)),
                    "size": os.path.getsize(os.path.join(_dirname, f)),
                }
            )
    return {
        "files": files_result,
        "directories": sorted(dirs_result, reverse=True),
        "message": message,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(generate_tfl_file(), indent=4, ensure_ascii=False))
