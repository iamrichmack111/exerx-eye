from exerx_eye.db import ExerxEye
def test_workout_history(tmp_path):
 db=ExerxEye(tmp_path/"x.db")
 db.conn.execute("""INSERT INTO exercises (exercise_name,equipment,variation,utility,mechanics,force,preparation,execution,target_muscles,synergist_muscles,stabilizer_muscles,antagonist_muscles,dynamic_stabilizer_muscles,main_muscle,difficulty,secondary_muscles,parent_id) VALUES ('Bench Press','Barbell','','Basic','Compound','Push','','','Chest','','','','','Chest',3,'Triceps','')"""); db.conn.commit()
 eid=db.conn.execute("SELECT id FROM exercises").fetchone()[0]
 wid=db.create_workout("Push Day"); db.add_to_workout(wid,eid,4,8,135)
 assert db.workout_detail(wid)[0]["sets"]==4
 sid=db.start_session(wid); db.log_set(sid,eid,1,8,135); db.complete_session(sid)
 assert db.progress(eid)[0]["volume"]==1080
 assert db.health()["sets"]==1
