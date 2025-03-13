import markdown

def format_text_to_html(text, log_callback):
    try:
        return markdown.markdown(text)
    except Exception as e:
        log_callback("Ошибка конвертации markdown: " + str(e))
        return "<p>" + text + "</p>"