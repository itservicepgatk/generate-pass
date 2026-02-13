"""
🪪 Генератор пропусков — веб-интерфейс
Streamlit + логотип по умолчанию + отступы для резки
"""

import streamlit as st
from PIL import Image
import io
import os

from config import PassConfig
from card_renderer import CardRenderer
from document_builder import DocumentBuilder
from photo_utils import PhotoUtils


# ═══════════════════════════════════════════════════
#  НАСТРОЙКА СТРАНИЦЫ
# ═══════════════════════════════════════════════════

st.set_page_config(
    page_title="Генератор пропусков",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #7F8C8D;
        margin-bottom: 2rem;
    }
    .success-box {
        background: #D4EDDA;
        border: 1px solid #C3E6CB;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .logo-info {
        background: #E8F4FD;
        border: 1px solid #B8DAFF;
        border-radius: 8px;
        padding: 0.7rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
#  УТИЛИТА: загрузка логотипа
# ═══════════════════════════════════════════════════

def load_default_logo(cfg: PassConfig) -> bytes | None:
    """Загружает логотип по умолчанию если он есть"""
    if cfg.has_default_logo():
        try:
            with open(cfg.default_logo_path(), "rb") as f:
                return f.read()
        except Exception as e:
            st.sidebar.warning(f"Не удалось загрузить логотип: {e}")
    return None


# ═══════════════════════════════════════════════════
#  САЙДБАР — НАСТРОЙКИ
# ═══════════════════════════════════════════════════

def render_sidebar() -> PassConfig:
    """Рендерит сайдбар и возвращает конфиг"""
    cfg = PassConfig()

    st.sidebar.title("⚙️ Настройки")

    # Организация
    st.sidebar.subheader("📋 Организация")
    cfg.org_name = st.sidebar.text_input("Название", cfg.org_name)
    cfg.header_text = st.sidebar.text_input("Заголовок пропуска", cfg.header_text)

    # Даты
    st.sidebar.subheader("📅 Даты")
    col1, col2 = st.sidebar.columns(2)
    cfg.date_start = col1.text_input("Начало", cfg.date_start)
    cfg.date_end = col2.text_input("Конец", cfg.date_end)

    # Размеры
    st.sidebar.subheader("📐 Размеры")
    col1, col2 = st.sidebar.columns(2)
    cfg.card_w = col1.number_input("Ширина (см)", 5.0, 15.0, cfg.card_w, 0.5)
    cfg.card_h = col2.number_input("Высота (см)", 4.0, 12.0, cfg.card_h, 0.5)

    # ══ ОТСТУПЫ ДЛЯ РЕЗКИ ══
    st.sidebar.subheader("✂️ Отступы для резки")
    cfg.cut_margin = st.sidebar.slider(
        "Зазор между карточками (мм)",
        min_value=0.0,
        max_value=5.0,
        value=2.0,
        step=0.5,
        help="Расстояние между карточками в документе для удобной резки",
    ) / 10  # мм → см

    if cfg.cut_margin > 0:
        st.sidebar.caption(
            f"📏 Карточка: {cfg.card_w}×{cfg.card_h} см (точно)\n\n"
            f"📦 Ячейка: {cfg.card_w + cfg.cut_margin * 2:.1f}×"
            f"{cfg.card_h + cfg.cut_margin * 2:.1f} см (с зазором)"
        )
    else:
        st.sidebar.caption("⚠️ Без зазора — карточки будут впритык")

    # Цвета
    st.sidebar.subheader("🎨 Цвета")
    col1, col2 = st.sidebar.columns(2)
    cfg.primary_color = col1.color_picker("Основной", cfg.primary_color)
    cfg.accent_color = col2.color_picker("Акцент", cfg.accent_color)

    col1, col2 = st.sidebar.columns(2)
    cfg.gradient_start = col1.color_picker("Градиент начало", cfg.gradient_start)
    cfg.gradient_end = col2.color_picker("Градиент конец", cfg.gradient_end)

    return cfg


# ═══════════════════════════════════════════════════
#  ЗАГРУЗКА ФАЙЛОВ
# ═══════════════════════════════════════════════════

def render_upload(cfg: PassConfig) -> tuple:
    """Рендерит зону загрузки, возвращает (photos_dict, logo_bytes)"""

    st.markdown(
        '<p class="main-header">🪪 Генератор пропусков</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">'
        'Загрузите фото сотрудников → настройте → скачайте готовый документ'
        '</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("📸 Фотографии сотрудников")
        st.caption("Имя файла = ФИО (например: `Иванов Иван Иванович.jpg`)")
        uploaded_photos = st.file_uploader(
            "Выберите фото",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="photos",
        )

    with col2:
        st.subheader("🏛️ Логотип")

        # ══ ЛОГОТИП ПО УМОЛЧАНИЮ ══
        default_logo_bytes = load_default_logo(cfg)
        has_default = default_logo_bytes is not None

        if has_default:
            st.markdown(
                '<div class="logo-info">'
                f'✅ Логотип по умолчанию: <b>{cfg.default_logo}</b>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.caption("Загрузите свой чтобы заменить ↓")

        uploaded_logo = st.file_uploader(
            "Свой логотип (необязательно)" if has_default else "Логотип организации",
            type=["jpg", "jpeg", "png"],
            key="logo",
        )

    # Собираем фото
    photos = {}
    if uploaded_photos:
        for f in uploaded_photos:
            fio = f.name.rsplit(".", 1)[0]
            photos[fio] = f.read()
            f.seek(0)

    # ══ Определяем логотип: свой или по умолчанию ══
    logo_bytes = None
    if uploaded_logo:
        # Пользователь загрузил свой — используем его
        logo_bytes = uploaded_logo.read()
        uploaded_logo.seek(0)
        st.sidebar.success("🖼️ Используется загруженный логотип")
    elif default_logo_bytes:
        # Используем логотип по умолчанию
        logo_bytes = default_logo_bytes
        st.sidebar.info(f"🖼️ Используется {cfg.default_logo}")

    return photos, logo_bytes


# ═══════════════════════════════════════════════════
#  ПРЕВЬЮ КАРТОЧЕК
# ═══════════════════════════════════════════════════

def render_preview(cfg: PassConfig, photos: dict, logo_bytes: bytes | None):
    """Показывает превью карточек"""
    if not photos:
        st.info("👆 Загрузите фотографии сотрудников для начала работы")
        return

    st.divider()
    st.subheader(f"👁️ Превью ({len(photos)} сотрудников)")

    # Показываем инфо о размерах
    col1, col2, col3 = st.columns(3)
    col1.metric("📏 Размер карточки", f"{cfg.card_w} × {cfg.card_h} см")
    col2.metric("✂️ Зазор для резки", f"{cfg.cut_margin * 10:.1f} мм")
    col3.metric("🖼️ Логотип", "Есть ✅" if logo_bytes else "Нет ❌")

    renderer = CardRenderer(cfg)
    logo_pil = None
    if logo_bytes:
        logo_pil = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    preview_names = list(photos.keys())[:4]

    for fio in preview_names:
        photo_pil = PhotoUtils.process_upload(photos[fio], fio)

        col1, col2 = st.columns(2)

        with col1:
            st.caption(f"**{fio}** — лицевая сторона")
            front = renderer.front(photo_pil, logo_pil)
            st.image(front, use_container_width=True)

        with col2:
            st.caption(f"**{fio}** — оборотная сторона")
            back_img = renderer.back(fio)
            st.image(back_img, use_container_width=True)

        st.divider()

    if len(photos) > 4:
        st.info(f"Показаны первые 4 из {len(photos)}. Все будут в итоговом документе.")


# ═══════════════════════════════════════════════════
#  ГЕНЕРАЦИЯ И СКАЧИВАНИЕ
# ═══════════════════════════════════════════════════

def render_generate(cfg: PassConfig, photos: dict, logo_bytes: bytes | None):
    """Кнопка генерации"""
    if not photos:
        return

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("📄 Генерация документа")
        st.write(f"Будет создано **{len(photos)}** пропусков")
        st.write(f"Размер: **{cfg.card_w}×{cfg.card_h}** см, "
                 f"зазор: **{cfg.cut_margin * 10:.1f}** мм")

        if st.button("🚀 Сгенерировать .docx", type="primary", use_container_width=True):
            progress = st.progress(0, text="Генерация пропусков...")

            def update_progress(value):
                progress.progress(value, text=f"Обработка... {int(value * 100)}%")

            builder = DocumentBuilder(cfg)
            docx_bytes = builder.build(photos, logo_bytes, progress_cb=update_progress)

            progress.progress(1.0, text="✅ Готово!")
            st.balloons()

            st.download_button(
                label="📥 Скачать готовый документ",
                data=docx_bytes,
                file_name="propuska.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
                use_container_width=True,
            )

            st.markdown(
                '<div class="success-box">'
                f"✅ Создано <b>{len(photos)}</b> пропусков! "
                f"Размер: {cfg.card_w}×{cfg.card_h} см"
                "</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════

def main():
    cfg = render_sidebar()
    photos, logo_bytes = render_upload(cfg)
    render_preview(cfg, photos, logo_bytes)
    render_generate(cfg, photos, logo_bytes)

    # Футер
    st.divider()
    col1, col2 = st.columns(2)
    col1.caption("🪪 Генератор пропусков v2.1")
    col2.caption(
        f"📏 Карточка: {cfg.card_w}×{cfg.card_h} см | "
        f"✂️ Зазор: {cfg.cut_margin * 10:.1f} мм"
    )


if __name__ == "__main__":
    main()