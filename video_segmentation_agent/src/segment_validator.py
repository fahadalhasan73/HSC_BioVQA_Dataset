from .taxonomy_validator import validate_mapping
def validate_segment(segment,taxonomy=None):
    if float(segment.get('duration_sec',0))<=0: raise ValueError('Segment duration must be positive')
    if not str(segment.get('transcript','')).strip(): raise ValueError('Segment transcript is empty')
    if float(segment['end_sec'])<=float(segment['start_sec']): raise ValueError('Invalid segment time range')
    if taxonomy and (segment.get('curriculum_mapping') or {}).get('status')=='mapped': validate_mapping(taxonomy,segment['curriculum_mapping'])
