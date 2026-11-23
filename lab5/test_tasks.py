import requests

BASE_URL = "http://localhost:5000"

def test_api():
    print("Запуск тестов для Tasks API...")

    # 1. Проверка корневого эндпоинта
    r = requests.get(f"{BASE_URL}/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "tasks-api"
    assert data["seed"] == 5
    print("1. GET / — ОК")

    # 2. Получение списка задач
    r = requests.get(f"{BASE_URL}/tasks")
    assert r.status_code == 200
    tasks_data = r.json()
    assert "items" in tasks_data
    assert tasks_data["total"] == 5
    print("2. GET /tasks — ОК")

    # 3. Создание новой задачи (POST)
    r = requests.post(f"{BASE_URL}/tasks", json={"title": "Тестовая задача из скрипта"})
    assert r.status_code == 201
    new_task = r.json()
    new_id = new_task["id"]
    print(f"3. POST /tasks (создано с id={new_id}) — ОК")

    # 4. Проверка дубликата (409)
    r = requests.post(f"{BASE_URL}/tasks", json={"title": "Тестовая задача из скрипта"})
    assert r.status_code == 409
    print("4. Проверка дубликата (409) — ОК")

    # 5. Удаление задачи (DELETE -> 204)
    r = requests.delete(f"{BASE_URL}/tasks/{new_id}")
    assert r.status_code == 204
    print("5. DELETE /tasks/<id> (204) — ОК")

    # 6. Повторный DELETE должен вернуть 404
    r = requests.delete(f"{BASE_URL}/tasks/{new_id}")
    assert r.status_code == 404
    print("6. Повторный DELETE (404) — ОК")

    print("\nВсе тесты успешно пройдены!")

if __name__ == "__main__":
    test_api()