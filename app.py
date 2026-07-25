from pathlib import Path
import os
from fastapi import FastAPI, HTTPException, Query
from exerx_eye.db import ExerxEye

DB_PATH=Path(os.getenv('EXERCISE_DB_PATH','/data/exercises.db'))
CSV_PATH=Path(os.getenv('EXERCISE_CSV_PATH','data/gym_exercise_dataset.csv'))
db=ExerxEye(DB_PATH)
if db.count()==0 and CSV_PATH.exists(): db.import_csv(CSV_PATH)

app=FastAPI(title='ExerxEye API', version='3.0.0')

def public(e):
    d=e.__dict__.copy(); d['favorite']=bool(d['favorite']); return d

@app.get('/')
def root(): return {'name':'ExerxEye API','version':'3.0.0','docs':'/docs'}

@app.get('/health')
def health(): return {**db.health(),'schema_version':db.schema_version()}

@app.get('/exercises')
def exercises(q:str='', muscle:str='All', equipment:str='All', difficulty:str='All', limit:int=Query(100,ge=1,le=500)):
    return {'results':[public(e) for e in db.query(text=q,muscle=muscle,equipment=equipment,difficulty=difficulty,limit=limit)]}

@app.get('/exercises/{exercise_id}')
def exercise(exercise_id:int):
    e=db.get(exercise_id)
    if not e: raise HTTPException(404,'Exercise not found')
    return public(e)

@app.get('/random')
def random_exercises(muscle:str|None=None,count:int=Query(1,ge=1,le=24)):
    return {'results':[public(e) for e in db.random(muscle,count)]}

@app.get('/muscles')
def muscles(): return {'muscles':db.distinct('main_muscle')}

@app.get('/stats')
def stats():
    s=db.stats()
    return {**{k:v for k,v in s.items() if not k.startswith('by_')},
            'by_muscle':[dict(r) for r in s['by_muscle']],
            'by_equipment':[dict(r) for r in s['by_equipment']],
            'by_difficulty':[dict(r) for r in s['by_difficulty']]}

# Backward-compatible legacy routes.
@app.get('/list_muscles')
def list_muscles(): return muscles()
@app.get('/search')
def legacy_search(column:str,value:str):
    mapping={'Exercise Name':'Name','Equipment':'Equipment','Target_Muscles':'Target','Main_muscle':'Main Muscle','Utility':'Utility','Mechanics':'Mechanics','Force':'Force','Variation':'Variation'}
    field=mapping.get(column,'All')
    return {'results':[public(e) for e in db.query(text=value,field=field,limit=500)]}
@app.get('/search_by_equipment')
def search_by_equipment(equipment:str): return {'results':[public(e) for e in db.query(text=equipment,field='Equipment',limit=500)]}
@app.get('/one_exercise_per_muscle')
def one_exercise_per_muscle(muscle:str|None=None): return random_exercises(muscle,1)
@app.get('/six_exercises_per_muscle')
def six_exercises_per_muscle(muscle:str|None=None): return random_exercises(muscle,6)
