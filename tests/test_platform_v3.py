from exerx_eye.db import ExerxEye

def seed(db):
    db.conn.execute("""INSERT INTO exercises (exercise_name,equipment,variation,utility,mechanics,force,preparation,execution,target_muscles,synergist_muscles,stabilizer_muscles,antagonist_muscles,dynamic_stabilizer_muscles,main_muscle,difficulty,secondary_muscles,parent_id) VALUES ('Squat','Barbell','','Basic','Compound','Push','','','Quadriceps','','','','','Quadriceps',3,'Glutes','')""")
    db.conn.commit()

def test_schema_health_and_progress(tmp_path):
    db=ExerxEye(tmp_path/'v3.db'); seed(db)
    assert db.schema_version()==3
    eid=db.conn.execute('SELECT id FROM exercises').fetchone()[0]
    wid=db.create_workout('Leg Day'); db.add_to_workout(wid,eid,5,5,225)
    sid=db.start_session(wid)
    assert db.session_set_count(sid,eid)==0
    db.log_set(sid,eid,1,5,225)
    assert db.session_set_count(sid,eid)==1
    db.complete_session(sid)
    row=db.progress(eid)[0]
    assert row['volume']==1125
    assert db.health()['sessions']==1
    db.close()


def test_query_language(tmp_path):
    db=ExerxEye(tmp_path/'q.db'); seed(db)
    assert len(db.query(text='muscle:Quadriceps equipment:Barbell'))==1
    assert len(db.query(text='muscle:Chest'))==0
    assert len(db.query(text='-equipment:Dumbbell'))==1
    db.close()
