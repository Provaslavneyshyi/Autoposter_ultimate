import openai
import requests
from PyQt5.QtGui import QPixmap

def generate_article_text(api_key, prompt, log_callback):
    """
    Генерирует текст статьи, используя OpenAI API.

    Args:
        api_key (str): API-ключ для OpenAI.
        prompt (str): Текстовый запрос для генерации статьи.
        log_callback (callable): Функция для логирования сообщений.

    Returns:
        str or None: Сгенерированный текст статьи или None в случае ошибки.
    """
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # При использовании openai==0.28 этот вызов поддерживается.
            messages=[
                {"role": "system", "content": "Ты помогаешь генерировать статьи для блога."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        # Извлечение сгенерированного текста из ответа API
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        log_callback("Ошибка генерации статьи: " + str(e))
        return None

def generate_image(api_key, prompt, log_callback):
    """
    Генерирует изображение по заданному промпту и возвращает QPixmap.

    Args:
        api_key (str): API-ключ для OpenAI.
        prompt (str): Запрос для генерации изображения.
        log_callback (callable): Функция для логирования.

    Returns:
        QPixmap or None: Сгенерированное изображение в формате QPixmap или None при ошибке.
    """
    openai.api_key = api_key
    # Ограничение длины промпта, если он слишком длинный
    truncated_prompt = prompt if len(prompt) <= 1000 else prompt[:1000]
    try:
        response = openai.Image.create(
            prompt=truncated_prompt,
            n=1,
            size="512x512"
        )
        image_url = response["data"][0]["url"]
        image_response = requests.get(image_url)
        if image_response.status_code == 200:
            pixmap = QPixmap()
            if pixmap.loadFromData(image_response.content):
                return pixmap
            else:
                log_callback("Ошибка обработки данных изображения.")
                return None
        else:
            log_callback("Ошибка загрузки изображения: статус " + str(image_response.status_code))
            return None
    except Exception as e:
        log_callback("Ошибка генерации изображения: " + str(e))
        return None
