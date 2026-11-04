from video_segmentation_agent.src.transcript_normalizer import normalize_text
def test_bn_normalize(): assert normalize_text('  কোষ   বিভাজন ')=='কোষ বিভাজন'
