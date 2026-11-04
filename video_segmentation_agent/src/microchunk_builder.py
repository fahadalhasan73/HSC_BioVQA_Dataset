def build_microchunks(asr_segments,target_duration_seconds=25,max_duration_seconds=35,min_text_characters=5):
    chunks=[]; current=[]
    def flush():
        nonlocal current
        if not current: return
        start=float(current[0]['start_sec']); end=float(current[-1]['end_sec'])
        text=' '.join((x.get('text_normalized') or x.get('text','')) for x in current).strip()
        if text and len(text)>=min_text_characters:
            chunks.append({'chunk_id':f'MC_{len(chunks)+1:04d}','start_sec':start,'end_sec':end,'duration_sec':round(end-start,3),
                           'transcript':text,'source_asr_segment_ids':[x['asr_segment_id'] for x in current],'curriculum_mapping':None})
        current=[]
    for seg in asr_segments:
        if not current: current=[seg]; continue
        prospective=float(seg['end_sec'])-float(current[0]['start_sec']); duration=float(current[-1]['end_sec'])-float(current[0]['start_sec'])
        if duration>=target_duration_seconds or prospective>max_duration_seconds: flush()
        current.append(seg)
    flush(); return chunks
