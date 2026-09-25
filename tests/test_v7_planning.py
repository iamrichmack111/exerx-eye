from pathlib import Path
from exerx_eye.db import ExerxEye


def seed(db: ExerxEye):
    db.conn.execute("""INSERT INTO exercises(id,exercise_name,equipment,main_muscle,difficulty)
        VALUES(1,'Bench Press','Barbell','Chest',3),(2,'Row','Cable','Back',2)""")
    db.conn.commit()


def test_preferences_schedule_active_session_and_review(tmp_path: Path):
    db = ExerxEye(tmp_path / 'v7.db')
    seed(db)
    uid = db.create_user('planner','planner@example.com','hash')
    wid = db.create_user_workout(uid, 'Upper', 'Plan')
    db.add_to_user_workout(uid, wid, 1, 3, 8, 135)

    assert db.schema_version() >= 6
    assert db.user_preferences(uid) == {'weekly_goal': 3, 'default_rest': 60}
    assert db.update_user_preferences(uid, 4, 90) == {'weekly_goal': 4, 'default_rest': 90}

    assert db.set_user_schedule(uid, 0, wid)
    schedule = db.user_schedule(uid)
    assert len(schedule) == 1
    assert schedule[0]['weekday'] == 0
    assert schedule[0]['name'] == 'Upper'

    sid = db.start_user_session(uid, wid)
    active = db.user_active_session(uid)
    assert active['id'] == sid
    db.log_user_set(uid, sid, 1, 1, 8, 135, 2, 'good')
    db.complete_user_session(uid, sid)
    assert db.user_active_session(uid) is None

    review = db.user_session_review(uid, sid)
    assert review['sets'] == 1
    assert review['exercises'] == 1
    assert review['volume'] == 1080
    assert review['avg_rir'] == 2
    assert db.update_user_session_review(uid, sid, 7, 'Felt strong')
    review = db.user_session_review(uid, sid)
    assert review['session']['session_rpe'] == 7
    assert review['session']['note'] == 'Felt strong'

    bundle = db.user_export_bundle(uid)
    assert bundle['preferences']['default_rest'] == 90
    assert bundle['schedule'][0]['workout_id'] == wid
    assert bundle['sessions'][0]['session_rpe'] == 7
    db.close()


def test_discard_active_session(tmp_path: Path):
    db = ExerxEye(tmp_path / 'discard.db')
    seed(db)
    uid = db.create_user('discard','discard@example.com','hash')
    wid = db.create_user_workout(uid, 'Plan')
    sid = db.start_user_session(uid, wid)
    assert db.discard_user_session(uid, sid)
    assert db.user_session(uid, sid) is None
    db.close()
