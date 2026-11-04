import json
from collections import defaultdict
from pathlib import Path
class TaxonomyError(ValueError): pass
class TaxonomyIndex:
    def __init__(self,payload):
        self.payload=payload; self.content_version=payload.get('taxonomy_content_version'); self.nodes=payload.get('nodes',[])
        self.by_id={}; self.children=defaultdict(list); self.by_level=defaultdict(list)
        for n in self.nodes:
            self.by_id[n['id']]=n; self.children[n.get('parent_id')].append(n); self.by_level[n.get('level','')].append(n)
    @classmethod
    def from_file(cls,path):
        with Path(path).open('r',encoding='utf-8') as f:return cls(json.load(f))
    def get(self,node_id):
        if node_id not in self.by_id: raise TaxonomyError(f'Unknown taxonomy id: {node_id}')
        return self.by_id[node_id]
    def nodes_at_level(self,level,active_only=True):
        xs=list(self.by_level.get(level,[])); return [n for n in xs if n.get('status','active')=='active'] if active_only else xs
    def ancestors(self,node_id):
        out=[]; n=self.get(node_id)
        while n.get('parent_id'): n=self.get(n['parent_id']); out.append(n)
        return out
    def path(self,node_id): return list(reversed(self.ancestors(node_id)))+[self.get(node_id)]
    def path_labels(self,node_id): return ' > '.join((n.get('label_bn') or n.get('label_en') or n['id']) for n in self.path(node_id))
    def ancestor_by_level(self,node_id,level):
        for n in self.path(node_id):
            if n.get('level')==level:return n
        return None
