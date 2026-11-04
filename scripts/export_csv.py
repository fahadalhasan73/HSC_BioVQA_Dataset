import csv,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; out=ROOT/'data/exports';out.mkdir(parents=True,exist_ok=True)
def write(name,rows,fields):
    with (out/name).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
q=json.load((ROOT/'data/questions/master/question.json').open(encoding='utf-8')).get('questions',[]); qr=[]
for x in q:
    m=x.get('curriculum_mapping',{});s=x.get('source',{});qr.append({'question_id':x.get('question_id'),'question':x.get('question_original_bn'),'board':s.get('board'),'year':s.get('year'),'paper_id':m.get('paper_id'),'chapter_id':m.get('chapter_id'),'topic_id':m.get('topic_id'),'subtopic_id':m.get('subtopic_id'),'primary_concept_id':m.get('primary_concept_id'),'confidence':m.get('confidence'),'review_status':m.get('review_status')})
write('questions.csv',qr,list(qr[0].keys()) if qr else ['question_id'])
s=json.load((ROOT/'data/segments/master/segments.json').open(encoding='utf-8')).get('segments',[]); sr=[]
for x in s:
    m=x.get('curriculum_mapping',{});sr.append({'segment_id':x.get('segment_id'),'video_id':x.get('video_id'),'start_sec':x.get('start_sec'),'end_sec':x.get('end_sec'),'transcript':x.get('transcript'),'chapter_id':m.get('chapter_id'),'topic_id':m.get('topic_id'),'subtopic_id':m.get('subtopic_id'),'primary_concept_id':m.get('primary_concept_id'),'confidence':m.get('confidence')})
write('segments.csv',sr,list(sr[0].keys()) if sr else ['segment_id'])
p=json.load((ROOT/'data/mappings/question_video_mapping.json').open(encoding='utf-8')).get('pairs',[]);pr=[]
for x in p:pr.append({'pair_id':x.get('pair_id'),'question_id':x.get('question_id'),'video_id':x.get('video_id'),'segment_id':x.get('segment_id'),'final_score':(x.get('scores') or {}).get('final'),'status':x.get('status')})
write('question_video_pairs.csv',pr,list(pr[0].keys()) if pr else ['pair_id'])
print('CSV exports written to',out)
