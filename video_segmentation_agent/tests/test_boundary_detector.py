from video_segmentation_agent.src.boundary_detector import curriculum_change
def test_topic_change():
    a={'status':'mapped','chapter_id':'C','topic_id':'T1','subtopic_id':'S1','primary_concept_id':'X'}; b={**a,'topic_id':'T2'}
    score,reason=curriculum_change(a,b); assert reason=='topic_change' and score>=.9
