import hashlib
import json
import mimetypes
import os
import uuid
from datetime import datetime

from flask import (Flask, flash, redirect, render_template, request,
                   send_from_directory, url_for)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")   # корневая папка для файлов
DATA_FILE = os.path.join(BASE_DIR, "files.json")    # "база данных" в JSON

# Запрещённые расширения
FORBIDDEN_EXTENSIONS = {
    ".exe", ".sh", ".php", ".js",
    ".bat", ".cmd", ".msi", ".com", ".scr", ".vbs", ".jar",
}
# Запрещённые MIME-типы
FORBIDDEN_MIME_TYPES = {
    "application/x-msdownload",
    "application/x-sh",
    "application/x-httpd-php",
    "application/javascript",
    "text/javascript",
}

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"   # нужен для flash-сообщений
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024    # лимит 16 МБ

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


#  Работа с JSON-хранилищем

def load_files():
    """Читает список записей о файлах из JSON. Если файла нет - пустой список."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_files(records):
    """Записывает список записей в JSON."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)


#  Проверки

def check_type(filename):
    """Возвращает текст ошибки, если файл запрещён, иначе None."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in FORBIDDEN_EXTENSIONS:
        return f"Загрузка файлов с расширением {ext} запрещена."
    mime, _ = mimetypes.guess_type(filename)
    if mime in FORBIDDEN_MIME_TYPES:
        return f"Тип файла {mime} запрещён к загрузке."
    return None


def md5_of(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


#  Маршруты

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        # Файл не выбран
        if file is None or file.filename == "":
            flash("Ошибка: файл не выбран.", "error")
            return redirect(url_for("index"))

        original_name = file.filename

        #  Проверка расширения / типа
        error = check_type(original_name)
        if error:
            flash(f"Ошибка: {error}", "error")
            return redirect(url_for("index"))

        data = file.read()
        if not data:
            flash("Ошибка: файл пустой.", "error")
            return redirect(url_for("index"))

        #  Проверка дубликата по MD5
        file_hash = md5_of(data)
        records = load_files()
        for rec in records:
            if rec["md5"] == file_hash:
                flash(
                    f"Ошибка: такой файл уже загружен "
                    f"(как «{rec['original_name']}»).",
                    "error",
                )
                return redirect(url_for("index"))

        #  Генерируем UUID-имя и раскладываем по подпапкам
        ext = os.path.splitext(original_name)[1].lower()
        new_name = uuid.uuid4().hex
        rel_dir = os.path.join(new_name[:2], new_name[2:4])
        abs_dir = os.path.join(UPLOAD_FOLDER, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        stored_filename = new_name + ext
        with open(os.path.join(abs_dir, stored_filename), "wb") as f:
            f.write(data)

        #  Сохраняем информацию о файле
        records.append({
            "original_name": original_name,
            "uuid_name": stored_filename,
            "path": "/".join(["uploads", new_name[:2], new_name[2:4], stored_filename]),
            "extension": ext,
            "upload_date": datetime.now().isoformat(sep=" ", timespec="seconds"),
            "md5": file_hash,
        })
        save_files(records)

        flash(f"Успех: файл «{original_name}» загружен.", "success")
        return redirect(url_for("index"))

    return render_template("index.html", files=load_files())


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Отдаёт загруженный файл по ссылке из таблицы."""
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.errorhandler(413)
def too_large(_):
    flash("Ошибка: файл слишком большой (максимум 16 МБ).", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)