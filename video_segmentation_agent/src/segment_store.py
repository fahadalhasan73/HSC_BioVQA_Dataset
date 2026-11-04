from pathlib import Path
from .utils import atomic_write_json,backup_json,utc_now_iso
class SegmentStore:
    def __init__(self,path,backup_dir): self.path=Path(path); self.backup_dir=Path(backup_dir); self.data=self._load()
    def _load(self):
        import json
        if self.path.exists(): return json.load(self.path.open(encoding='utf-8'))
        return {'dataset':{'name':'HSC BioVQA Segment Registry','schema_version':'1.0','revision':0,'total_videos':0,'total_segments':0,'last_updated':None},'videos':[],'segments':[]}
    def upsert_video(self,video_record,segments):
        vid=video_record['video_id']; self.data['videos']=[x for x in self.data['videos'] if x.get('video_id')!=vid]; self.data['segments']=[x for x in self.data['segments'] if x.get('video_id')!=vid]
        self.data['videos'].append(video_record); self.data['segments'].extend(segments); d=self.data['dataset']; d['revision']=int(d.get('revision',0))+1; d['total_videos']=len(self.data['videos']); d['total_segments']=len(self.data['segments']); d['last_updated']=utc_now_iso()
    def save(self,backup=True):
        if backup: backup_json(self.path,self.backup_dir)
        atomic_write_json(self.path,self.data)
