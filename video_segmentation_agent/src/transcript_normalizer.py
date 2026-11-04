import re, unicodedata
_WS=re.compile(r'\s+')
def normalize_text(text):
    text=unicodedata.normalize('NFC',text or '').replace('\u200c','').replace('\u200d','')
    return _WS.sub(' ',text).strip()
def normalize_asr_segments(segments):
    return [{**s,'text_normalized':normalize_text(s.get('text',''))} for s in segments]
