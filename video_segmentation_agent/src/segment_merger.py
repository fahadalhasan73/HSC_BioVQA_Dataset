from collections import Counter
from .utils import sec_to_hms

def _aggregate_mapping(chunks):
    mapped=[c['curriculum_mapping'] for c in chunks if (c.get('curriculum_mapping') or {}).get('status')=='mapped']
    if not mapped:return {'status':'low_information','confidence':0.0}
    def mode(k): return Counter(m.get(k) for m in mapped if m.get(k)).most_common(1)[0][0]
    sub=mode('subtopic_id'); same=[m for m in mapped if m.get('subtopic_id')==sub]; primary=Counter(m.get('primary_concept_id') for m in same if m.get('primary_concept_id')).most_common(1)[0][0]
    seconds=[]
    for m in same:
        for x in m.get('secondary_concept_ids') or []:
            if x!=primary and x not in seconds: seconds.append(x)
    base=next(m for m in same if m.get('primary_concept_id')==primary)
    return {'status':'mapped','taxonomy_version':base.get('taxonomy_version'),'paper_id':base['paper_id'],'chapter_id':base['chapter_id'],'topic_id':base['topic_id'],'subtopic_id':base['subtopic_id'],
            'primary_concept_id':primary,'secondary_concept_ids':seconds[:3],'confidence':round(sum(float(m.get('confidence',0)) for m in same)/len(same),4)}

def merge_chunks(video_id,chunks,boundaries,max_final_segment_seconds=240):
    if not chunks:return []
    split_after={b['left_chunk_id']:b for b in boundaries if b.get('split')}; groups=[]; cur=[]
    for c in chunks:
        if cur and float(c['end_sec'])-float(cur[0]['start_sec'])>max_final_segment_seconds:
            groups.append((cur,{'reason':'max_duration','score':1.0})); cur=[]
        cur.append(c)
        if c['chunk_id'] in split_after: groups.append((cur,split_after[c['chunk_id']])); cur=[]
    if cur: groups.append((cur,{'reason':'end_of_video','score':1.0}))
    out=[]
    for i,(g,b) in enumerate(groups,1):
        start=float(g[0]['start_sec']); end=float(g[-1]['end_sec'])
        out.append({'segment_id':f'{video_id}_SEG_{i:04d}','video_id':video_id,'start_sec':start,'end_sec':end,'start_time':sec_to_hms(start),'end_time':sec_to_hms(end),
                    'duration_sec':round(end-start,3),'transcript':' '.join(c['transcript'] for c in g).strip(),'source_chunk_ids':[c['chunk_id'] for c in g],
                    'curriculum_mapping':_aggregate_mapping(g),'boundary':{'end_reason':b.get('reason'),'end_boundary_score':b.get('score')},'review':{'status':'pending'}})
    return out
