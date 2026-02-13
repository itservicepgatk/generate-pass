"""Рендер карточек — ИСПРАВЛЕНЫ: размещение, шрифты, лого, поля"""

import os
from PIL import Image, ImageDraw
from config import PassConfig
from drawing_utils import DrawingUtils as DU


class CardRenderer:

    def __init__(self, cfg: PassConfig):
        self.cfg = cfg
        self.w, self.h = cfg.get_px()
        self.fonts = DU.get_fonts(cfg)

    # ═══════════════════════════════════════════════
    #  ЛИЦЕВАЯ СТОРОНА
    # ═══════════════════════════════════════════════

    def front(self, photo_pil: Image.Image, logo_pil=None) -> Image.Image:
        img = Image.new("RGB", (self.w, self.h), "white")
        draw = ImageDraw.Draw(img)

        hh = self._front_header(img, draw)
        pr = self._front_photo(img, photo_pil, hh)

        # ══ ФИКС: логотип рисуется ДО текста (как фон) ══
        if logo_pil is not None:
            self._front_logo(img, logo_pil, pr, hh)

        self._front_info(draw, pr, hh)
        DU.card_border(draw, self.w, self.h, self.cfg.primary_color)
        return img

    # ═══════════════════════════════════════════════
    #  ОБОРОТНАЯ СТОРОНА
    # ═══════════════════════════════════════════════

    def back(self, fio: str) -> Image.Image:
        img = Image.new("RGB", (self.w, self.h), "white")
        draw = ImageDraw.Draw(img)

        parts = fio.split()
        sur = parts[0] if parts else ""
        name = parts[1] if len(parts) > 1 else ""
        pat = " ".join(parts[2:]) if len(parts) > 2 else ""

        y = self._back_header(draw)
        y = self._back_fio(draw, sur, name, pat, y)
        y = self._back_date(draw, y)
        y = self._back_perm(draw, y)
        self._back_sign(draw, y)
        DU.card_border(draw, self.w, self.h, self.cfg.primary_color)
        return img

    # ──────────────────────────────────────────────
    #  ЛИЦЕВАЯ: элементы
    # ──────────────────────────────────────────────

    def _front_header(self, img, draw) -> int:
        """Градиентная шапка, возвращает высоту"""
        hh = int(self.h * 0.18)
        grad = DU.create_gradient(
            self.w, hh, self.cfg.gradient_start, self.cfg.gradient_end
        )
        img.paste(grad, (0, 0))

        bb = draw.textbbox((0, 0), self.cfg.header_text, font=self.fonts["header"])
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        DU.text_shadow(
            draw, self.cfg.header_text, self.fonts["header"],
            (self.w - tw) / 2, (hh - th) / 2,
            fill=self.cfg.text_light, off=3,
        )
        return hh

    def _front_photo(self, img, photo_pil, hh) -> int:
        """Фото с рамкой, возвращает правую границу"""
        pw = int(self.w * 0.32)
        ph = int(pw * 1.33)
        return DU.add_photo(img, photo_pil, 50, hh + 50, (pw, ph), "#FFFFFF", 10)

    def _front_logo(self, img, logo_pil, photo_right, header_h):
        """Полупрозрачный логотип-водяной знак справа от фото"""
        try:
            logo = logo_pil.copy().convert("RGBA")

            # Делаем полупрозрачным (30% видимость)
            r, g, b, a = logo.split()
            a = a.point(lambda p: int(p * 0.30))
            logo.putalpha(a)

            # Масштабируем
            lh = int(self.h * 0.45)
            lw = int(logo.width * (lh / logo.height))
            logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)

            # Центрируем в правой части карточки
            right_start = photo_right + 30
            right_end = self.w - 40
            center_x = right_start + (right_end - right_start) // 2

            logo_x = int(center_x - lw / 2)
            logo_y = header_h + (self.h - header_h - lh) // 2 + 20

            # Убеждаемся что координаты в пределах карточки
            logo_x = max(0, min(logo_x, self.w - lw))
            logo_y = max(0, min(logo_y, self.h - lh))

            img.paste(logo, (logo_x, logo_y), logo)
            print(f"  ✓ Логотип добавлен: ({logo_x}, {logo_y}), размер {lw}x{lh}")

        except Exception as e:
            # ══ ФИКС: НЕ глушим ошибку ══
            print(f"  ⚠️ Ошибка логотипа: {e}")

    def _front_info(self, draw, photo_right, header_h):
        """Информационный блок справа от фото"""
        right_start = photo_right + 40
        right_end = self.w - 50
        cx = right_start + (right_end - right_start) / 2
        available_w = right_end - right_start

        y = header_h + 30

        # ══ ФИКС: название организации — шрифт подбирается под доступную ширину ══
        org_font = self._fit_font_for_text(
            draw, self.cfg.org_name, available_w,
            self.fonts["org"], min_size=22
        )

        lines = DU.wrap_text(self.cfg.org_name, org_font, available_w)
        for ln in lines:
            y = DU.text_centered(draw, ln, org_font, cx, y, self.cfg.primary_color) + 3

        y += 25

        # УДОСТОВЕРЕНИЕ — тоже подгоняем размер
        udost_font = self._fit_font_for_text(
            draw, "УДОСТОВЕРЕНИЕ", available_w,
            self.fonts["udost"], min_size=32
        )
        y = DU.text_centered(
            draw, "УДОСТОВЕРЕНИЕ", udost_font, cx, y, self.cfg.accent_color
        )
        y += 20

        # Серия / номер
        series = "Серия _____ № ______"
        sb = draw.textbbox((0, 0), series, font=self.fonts["value"])
        sw, sh = sb[2] - sb[0], sb[3] - sb[1]

        # Если не влезает — уменьшаем шрифт
        val_font = self._fit_font_for_text(
            draw, series, available_w - 30,
            self.fonts["value"], min_size=24
        )
        sb = draw.textbbox((0, 0), series, font=val_font)
        sw, sh = sb[2] - sb[0], sb[3] - sb[1]

        pad = 12
        DU.rounded_rect(
            draw,
            (cx - sw / 2 - pad, y - 5, cx + sw / 2 + pad, y + sh + 10),
            8, "#F8F9FA", self.cfg.border_color, 2,
        )
        DU.text_centered(draw, series, val_font, cx, y, self.cfg.primary_color)

        # Дата внизу — фиксированная позиция от низа
        by = self.h - 110
        label_font = self.fonts["label"]
        date_label = "Дата окончания действия удостоверения"

        # ══ ФИКС: подгоняем шрифт метки под ширину ══
        label_font = self._fit_font_for_text(
            draw, date_label, available_w,
            self.fonts["label"], min_size=16
        )

        DU.text_centered(draw, date_label, label_font, cx, by, self.cfg.text_dark)
        by += 30

        dt = f"{self.cfg.date_end} г."
        db = draw.textbbox((0, 0), dt, font=val_font)
        dw = db[2] - db[0]
        dx = cx - dw / 2
        draw.text((dx, by), dt, font=val_font, fill=self.cfg.accent_color)
        draw.line([(dx, by + 35), (dx + dw, by + 35)], fill=self.cfg.accent_color, width=3)

    # ──────────────────────────────────────────────
    #  ОБОРОТНАЯ: элементы
    # ──────────────────────────────────────────────

    def _back_header(self, draw) -> int:
        """Заголовок с названием организации"""
        y = 30

        # ══ ФИКС: адаптивный шрифт для org name ══
        available = self.w - 80
        font = self._fit_font_for_text(
            draw, self.cfg.org_name, available,
            self.fonts["org"], min_size=22
        )

        lines = DU.wrap_text(self.cfg.org_name, font, available)
        for ln in lines:
            bb = draw.textbbox((0, 0), ln, font=font)
            tw = bb[2] - bb[0]
            th = bb[3] - bb[1]
            draw.text(((self.w - tw) / 2, y), ln, font=font, fill=self.cfg.primary_color)
            y += th + 5

        return y + 30

    def _back_fio(self, draw, sur, name, pat, y) -> int:
        """Поля ФИО с динамической шириной меток"""
        xm = 50  # левый отступ
        fields = [
            ("Фамилия", sur),
            ("Собственное имя", name),
            ("Отчество", pat),
        ]

        # ══ ФИКС: вычисляем РЕАЛЬНУЮ ширину самой длинной метки ══
        label_font = self.fonts["label"]
        value_font = self.fonts["value"]

        max_label_w = 0
        for label, _ in fields:
            bb = draw.textbbox((0, 0), label, font=label_font)
            lw = bb[2] - bb[0]
            max_label_w = max(max_label_w, lw)

        # Отступ после метки
        label_end = xm + max_label_w + 20

        for label, value in fields:
            # Метка слева
            draw.text((xm, y), label, font=label_font, fill=self.cfg.text_dark)

            # Линия для значения — начинается после самой длинной метки
            line_y = y + 38
            draw.line(
                [(label_end, line_y), (self.w - xm, line_y)],
                fill=self.cfg.primary_color, width=2,
            )

            # Значение НАД линией
            if value:
                # ══ ФИКС: проверяем что значение влезает ══
                avail = self.w - xm - label_end - 10
                vf = self._fit_font_for_text(draw, value, avail, value_font, 24)
                draw.text(
                    (label_end + 10, y + 2), value,
                    font=vf, fill=self.cfg.accent_color,
                )
            y += 60

        return y + 10

    def _back_date(self, draw, y) -> int:
        """Дата оформления"""
        xm = 50
        label_font = self.fonts["label"]
        value_font = self.fonts["value"]

        label = "Дата оформления"
        bb = draw.textbbox((0, 0), label, font=label_font)
        label_w = bb[2] - bb[0]
        label_end = xm + label_w + 20

        draw.text((xm, y), label, font=label_font, fill=self.cfg.text_dark)

        dt = f"{self.cfg.date_start} г."
        draw.text((label_end + 10, y + 2), dt, font=value_font, fill=self.cfg.accent_color)

        # Линия под датой
        db = draw.textbbox((0, 0), dt, font=value_font)
        dw = db[2] - db[0]
        draw.line(
            [(label_end, y + 38), (label_end + dw + 20, y + 38)],
            fill=self.cfg.primary_color, width=2,
        )
        return y + 80

    def _back_perm(self, draw, y) -> int:
        """Блок разрешения"""
        txt = "Разрешено хранение и ношение специальных средств"

        # ══ ФИКС: подгоняем шрифт под ширину ══
        avail = self.w - 120
        font = self._fit_font_for_text(draw, txt, avail, self.fonts["label"], 16)

        bb = draw.textbbox((0, 0), txt, font=font)
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]

        box_pad = 10
        DU.rounded_rect(
            draw,
            (50, y - box_pad, self.w - 50, y + th + box_pad),
            10, "#FEF5E7", self.cfg.accent_color, 2,
        )
        draw.text(((self.w - tw) / 2, y), txt, font=font, fill=self.cfg.text_dark)
        return y + th + box_pad + 35

    def _back_sign(self, draw, y):
        """Подпись руководителя"""
        xm = 50
        label = "Подпись руководителя"
        label_font = self.fonts["label"]

        bb = draw.textbbox((0, 0), label, font=label_font)
        label_w = bb[2] - bb[0]

        draw.text((xm, y), label, font=label_font, fill=self.cfg.text_dark)

        # ══ ФИКС: линия начинается сразу после текста метки ══
        sign_start = xm + label_w + 15
        draw.line(
            [(sign_start, y + 38), (self.w - xm, y + 38)],
            fill=self.cfg.primary_color, width=2,
        )

    # ──────────────────────────────────────────────
    #  УТИЛИТА: подбор размера шрифта
    # ──────────────────────────────────────────────

    @staticmethod
    def _fit_font_for_text(draw, text, max_width, base_font, min_size=16):
        """
        Уменьшает шрифт пока текст не влезет в max_width.
        Возвращает подходящий шрифт.
        """
        font = base_font

        # Проверяем влезает ли текст
        bb = draw.textbbox((0, 0), text, font=font)
        if bb[2] - bb[0] <= max_width:
            return font

        # Пробуем уменьшать размер
        try:
            font_path = font.path
        except AttributeError:
            return font  # дефолтный шрифт, нельзя изменить размер

        current_size = font.size
        while current_size > min_size:
            current_size -= 2
            try:
                test_font = DU._load_font(font_path, current_size)
                bb = draw.textbbox((0, 0), text, font=test_font)
                if bb[2] - bb[0] <= max_width:
                    return test_font
            except Exception:
                break

        # Вернуть минимальный размер
        try:
            return DU._load_font(font_path, min_size)
        except Exception:
            return font