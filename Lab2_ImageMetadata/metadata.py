from dataclasses import dataclass

@dataclass(slots=True)
class ImageMetadata:
    path: str = ""
    file_name: str = ""
    format: str = "Неизвестно"
    size: str = "—"
    dpi: str = "Не задано"
    depth: str = "—"
    compression: str = "—"
    status: str = "—"
    details: str = ""
    ok: bool = False
