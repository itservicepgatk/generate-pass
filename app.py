"""
🎨 Генератор пропусков — веб-интерфейс
Streamlit-приложение для создания и редактирования пропусков
"""

import streamlit as st
from PIL import Image
import io

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

# Кастомный CSS
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
    .card-preview {
        border: 2px solid #E0E0E0;
        border-radius: 12px;
        padding: 8px;
        background: #FAFAFA;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .success-box {
        background: #D4EDDA;
        border: 1px solid #C3E6CB;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


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
    st.sidebar.subheader("📐 Размеры (см)")
    col1, col2 = st.sidebar.columns(2)
    cfg.card_w = col1.number_input("Ширина", 5.0, 15.0, cfg.card_w, 0.5)
    cfg.card_h = col2.number_input("Высота", 4.0, 12.0, cfg.card_h, 0.5)

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

def render_upload() -> tuple:
    """Рендерит зону загрузки, возвращает (photos_dict, logo_bytes)"""

    st.markdown('<p class="main-header">🪪 Генератор пропусков</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Загрузите фото сотрудников → настройте → скачайте готовый документ</p>',
                unsafe_allow_html=True)

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
        st.caption("Необязательно")
        uploaded_logo = st.file_uploader(
            "Логотип организации",
            type=["jpg", "jpeg", "png"],
            key="logo",
        )

    photos = {}
    if uploaded_photos:
        for f in uploaded_photos:
            fio = f.name.rsplit(".", 1)[0]  # убираем расширение
            photos[fio] = f.read()
            f.seek(0)  # сбрасываем позицию для повторного чтения

    logo_bytes = None
    if uploaded_logo:
        logo_bytes = uploaded_logo.read()
        uploaded_logo.seek(0)

    return photos, logo_bytes


# ═══════════════════════════════════════════════════
#  ПРЕВЬЮ КАРТОЧЕК
# ═══════════════════════════════════════════════════

def render_preview(cfg: PassConfig, photos: dict, logo_bytes: bytes | None):
    """Показывает превью первых карточек"""
    if not photos:
        st.info("👆 Загрузите фотографии сотрудников для начала работы")
        return

    st.divider()
    st.subheader(f"👁️ Превью ({len(photos)} сотрудников)")

    renderer = CardRenderer(cfg)
    logo_pil = None
    if logo_bytes:
        logo_pil = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

    # Показываем максимум 4 превью
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
    """Кнопка генерации и скачивания"""
    if not photos:
        return

    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("📄 Генерация документа")
        st.write(f"Будет создано **{len(photos)}** пропусков")

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
                f"✅ Создано <b>{len(photos)}</b> пропусков!"
                "</div>",
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════

def main():
    cfg = render_sidebar()
    photos, logo_bytes = render_upload()
    render_preview(cfg, photos, logo_bytes)
    render_generate(cfg, photos, logo_bytes)

    # Футер
    st.divider()
    st.caption("🪪 Генератор пропусков v2.0 | Streamlit + Python")


if __name__ == "__main__":
    main()