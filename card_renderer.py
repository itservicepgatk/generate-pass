"""Рендер лицевой и оборотной сторон карточки"""

import io
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

    def front(
        self,
        photo_pil: Image.Image,
        logo_pil: Image.Image | None = None,
    ) -> Image.Image:
        img = Image.new("RGB", (self.w, self.h), "white")
        draw = ImageDraw.Draw(img)

        hh = self._front_header(img, draw)
        pr = self._front_photo(img, photo_pil, hh)
        if logo_pil:
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

    # ── Лицевая: части ────────────────────────────

    def _front_header(self, img, draw) -> int:
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
        pw = int(self.w * 0.32)
        ph = int(pw * 1.33)
        return DU.add_photo(img, photo_pil, 50, hh + 50, (pw, ph), "#FFFFFF", 10)

    def _front_logo(self, img, logo_pil, pr, hh):
        try:
            logo = logo_pil.convert("RGBA")
            r, g, b, a = logo.split()
            a = a.point(lambda p: int(p * 0.25))
            logo.putalpha(a)
            lh = int(self.h * 0.45)
            lw = int(logo.width * (lh / logo.height))
            logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)
            rs = pr + 30
            cx = rs + (self.w - 40 - rs) / 2
            img.paste(logo, (int(cx - lw / 2), hh + (self.h - hh - lh) // 2 + 20), logo)
        except Exception:
            pass

    def _front_info(self, draw, pr, hh):
        rs = pr + 40
        cx = rs + (self.w - 50 - rs) / 2
        y = hh + 40

        for ln in DU.wrap_text(self.cfg.org_name, self.fonts["org"], self.w - rs - 60):
            y = DU.text_centered(draw, ln, self.fonts["org"], cx, y, self.cfg.primary_color) + 5
        y += 40

        y = DU.text_centered(draw, "УДОСТОВЕРЕНИЕ", self.fonts["udost"], cx, y, self.cfg.accent_color)
        y += 30

        ser = "Серия _____ № ______"
        sb = draw.textbbox((0, 0), ser, font=self.fonts["value"])
        sw, sh = sb[2] - sb[0], sb[3] - sb[1]
        p = 15
        DU.rounded_rect(draw, (cx - sw/2 - p, y - 5, cx + sw/2 + p, y + sh + 10),
                         8, "#F8F9FA", self.cfg.border_color, 2)
        DU.text_centered(draw, ser, self.fonts["value"], cx, y, self.cfg.primary_color)

        by = self.h - 140
        DU.text_centered(draw, "Дата окончания действия удостоверения",
                         self.fonts["label"], cx, by, self.cfg.text_dark)
        by += 35
        dt = f"{self.cfg.date_end} г."
        db = draw.textbbox((0, 0), dt, font=self.fonts["value"])
        dw = db[2] - db[0]
        dx = cx - dw / 2
        draw.text((dx, by), dt, font=self.fonts["value"], fill=self.cfg.accent_color)
        draw.line([(dx, by + 40), (dx + dw, by + 40)], fill=self.cfg.accent_color, width=3)

    # ── Оборотная: части ──────────────────────────

    def _back_header(self, draw) -> int:
        y = 40
        for ln in DU.wrap_text(self.cfg.org_name, self.fonts["org"], self.w - 100):
            bb = draw.textbbox((0, 0), ln, font=self.fonts["org"])
            draw.text(((self.w - bb[2] + bb[0]) / 2, y), ln,
                      font=self.fonts["org"], fill=self.cfg.primary_color)
            y += bb[3] - bb[1] + 5
        return y + 40

    def _back_fio(self, draw, sur, name, pat, y) -> int:
        xm, lw = 60, 250
        for label, val in [("Фамилия", sur), ("Собственное имя", name), ("Отчество", pat)]:
            draw.text((xm, y), label, font=self.fonts["label"], fill=self.cfg.text_dark)
            lx = xm + lw
            draw.line([(lx, y + 38), (self.w - xm, y + 38)], fill=self.cfg.primary_color, width=2)
            if val:
                draw.text((lx + 10, y + 2), val, font=self.fonts["value"], fill=self.cfg.accent_color)
            y += 65
        return y + 15

    def _back_date(self, draw, y) -> int:
        xm, lw = 60, 250
        draw.text((xm, y), "Дата оформления", font=self.fonts["label"], fill=self.cfg.text_dark)
        dt = f"{self.cfg.date_start} г."
        lx = xm + lw
        draw.text((lx + 10, y + 2), dt, font=self.fonts["value"], fill=self.cfg.accent_color)
        db = draw.textbbox((0, 0), dt, font=self.fonts["value"])
        draw.line([(lx, y + 38), (lx + db[2] - db[0] + 20, y + 38)],
                  fill=self.cfg.primary_color, width=2)
        return y + 95

    def _back_perm(self, draw, y) -> int:
        txt = "Разрешено хранение и ношение специальных средств"
        bb = draw.textbbox((0, 0), txt, font=self.fonts["label"])
        tw = bb[2] - bb[0]
        DU.rounded_rect(draw, (50, y - 10, self.w - 50, y + 40),
                         10, "#FEF5E7", self.cfg.accent_color, 2)
        draw.text(((self.w - tw) / 2, y), txt, font=self.fonts["label"], fill=self.cfg.text_dark)
        return y + 75

    def _back_sign(self, draw, y):
        xm = 60
        draw.text((xm, y), "Подпись руководителя", font=self.fonts["label"], fill=self.cfg.text_dark)
        draw.line([(xm + 285, y + 38), (self.w - xm, y + 38)], fill=self.cfg.primary_color, width=2)