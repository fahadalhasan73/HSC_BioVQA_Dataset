from video_segmentation_agent.src.segment_merger import merge_chunks
def test_merge():
    m={'status':'mapped','taxonomy_version':'v','paper_id':'P','chapter_id':'C','topic_id':'T','subtopic_id':'S','primary_concept_id':'X','secondary_concept_ids':[],'confidence':.9}
    chunks=[{'chunk_id':'MC_0001','start_sec':0,'end_sec':20,'transcript':'a','curriculum_mapping':m},{'chunk_id':'MC_0002','start_sec':20,'end_sec':40,'transcript':'b','curriculum_mapping':m}]
    out=merge_chunks('VID',chunks,[],240); assert len(out)==1 and out[0]['duration_sec']==40
