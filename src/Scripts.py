import requests, openai, markdown
from PyQt5.QtGui import QPixmap

def get_category_id(url, login, app_password, category_name, log_callback):
    try:
        response = requests.get(
            url.rstrip("/") + "/wp-json/wp/v2/categories",
            auth=(login, app_password)
        )
        if response.status_code == 200:
            categories = response.json()
            for cat in categories:
                if cat["name"].lower() == category_name.lower():
                    return cat["id"]
        log_callback("Не удалось найти категорию по названию: " + category_name)
        return None
    except Exception as e:
        log_callback("Ошибка при поиске категории: " + str(e))
        return None

def create_category(url, login, app_password, category_name, log_callback):
    try:
        post_data = {"name": category_name}
        response = requests.post(
            url.rstrip("/") + "/wp-json/wp/v2/categories",
            json=post_data,
            auth=(login, app_password)
        )
        if response.status_code in (200, 201):
            log_callback("Категория создана: " + category_name)
            return response.json().get("id")
        else:
            log_callback("Ошибка создания категории: " + response.text)
            return None
    except Exception as e:
        log_callback("Ошибка создания категории: " + str(e))
        return None

def generate_article_text(api_key, prompt, log_callback):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # замените модель, если нужно
            messages=[
                {"role": "system", "content": "Ты помогаешь генерировать статьи для блога."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        log_callback("Ошибка генерации статьи: " + str(e))
        return None

def format_text_to_html(text, log_callback):
    try:
        return markdown.markdown(text)
    except Exception as e:
        log_callback("Ошибка конвертации markdown: " + str(e))
        return "<p>" + text + "</p>"

def generate_image(api_key, prompt, log_callback):
    openai.api_key = api_key
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

def publish_article(url, login, app_password, title, content, category, log_callback):
    if not category.strip():
        category = "Uncategorized"
    try:
        # Пытаемся преобразовать в число (ID)
        category_id = int(category)
    except ValueError:
        # Если не число – ищем категорию по имени
        category_id = get_category_id(url, login, app_password, category, log_callback)
        if category_id is None:
            log_callback("Категория не найдена, создаём новую...")
            category_id = create_category(url, login, app_password, category, log_callback)
            if category_id is None:
                log_callback("Ошибка публикации: не удалось создать рубрику")
                return None, None
    post_data = {
        "title": title,
        "content": content,
        "status": "publish",
        "categories": [category_id]
    }
    try:
        response = requests.post(
            url.rstrip("/") + "/wp-json/wp/v2/posts",
            json=post_data,
            auth=(login, app_password)
        )
        if response.status_code in (200, 201):
            log_callback("Статья успешно опубликована: " + title)
            return response.json(), None
        else:
            log_callback("Ошибка публикации: " + response.text)
            return None, response.text
    except Exception as e:
        log_callback("Ошибка публикации: " + str(e))
        return None, str(e)
