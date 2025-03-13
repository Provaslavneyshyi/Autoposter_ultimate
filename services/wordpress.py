import requests

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

def publish_article(url, login, app_password, title, content, category, log_callback):
    if not category.strip():
        category = "Uncategorized"
    try:
        # Если возможно, пытаемся преобразовать категорию в число (ID)
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