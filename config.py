"""Конфигурация — значения по умолчанию + путь к шрифтам"""

import os
from typing import Tuple
from dataclasses import dataclass, field


@dataclass
class PassConfig:
    """Настройки пропуска (редактируемые через UI)"""

    # Размеры (см)
    card_w: float = 9.5
    card_h: float = 6.5
    dpi: int = 300

    # Тексты
    date_start: str = "05.01.2026"
    date_end: str = "05.01.2031"
    org_name: str = 'УО «ПГАТК имени А.Е.Клещёва»'
    header_text: str = "РАБОТНИК ОХРАНЫ"

    # Цвета
    primary_color: str = "#2C3E50"
    accent_color: str = "#E74C3C"
    gradient_start: str = "#3498DB"
    gradient_end: str = "#2C3E50"
    text_dark: str = "#2C3E50"
    text_light: str = "#FFFFFF"
    border_color: str = "#BDC3C7"

    # Пути шрифтов
    font_dir: str = "fonts"

    def get_px(self) -> Tuple[int, int]:
        w = int(self.card_w / 2.54 * self.dpi)
        h = int(self.card_h / 2.54 * self.dpi)
        return w, h

    def font_path(self, name: str) -> str:
        return os.path.join(self.font_dir, name)