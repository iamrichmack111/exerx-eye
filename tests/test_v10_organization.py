from pathlib import Path
from datetime import date

from exerx_eye.db import ExerxEye


def seed(db: ExerxEye):
    db.conn.execute("""INSERT INTO exercises(id,exercise_name,equipment,main_muscle,difficulty)
        VALUES(1,'Bench Press','Barbell','Chest',3),
              (2,'Row','Cable','Back',2),
              (3,'Squat','Barbell','Thighs',3)""")
    db.conn.commit()


def test_v10_dashboard_insights(tmp_path: Path):
    db = ExerxEye(tmp_path / 'v10.db')
    seed(db)
    uid = db.create_user('v10user', 'hash')
    wid = db.create_user_workout(uid, 'Full Body')
    db.add_to_user_workout(uid, wid, 1, 3, 8, 100)
    db.add_to_user_workout(uid, wid, 2, 3, 10, 80)
    sid = db.start_user_session(uid, wid)
    db.log_user_set(uid, sid, 1, 1, 8, 100, 2, '')
    db.log_user_set(uid, sid, 2, 1, 10, 80, 3, '')
    db.complete_user_session(uid, sid)

    streak = db.user_training_streak(uid)
    assert streak['current'] >= 1
    assert streak['best'] >= 1

    week = db.user_week_activity(uid)
    assert len(week) == 7
    assert sum(day['sessions'] for day in week) >= 1

    mix = db.user_muscle_volume(uid, 30, 6)
    names = {row['muscle'] for row in mix}
    assert {'Chest', 'Back'} <= names

    dashboard = db.user_dashboard(uid)
    assert 'streak' in dashboard
    assert 'week_activity' in dashboard
    assert 'muscle_volume' in dashboard
    db.close()
