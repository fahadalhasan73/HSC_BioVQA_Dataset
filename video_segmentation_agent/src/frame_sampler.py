from pathlib import Path
def sample_frames(video_path,output_dir,interval_seconds=30):
    import cv2
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True); cap=cv2.VideoCapture(str(video_path)); fps=cap.get(cv2.CAP_PROP_FPS) or 25.0; step=max(1,int(fps*interval_seconds)); idx=0; rows=[]
    while True:
        ok,frame=cap.read()
        if not ok: break
        if idx%step==0:
            t=idx/fps; p=out/f'frame_{len(rows)+1:05d}_{int(t):06d}s.jpg'; cv2.imwrite(str(p),frame); rows.append({'time_sec':t,'file':str(p)})
        idx+=1
    cap.release(); return rows
