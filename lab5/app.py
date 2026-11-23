from flask import Flask, request, jsonify
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

tasks = []
next_id = 1

MAX_TITLE_LEN = 200
DEFAULT_PER_PAGE = 10
MAX_PER_PAGE = 100


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def normalize(title):
    if not isinstance(title, str):
        return ""
    return " ".join(title.split()).lower()


def err(message, code):
    return jsonify({"error": message}), code


def find_task(task_id):
    for t in tasks:
        if t["id"] == task_id:
            return t
    return None


def title_exists(title, exclude_id=None):
    norm_title = normalize(title)
    for t in tasks:
        if exclude_id is not None and t["id"] == exclude_id:
            continue
        if normalize(t["title"]) == norm_title:
            return True
    return False


def validate_title(data, exclude_id=None):
    if not isinstance(data, dict):
        return None, err("некорректный формат JSON", 400)
    
    if "title" not in data:
        return None, err("поле title обязательно", 400)
    
    raw_title = data["title"]
    if not isinstance(raw_title, str):
        return None, err("title должен быть строкой", 422)
    
    cleaned_title = raw_title.strip()
    if not cleaned_title:
        return None, err("title не может быть пустым", 422)
    
    if len(cleaned_title) > MAX_TITLE_LEN:
        return None, err(f"title длиннее {MAX_TITLE_LEN} символов", 422)
    
    if title_exists(cleaned_title, exclude_id=exclude_id):
        return None, err("задача с таким названием уже существует", 409)
    
    return cleaned_title, None


def seed():
    global tasks, next_id
    tasks.clear()
    base_time = datetime.now(timezone.utc)
    demo_data = [
        ("Купить молоко", True, 5),
        ("Выучить REST", False, 4),
        ("Сдать лабораторную", True, 3),
        ("Проверить почту", False, 2),
        ("Позвонить маме", False, 1)
    ]
    for i, (title, done, hours_ago) in enumerate(demo_data, start=1):
        t_created = (base_time - timedelta(hours=hours_ago)).isoformat()
        tasks.append({
            "id": i,
            "title": title,
            "done": done,
            "created_at": t_created
        })
    next_id = 6


seed()


@app.get("/tasks")
def list_tasks():
    filtered = list(tasks)

    done_param = request.args.get("done")
    if done_param is not None:
        if done_param.lower() == "true":
            filtered = [t for t in filtered if t["done"] is True]
        elif done_param.lower() == "false":
            filtered = [t for t in filtered if t["done"] is False]
        else:
            return err("неверное значение параметра done", 400)

    q_param = request.args.get("q")
    if q_param is not None:
        norm_q = normalize(q_param)
        filtered = [t for t in filtered if norm_q in normalize(t["title"])]

    sort_field = request.args.get("sort", "created_at")
    if sort_field not in ["id", "title", "created_at"]:
        return err("неверное поле для сортировки", 400)

    order_param = request.args.get("order", "asc")
    if order_param not in ["asc", "desc"]:
        return err("неверный порядок сортировки", 400)

    reverse = (order_param == "desc")
    try:
        filtered.sort(key=lambda x: x[sort_field], reverse=reverse)
    except Exception:
        pass

    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        return err("неверный номер страницы", 400)

    try:
        per_page = int(request.args.get("per_page", DEFAULT_PER_PAGE))
    except ValueError:
        return err("неверный размер страницы", 400)

    if page < 1 or per_page < 1 or per_page > MAX_PER_PAGE:
        return err("недопустимые параметры пагинации", 400)

    total = len(filtered)
    pages = (total + per_page - 1) // per_page if total > 0 else 1

    start = (page - 1) * per_page
    end = start + per_page
    items = filtered[start:end]

    return jsonify({
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages
    }), 200


@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    t = find_task(task_id)
    if not t:
        return err("задача не найдена", 404)
    return jsonify(t), 200


@app.post("/tasks")
def create_task():
    global next_id
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return err("тело запроса должно быть JSON-объектом", 400)

    title, error_response = validate_title(data)
    if error_response:
        return error_response

    done_val = data.get("done", False)
    if not isinstance(done_val, bool):
        done_val = bool(done_val)

    task = {
        "id": next_id,
        "title": title,
        "done": done_val,
        "created_at": now_iso()
    }
    tasks.append(task)
    next_id += 1
    return jsonify(task), 201


@app.put("/tasks/<int:task_id>")
def replace_task(task_id):
    t = find_task(task_id)
    if not t:
        return err("задача не найдена", 404)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return err("тело запроса должно быть JSON-объектом", 400)

    title, error_response = validate_title(data, exclude_id=task_id)
    if error_response:
        return error_response

    done_val = data.get("done", False)
    if not isinstance(done_val, bool):
        done_val = bool(done_val)

    t["title"] = title
    t["done"] = done_val
    return jsonify(t), 200


@app.patch("/tasks/<int:task_id>")
def update_task(task_id):
    t = find_task(task_id)
    if not t:
        return err("задача не найдена", 404)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return err("тело запроса должно быть JSON-объектом", 400)

    if "title" in data:
        title, error_response = validate_title(data, exclude_id=task_id)
        if error_response:
            return error_response
        t["title"] = title

    if "done" in data:
        done_val = data["done"]
        if not isinstance(done_val, bool):
            done_val = bool(done_val)
        t["done"] = done_val

    return jsonify(t), 200


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    global tasks
    t = find_task(task_id)
    if not t:
        return err("задача не найдена", 404)
    
    tasks = [item for item in tasks if item["id"] != task_id]
    return "", 204


@app.get("/")
def index():
    return jsonify({
        "service": "tasks-api",
        "seed": len(tasks),
        "endpoints": [
            "GET /",
            "GET /tasks",
            "GET /tasks/<id>",
            "POST /tasks",
            "PUT /tasks/<id>",
            "PATCH /tasks/<id>",
            "DELETE /tasks/<id>"
        ]
    }), 200


if __name__ == "__main__":
    app.run(debug=True)