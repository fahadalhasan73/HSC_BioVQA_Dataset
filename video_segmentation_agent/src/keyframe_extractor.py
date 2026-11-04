from pathlib import Path
def extract_segment_keyframes(video_path,segments,output_dir):
    import cv2
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); cap=cv2.VideoCapture(str(video_path)); rows=[]
    for seg in segments:
        t=(float(seg['start_sec'])+float(seg['end_sec']))/2; cap.set(cv2.CAP_PROP_POS_MSEC,t*1000); ok,frame=cap.read()
        if ok:
            p=out/f"{seg['segment_id']}.jpg"; cv2.imwrite(str(p),frame); seg.setdefault('visual',{})['keyframe']=str(p); rows.append({'segment_id':seg['segment_id'],'time_sec':t,'file':str(p)})
    cap.release(); return rows
