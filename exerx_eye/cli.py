from __future__ import annotations
import argparse
from pathlib import Path
from .db import ExerxEye

APP_DIR = Path.home()/'.local'/'share'/'exerx-eye'
DEFAULT_DB = APP_DIR/'exercises.db'

def main() -> None:
    p=argparse.ArgumentParser(prog='exerx-eye', description='ExerxEye: CLI + TUI + SQLite')
    p.add_argument('--db', type=Path, default=DEFAULT_DB)
    p.add_argument('--csv', type=Path, help='Backward compatible: import CSV before launch')
    p.add_argument('--replace', action='store_true')
    p.add_argument('--import-only', action='store_true')
    sub=p.add_subparsers(dest='command')
    imp=sub.add_parser('import'); imp.add_argument('csv',type=Path); imp.add_argument('--replace',action='store_true')
    sea=sub.add_parser('search'); sea.add_argument('query'); sea.add_argument('--muscle',default='All'); sea.add_argument('--limit',type=int,default=20)
    rnd=sub.add_parser('random'); rnd.add_argument('--muscle'); rnd.add_argument('--count',type=int,default=1)
    sub.add_parser('stats'); sub.add_parser('doctor'); sub.add_parser('tui')
    exp=sub.add_parser('export'); exp.add_argument('path',type=Path)
    args=p.parse_args()

    if args.csv:
        db=ExerxEye(args.db)
        try: print(f'Imported {db.import_csv(args.csv, replace=args.replace)} exercises into {args.db}')
        finally: db.close()
        if args.import_only: return
    if args.command=='import':
        db=ExerxEye(args.db)
        try: print(f'Imported {db.import_csv(args.csv, replace=args.replace)} exercises into {args.db}')
        finally: db.close()
        return
    if args.command=='search':
        db=ExerxEye(args.db)
        try:
            for e in db.query(text=args.query,muscle=args.muscle,limit=args.limit):
                print(f'{e.id:>4}  {e.exercise_name} | {e.main_muscle} | {e.equipment} | {e.difficulty}/5')
        finally: db.close()
        return
    if args.command=='random':
        db=ExerxEye(args.db)
        try:
            for e in db.random(args.muscle,args.count): print(f'{e.exercise_name} | {e.main_muscle} | {e.equipment} | {e.difficulty}/5')
        finally: db.close()
        return
    if args.command=='stats':
        db=ExerxEye(args.db)
        try:
            s=db.stats()
            print(f"exercises: {s['exercises']}\nunique names: {s['names']}\nequipment: {s['equipment']}\nmuscles: {s['muscles']}\nfavorites: {s['favorites']}\navg difficulty: {s['avg_difficulty']}")
        finally: db.close()
        return
    if args.command=='doctor':
        db=ExerxEye(args.db)
        try:
            h=db.health(); print('ExerxEye doctor')
            print(f"database: {h['database']}\nlatency: {h['latency_ms']} ms\ndatabase size: {h['db_size_bytes']} bytes\nexercises: {h['exercises']}\nworkouts: {h['workouts']}\ncompleted sessions: {h['sessions']}\nlogged sets: {h['sets']}\nschema version: {db.schema_version()}")
        finally: db.close()
        return
    if args.command=='export':
        db=ExerxEye(args.db)
        try: print(f"Exported {db.export_rows(db.query(limit=100000),args.path)} rows -> {args.path}")
        finally: db.close()
        return
    from .app import ExerciseTUI
    ExerciseTUI(args.db).run()

if __name__=='__main__': main()
