import json
from pathlib import Path
from difflib import SequenceMatcher
import regex
from .taxonomy_validator import validate_mapping

TOKEN_RE=regex.compile(r'[\p{L}\p{M}\p{N}_]+')
def tokens(s): return set(TOKEN_RE.findall((s or '').lower()))
def lexical_score(q,d):
    qt=tokens(q); dt=tokens(d); overlap=len(qt&dt)/len(qt) if qt else 0.0; seq=SequenceMatcher(None,(q or '').lower(),(d or '').lower()).ratio()
    return 0.7*overlap+0.3*seq

class CurriculumTagger:
    def __init__(self,taxonomy,llm,prompt_path,cfg):
        self.taxonomy=taxonomy; self.llm=llm; self.cfg=cfg; self.prompt=Path(prompt_path).read_text(encoding='utf-8')
        self.paper_id=cfg.get('paper_id','HSC_BIO_P1'); self.top_k=int(cfg.get('top_k_concepts',30)); self.max_secondary=int(cfg.get('max_secondary_concepts',3))
        self.concepts=[c for c in taxonomy.nodes_at_level('concept') if (taxonomy.ancestor_by_level(c['id'],'paper') or {}).get('id')==self.paper_id]
    def _doc(self,c):
        vals=[c.get('label_bn',''),c.get('label_en',''),*(c.get('aliases_bn') or []),*(c.get('aliases_en') or []),self.taxonomy.path_labels(c['id'])]
        return ' '.join(x for x in vals if x)
    def candidates(self,text):
        ranked=sorted(((lexical_score(text,self._doc(c)),c) for c in self.concepts),key=lambda x:x[0],reverse=True)[:self.top_k]
        out=[]
        for score,c in ranked:
            sub=self.taxonomy.ancestor_by_level(c['id'],'subtopic'); topic=self.taxonomy.ancestor_by_level(c['id'],'topic'); chapter=self.taxonomy.ancestor_by_level(c['id'],'chapter'); paper=self.taxonomy.ancestor_by_level(c['id'],'paper')
            out.append({'concept_id':c['id'],'concept_bn':c.get('label_bn'),'concept_en':c.get('label_en'),'paper_id':paper['id'],'chapter_id':chapter['id'],'topic_id':topic['id'],'subtopic_id':sub['id'],'path':self.taxonomy.path_labels(c['id']),'retrieval_score':round(score,6)})
        return out
    def tag(self,text):
        candidates=self.candidates(text); allowed={c['concept_id']:c for c in candidates}
        prompt=self.prompt.format(chunk_text=text,max_secondary_concepts=self.max_secondary,candidates_json=json.dumps(candidates,ensure_ascii=False,indent=2))
        r=self.llm.classify_json(prompt); status=r.get('status','mapped'); conf=max(0.0,min(float(r.get('confidence',0)),1.0))
        if status!='mapped': return {'status':status,'taxonomy_version':self.taxonomy.content_version,'confidence':conf,'candidate_trace':candidates}
        primary=r.get('primary_concept_id'); secs=[x for x in (r.get('secondary_concept_ids') or []) if x and x!=primary][:self.max_secondary]
        if primary not in allowed or any(x not in allowed for x in secs): raise ValueError('LLM selected concept outside candidate set')
        p=allowed[primary]
        # Restrict secondaries to the same subtopic for a coherent mapping record.
        secs=[x for x in secs if allowed[x]['subtopic_id']==p['subtopic_id']]
        m={'status':'mapped','taxonomy_version':self.taxonomy.content_version,'paper_id':p['paper_id'],'chapter_id':p['chapter_id'],'topic_id':p['topic_id'],'subtopic_id':p['subtopic_id'],
           'primary_concept_id':primary,'secondary_concept_ids':secs,'confidence':conf,'candidate_trace':candidates}
        validate_mapping(self.taxonomy,m); return m
