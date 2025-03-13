import re


def extract_title_from_html(html):
    """
    Извлекает заголовок из HTML-текста.

    Ищет первый тег <h1>-<h6> и возвращает его содержимое.
    Если заголовок не найден, возвращает "Без заголовка".

    Args:
        html (str): HTML-текст.

    Returns:
        str: Заголовок или "Без заголовка".
    """
    pattern = re.compile(r'<h[1-6]>(.*?)</h[1-6]>', re.IGNORECASE)
    match = pattern.search(html)
    if match:
        title = match.group(1).strip()
        if title:
            return title
    return "Без заголовка"
