def detect_scenes(video_path,sample_interval_seconds=1.0,threshold=0.45):
    try: import cv2
    except ImportError as exc: raise RuntimeError('opencv-python-headless is required for scene detection.') from exc
    cap=cv2.VideoCapture(str(video_path)); fps=cap.get(cv2.CAP_PROP_FPS) or 25.0; step=max(1,int(fps*sample_interval_seconds)); changes=[]; prev=None; idx=0
    while True:
        ok,frame=cap.read()
        if not ok: break
        if idx%step==0:
            gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY); hist=cv2.calcHist([gray],[0],None,[64],[0,256]); cv2.normalize(hist,hist)
            if prev is not None:
                dist=cv2.compareHist(prev,hist,cv2.HISTCMP_BHATTACHARYYA)
                if dist>=threshold: changes.append({'time_sec':idx/fps,'score':float(dist)})
            prev=hist
        idx+=1
    cap.release(); return changes
