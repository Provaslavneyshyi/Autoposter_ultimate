# data/data_manager.py

import json
import os
from config import DATA_FILE

def load_data():
    """
    Загружает данные из JSON-файла.

    Если файл существует, выполняется его чтение и возврат словаря.
    Если файла нет, возвращается словарь с пустыми значениями для ключей.
    """
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка чтения {DATA_FILE}: {e}")
            return {}
    else:
        return {
            "profiles": [],
            "api_keys": [],
            "categories": [],
            "prompts": [],
            "image_prompts": [],
            "generated_articles": [],      # <--- Новый список для сгенерированных статей
            "published_articles": []
        }

def save_data(data):
    """
    Сохраняет данные в JSON-файл.

    Args:
        data (dict): Данные для сохранения.
    """
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка записи в {DATA_FILE}: {e}")
