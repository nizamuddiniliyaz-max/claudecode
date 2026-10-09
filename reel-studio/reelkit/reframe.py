"""Optional speaker-centred 9:16 crop. Needs opencv-python-headless; falls back to centre crop."""
import statistics


def face_center_fraction(path, start, end, step=1.5):
    """Median horizontal position (0..1) of the largest face over the clip, or None."""
    try:
        import cv2
    except ImportError:
        return None
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return None
    xs, t = [], start
    while t < end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if ok:
            h, w = frame.shape[:2]
            scale = 640 / w
            small = cv2.resize(frame, (640, int(h * scale)))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, 1.15, 5, minSize=(40, 40))
            if len(faces):
                fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                xs.append((fx + fw / 2) / 640)
        t += step
    cap.release()
    if len(xs) < 3:
        return None
    return statistics.median(xs)
