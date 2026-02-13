"""Конфигурация генератора пропусков"""

import os
from typing import Tuple
from dataclasses import dataclass


@dataclass
class PassConfig:
    """Настройки пропуска (редактируемые через UI)"""

    # Размеры (см)
    card_w: float = 9.5
    card_h: float = 6.5
    dpi: int = 300

    # ══ ОТСТУП для резки (см) ══
    # Расстояние между карточками в документе
    cut_margin: float = 0.2  # 2мм с каждой стороны

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

    # Пути
    font_dir: str = "fonts"
    assets_dir: str = "assets"
    default_logo: str = "logo_pgatkk.png"

    def get_px(self) -> Tuple[int, int]:
        w = int(self.card_w / 2.54 * self.dpi)
        h = int(self.card_h / 2.54 * self.dpi)
        return w, h

    def font_path(self, name: str) -> str:
        return os.path.join(self.font_dir, name)

    def default_logo_path(self) -> str:
        """Полный путь к логотипу по умолчанию"""
        return os.path.join(self.assets_dir, self.default_logo)

    def has_default_logo(self) -> bool:
        """Есть ли логотип по умолчанию"""
        return os.path.exists(self.default_logo_path())