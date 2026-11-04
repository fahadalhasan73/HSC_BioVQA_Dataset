import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def add(name,ok,detail=''):checks.append((name,ok,detail))
add('Python >= 3.10',sys.version_info>=(3,10),sys.version.split()[0])
add('ffmpeg',bool(shutil.which('ffmpeg')),shutil.which('ffmpeg') or 'not found')
add('ffprobe',bool(shutil.which('ffprobe')),shutil.which('ffprobe') or 'not found')
for rel in ['shared/taxonomy/hsc_biology_master_taxonomy_v1.0.json','data/questions/master/question.json','data/segments/master/segments.json','data/mappings/question_video_mapping.json']:
    p=ROOT/rel
    try: json.load(p.open(encoding='utf-8')); add(rel,True,'valid JSON')
    except Exception as e:add(rel,False,str(e))
for n,ok,d in checks: print(('PASS' if ok else 'FAIL'),'-',n,'-',d)
raise SystemExit(0 if all(x[1] for x in checks if x[0] not in {'ffmpeg','ffprobe'}) else 1)
