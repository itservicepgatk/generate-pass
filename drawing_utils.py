"""Утилиты рисования — ИСПРАВЛЕНЫ"""

import os
from typing import Tuple, Dict
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import PassConfig
from photo_utils import PhotoUtils


class DrawingUtils:

    # ── Шрифты ─────────────────────────────────────

    @staticmethod
    def get_fonts(cfg: PassConfig) -> Dict[str, ImageFont.FreeTypeFont]:
        """Загрузка шрифтов — несколько уровней fallback"""
        bold = DrawingUtils._find_font(cfg, [
            "DejaVuSans-Bold.ttf", "arialbd.ttf", "LiberationSans-Bold.ttf"
        ])
        regular = DrawingUtils._find_font(cfg, [
            "DejaVuSans.ttf", "arial.ttf", "LiberationSans-Regular.ttf"
        ])
        serif = DrawingUtils._find_font(cfg, [
            "DejaVuSerif.ttf", "times.ttf", "LiberationSerif-Regular.ttf"
        ])

        return {
            "header": DrawingUtils._load_font(bold, 70),
            "org":    DrawingUtils._load_font(bold, 36),
            "label":  DrawingUtils._load_font(regular, 28),
            "value":  DrawingUtils._load_font(serif, 36),
            "udost":  DrawingUtils._load_font(bold, 56),
            "small":  DrawingUtils._load_font(regular, 24),
            "tiny":   DrawingUtils._load_font(regular, 20),
        }

    @staticmethod
    def _find_font(cfg: PassConfig, candidates: list) -> str:
        """Ищет первый доступный шрифт"""
        for name in candidates:
            # В папке fonts/
            path = cfg.font_path(name)
            if os.path.exists(path):
                return path
            # Системный
            try:
                ImageFont.truetype(name, 12)
                return name
            except Exception:
                continue
        return candidates[0]

    @staticmethod
    def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
        """Загружает шрифт с fallback"""
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            try:
                # Пробуем только имя файла (системный шрифт)
                return ImageFont.truetype(os.path.basename(path), size)
            except Exception:
                return ImageFont.load_default()

    # ── Градиент ───────────────────────────────────

    @staticmethod
    def create_gradient(w: int, h: int, c1: str, c2: str) -> Image.Image:
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)
        r1, g1, b1 = DrawingUtils.hex2rgb(c1)
        r2, g2, b2 = DrawingUtils.hex2rgb(c2)
        for y in range(h):
            t = y / max(h, 1)
            draw.line([(0, y), (w, y)], fill=(
                int(r1 + (r2 - r1) * t),
                int(g1 + (g2 - g1) * t),
                int(b1 + (b2 - b1) * t),
            ))
        return img

    # ── Скруглённый прямоугольник ──────────────────

    @staticmethod
    def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
        x1, y1, x2, y2 = xy
        d = radius * 2
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
        for cx, cy in [(x1, y1), (x2 - d, y1), (x1, y2 - d), (x2 - d, y2 - d)]:
            draw.ellipse([cx, cy, cx + d, cy + d], fill=fill)
        if outline:
            draw.arc([x1, y1, x1 + d, y1 + d], 180, 270, fill=outline, width=width)
            draw.arc([x2 - d, y1, x2, y1 + d], 270, 360, fill=outline, width=width)
            draw.arc([x1, y2 - d, x1 + d, y2], 90, 180, fill=outline, width=width)
            draw.arc([x2 - d, y2 - d, x2, y2], 0, 90, fill=outline, width=width)
            draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
            draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
            draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
            draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)

    # ── Текст ──────────────────────────────────────

    @staticmethod
    def text_centered(draw, text, font, cx, y, fill="black") -> int:
        bb = draw.textbbox((0, 0), text, font=font)
        w, h = bb[2] - bb[0], bb[3] - bb[1]
        draw.text((cx - w / 2, y), text, font=font, fill=fill)
        return y + h

    @staticmethod
    def text_shadow(draw, text, font, x, y, fill="white", shadow="black", off=2):
        draw.text((x + off, y + off), text, font=font, fill=shadow)
        draw.text((x, y), text, font=font, fill=fill)

    # ── Фото с рамкой ─────────────────────────────

    @staticmethod
    def add_photo(img, photo_pil, x, y, size, border_color="#FFFFFF", border_w=8) -> int:
        """Вставляет фото, возвращает ПРАВУЮ границу"""
        try:
            tw, th = size
            ratio = min(tw / photo_pil.width, th / photo_pil.height)
            nw, nh = int(photo_pil.width * ratio), int(photo_pil.height * ratio)
            resized = photo_pil.resize((nw, nh), Image.Resampling.LANCZOS)

            canvas = Image.new("RGB", size, "white")
            canvas.paste(resized, ((tw - nw) // 2, (th - nh) // 2))

            bw = border_w
            bordered = Image.new("RGB", (tw + bw * 2, th + bw * 2), border_color)
            bordered.paste(canvas, (bw, bw))

            # Тень
            shadow = Image.new("RGBA", bordered.size, (0, 0, 0, 0))
            ImageDraw.Draw(shadow).rectangle(
                [0, 0, bordered.width, bordered.height], fill=(0, 0, 0, 30)
            )
            shadow = shadow.filter(ImageFilter.GaussianBlur(8))
            img.paste(shadow, (x - 4, y + 4), shadow)
            img.paste(bordered, (x, y))

            return x + bordered.width
        except Exception as e:
            print(f"  ⚠️ Ошибка фото: {e}")
            return x

    # ── Перенос текста ─────────────────────────────

    @staticmethod
    def wrap_text(text, font, max_w):
        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
        words = text.split()
        lines, cur = [], []
        for w in words:
            test = " ".join(cur + [w])
            if draw.textbbox((0, 0), test, font=font)[2] <= max_w:
                cur.append(w)
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
        if cur:
            lines.append(" ".join(cur))
        return lines or [text]

    # ── Рамка карточки ─────────────────────────────

    @staticmethod
    def card_border(draw, w, h, color, width=4):
        draw.line([(0, 0), (w, 0)], fill=color, width=width)
        draw.line([(0, h - 1), (w, h - 1)], fill=color, width=width)
        draw.line([(0, 0), (0, h)], fill=color, width=width)
        draw.line([(w - 1, 0), (w - 1, h)], fill=color, width=width)

    @staticmethod
    def hex2rgb(c: str) -> Tuple[int, int, int]:
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))