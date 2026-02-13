"""
Генератор пропусков для работников охраны — точка входа
"""

import os
from config import Config
from document_builder import DocumentBuilder


def main():
    print("🎨 Генератор профессиональных пропусков")
    print("=" * 50)

    cfg = Config()

    if not os.path.exists(cfg.FOLDER_PATH):
        print(f"❌ Папка {cfg.FOLDER_PATH} не найдена!")
        print(f"   Создайте папку и поместите туда:")
        print(f"   - Фотографии сотрудников (имя файла = ФИО)")
        print(f"   - Логотип: {cfg.LOGO_FILENAME}")
        return

    builder = DocumentBuilder()
    builder.build()

    print("\n🎉 Процесс завершен успешно!")


if __name__ == "__main__":
    main()