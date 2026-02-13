"""Сборка Word-документа (работает с байтами в памяти)"""

import io
from PIL import Image
from docx import Document
from docx.shared import Cm, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ROW_HEIGHT_RULE

from config import PassConfig
from card_renderer import CardRenderer
from photo_utils import PhotoUtils


class DocumentBuilder:

    CHUNK = 8

    def __init__(self, cfg: PassConfig):
        self.cfg = cfg
        self.renderer = CardRenderer(cfg)

    def build(
        self,
        photos: dict[str, bytes],
        logo_bytes: bytes | None = None,
        progress_cb=None,
    ) -> bytes:
        """
        photos:  {"Иванов Иван Иванович": b"...", ...}
        logo_bytes: байты логотипа или None
        Возвращает байты .docx
        """
        logo_pil = None
        if logo_bytes:
            logo_pil = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        doc = self._new_doc()
        names = list(photos.keys())
        chunks = [names[i:i + self.CHUNK] for i in range(0, len(names), self.CHUNK)]
        total = len(names)
        done = 0

        for ci, chunk in enumerate(chunks):
            # ── Лицевые ──
            if ci > 0:
                doc.add_page_break()
            tf = self._table(doc)

            for i, fio in enumerate(chunk):
                photo_pil = PhotoUtils.process_upload(photos[fio], fio)
                card = self.renderer.front(photo_pil, logo_pil)
                self._insert(tf, i // 2, i % 2, card)
                done += 1
                if progress_cb:
                    progress_cb(done / (total * 2))

            # ── Оборотные ──
            doc.add_page_break()
            tb = self._table(doc)

            for i, fio in enumerate(chunk):
                card = self.renderer.back(fio)
                self._insert(tb, i // 2, 1 - (i % 2), card)
                done += 1
                if progress_cb:
                    progress_cb(done / (total * 2))

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    # ── Внутренние ─────────────────────────────────

    def _new_doc(self):
        doc = Document()
        s = doc.sections[0]
        for attr in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(s, attr, Mm(10))
        s.page_width, s.page_height = Mm(210), Mm(297)
        return doc

    def _table(self, doc):
        t = doc.add_table(rows=4, cols=2)
        t.autofit = t.allow_autofit = False
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cw = Cm(self.cfg.card_w + 0.5)
        for c in t.columns:
            c.width = cw
        return t

    def _insert(self, table, row, col, card_img: Image.Image):
        buf = io.BytesIO()
        card_img.save(buf, format="PNG")
        buf.seek(0)

        cell = table.rows[row].cells[col]
        cell.width = Cm(self.cfg.card_w + 0.5)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(buf, width=Cm(self.cfg.card_w), height=Cm(self.cfg.card_h))
        table.rows[row].height_rule = WD_ROW_HEIGHT_RULE.EXACTLY
        table.rows[row].height = Cm(self.cfg.card_h + 0.2)