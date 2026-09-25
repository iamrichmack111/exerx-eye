from pathlib import Path

import pytest

flask = pytest.importorskip("flask")
from app import create_app

CSV = Path(__file__).parents[1] / "data" / "gym_exercise_dataset.csv"


def make_client(tmp_path):
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test",
        "DATABASE": tmp_path / "flask-test.db",
        "CSV_PATH": CSV,
    })
    return app.test_client()


def signup(client, username="tester", password="Password123!"):
    return client.post("/signup", data={
        "username": username,
        "password": password,
        "confirm_password": password,
    })


def test_home_and_health(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert b"Exercise library" in response.data
    health = client.get("/health")
    assert health.status_code == 200
    assert health.get_json()["exercises"] == 617
    assert health.get_json()["schema_version"] >= 5


def test_api_search(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/api/exercises?q=barbell&field=Equipment&limit=5")
    assert response.status_code == 200
    rows = response.get_json()["results"]
    assert rows
    assert all("barbell" in row["equipment"].lower() for row in rows)


def test_signup_login_and_private_workout_flow(tmp_path):
    client = make_client(tmp_path)
    created = signup(client)
    assert created.status_code == 302
    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert b"Welcome back" in dashboard.data
    account = client.get("/account")
    assert account.status_code == 200
    assert b"tester" in account.data

    create = client.post("/workouts", data={"name": "Push Day"})
    assert create.status_code == 302
    exercise = client.get("/api/exercises?limit=1").get_json()["results"][0]
    add = client.post(f"/workouts/1/add/{exercise['id']}", data={"sets": 3, "reps": 8})
    assert add.status_code == 302
    page = client.get("/workouts/1")
    assert exercise["exercise_name"].encode() in page.data
    started = client.post("/workouts/1/start")
    assert started.status_code == 302
    session_path = started.headers["Location"]
    assert "session=" in session_path
    session_id = int(session_path.split("session=")[1].split("&")[0])
    logged = client.post(f"/sessions/{session_id}/log/{exercise['id']}", data={"reps": 8, "weight": 100, "rir": 2, "note": "smooth"})
    assert logged.status_code == 302
    progress = client.get("/progress")
    assert b"smooth" in progress.data

    logout = client.post("/logout")
    assert logout.status_code == 302
    assert client.get("/workouts").status_code == 302

    login = client.post("/login", data={"login": "tester", "password": "Password123!"})
    assert login.status_code == 302
    assert client.get("/workouts/1").status_code == 200


def test_user_data_isolation(tmp_path):
    client = make_client(tmp_path)
    signup(client, "alpha")
    client.post("/workouts", data={"name": "Alpha Plan"})
    client.post("/logout")

    signup(client, "beta")
    page = client.get("/workouts")
    assert b"Alpha Plan" not in page.data
    assert client.get("/workouts/1").status_code == 404


def test_exports_require_login_and_download(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/exports").status_code == 302
    signup(client)
    assert client.get("/exports").status_code == 200
    for path in ["/exports/progress.csv", "/exports/workouts.csv", "/exports/favorites.csv", "/exports/account.json"]:
        response = client.get(path)
        assert response.status_code == 200
        assert "attachment" in response.headers.get("Content-Disposition", "")


def test_planner_preferences_and_session_review_routes(tmp_path):
    client = make_client(tmp_path)
    signup(client)
    client.post('/workouts', data={'name': 'Upper'})
    exercise = client.get('/api/exercises?limit=1').get_json()['results'][0]
    client.post(f"/workouts/1/add/{exercise['id']}", data={'sets': 2, 'reps': 8, 'target_weight': 100})

    prefs = client.post('/account/preferences', data={'weekly_goal': 4, 'default_rest': 90})
    assert prefs.status_code == 302
    account = client.get('/account')
    assert b'90 seconds' in account.data

    planner = client.post('/planner', data={'day_0': '1', 'day_1': '', 'day_2': '', 'day_3': '', 'day_4': '', 'day_5': '', 'day_6': ''})
    assert planner.status_code == 302
    planner_page = client.get('/planner')
    assert b'Upper' in planner_page.data

    started = client.post('/workouts/1/start')
    session_id = int(started.headers['Location'].split('session=')[1].split('&')[0])
    client.post(f"/sessions/{session_id}/log/{exercise['id']}", data={'reps': 8, 'weight': 100, 'rir': 2})
    finished = client.post(f'/sessions/{session_id}/finish')
    assert finished.status_code == 302
    assert '/summary' in finished.headers['Location']
    review = client.post(f'/sessions/{session_id}/summary', data={'session_rpe': 7, 'note': 'Good day'})
    assert review.status_code == 302
    page = client.get(f'/sessions/{session_id}/summary')
    assert b'Good day' in page.data
