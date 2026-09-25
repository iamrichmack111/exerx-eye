from pathlib import Path
from exerx_eye.db import ExerxEye


def seed(db: ExerxEye):
    db.conn.execute("""INSERT INTO exercises(id,exercise_name,equipment,main_muscle,difficulty)
        VALUES(1,'Bench Press','Barbell','Chest',3),(2,'Row','Cable','Back',2)""")
    db.conn.commit()


def test_v6_private_training_features(tmp_path: Path):
    db = ExerxEye(tmp_path / 'v6.db')
    seed(db)
    uid = db.create_user('demo','demo@example.com','hash')
    wid = db.create_user_workout(uid, 'Upper', 'A plan')
    db.add_to_user_workout(uid, wid, 1, 3, 8, 135)
    db.add_to_user_workout(uid, wid, 2, 3, 10, 100)
    items = db.user_workout_detail(uid, wid)
    assert len(items) == 2

    assert db.update_user_workout_item(uid, wid, items[0]['item_id'], 4, 6, 145)
    db.move_user_workout_item(uid, wid, items[1]['item_id'], 'up')
    moved = db.user_workout_detail(uid, wid)
    assert moved[0]['exercise_id'] == 2
    assert moved[1]['sets'] == 4

    sid = db.start_user_session(uid, wid)
    db.log_user_set(uid, sid, 1, 1, 6, 145, 2, 'Solid set')
    db.complete_user_session(uid, sid)
    rows = db.user_progress(uid)
    assert rows[0]['rir'] == 2
    assert rows[0]['note'] == 'Solid set'
    assert db.user_dashboard(uid)['week']['sets'] == 1
    assert db.user_recent_prs(uid)[0]['exercise_id'] == 1
    assert db.schema_version() >= 5
    db.close()
