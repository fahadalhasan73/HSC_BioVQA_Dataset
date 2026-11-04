from video_segmentation_agent.src.microchunk_builder import build_microchunks
def test_microchunks():
    xs=[{'asr_segment_id':i,'start_sec':i*10,'end_sec':(i+1)*10,'text_normalized':x} for i,x in enumerate(['a text','b text','c text','d text'])]
    out=build_microchunks(xs,25,35,1); assert len(out)==2; assert out[0]['start_sec']==0; assert out[-1]['end_sec']==40
