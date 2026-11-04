def curriculum_change(left,right):
    if not left or not right or left.get('status')!='mapped' or right.get('status')!='mapped': return 0.5,'uncertain_mapping'
    if left.get('chapter_id')!=right.get('chapter_id'): return 1.0,'chapter_change'
    if left.get('topic_id')!=right.get('topic_id'): return 0.9,'topic_change'
    if left.get('subtopic_id')!=right.get('subtopic_id'): return 0.7,'subtopic_change'
    if left.get('primary_concept_id')!=right.get('primary_concept_id'): return 0.3,'concept_change'
    return 0.0,'curriculum_compatible'

def build_boundaries(chunks,cfg,semantic_similarities=None,scene_changes=None):
    semantic_similarities=semantic_similarities or [1.0]*(max(0,len(chunks)-1)); scene_changes=scene_changes or []; out=[]; weights=cfg.get('weights',{})
    for i in range(len(chunks)-1):
        a,b=chunks[i],chunks[i+1]; cc,reason=curriculum_change(a.get('curriculum_mapping'),b.get('curriculum_mapping'))
        sem_change=1.0-semantic_similarities[i] if i<len(semantic_similarities) else 0.0; gap=max(0.0,float(b['start_sec'])-float(a['end_sec'])); pause=min(gap/3.0,1.0)
        scene=1.0 if any(float(a['end_sec'])-1.5<=s['time_sec']<=float(b['start_sec'])+1.5 for s in scene_changes) else 0.0
        score=weights.get('curriculum',.65)*cc+weights.get('semantic_change',.2)*sem_change+weights.get('scene_change',.1)*scene+weights.get('pause',.05)*pause
        hard=(cfg.get('hard_split_on_chapter_change',True) and reason=='chapter_change') or (cfg.get('hard_split_on_topic_change',True) and reason=='topic_change')
        split=hard or score>=float(cfg.get('threshold',.55))
        out.append({'left_chunk_id':a['chunk_id'],'right_chunk_id':b['chunk_id'],'time_sec':float(b['start_sec']),'split':split,'score':round(score,4),'reason':reason,
                    'components':{'curriculum_change':round(cc,4),'semantic_change':round(sem_change,4),'scene_change':scene,'pause':round(pause,4)}})
    return out
