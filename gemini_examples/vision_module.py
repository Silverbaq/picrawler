import cv2
import os
import config

class VisionModule:
    def __init__(self):
        # Load Haar Cascade
        # We need the xml file. Usually it's in cv2 data.
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def detect_face(self, img_path_or_array):
        """
        Returns (x, y, w, h) of the largest face found, or None.
        x, y are normalized -1.0 to 1.0 from center? 
        Let's return normalized offset from center (-1 to 1) for X and Y.
        """
        img = None
        if isinstance(img_path_or_array, str):
            if os.path.exists(img_path_or_array):
                img = cv2.imread(img_path_or_array)
        else:
            img = img_path_or_array
            
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Find largest face
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = largest_face
        
        height, width = img.shape[:2]
        center_x = width / 2
        center_y = height / 2
        
        # Calculate offset
        face_center_x = x + w/2
        face_center_y = y + h/2
        
        offset_x = (face_center_x - center_x) / (width / 2) # -1 (left) to 1 (right)
        offset_y = (face_center_y - center_y) / (height / 2) # -1 (up) to 1 (down) ? 
        # usually y goes down in images. 0 is top.
        # if face is at 0 (top), center is H/2. 0 - H/2 = -H/2. / H/2 = -1. So -1 is Top, 1 is Bottom.
        
        return offset_x, offset_y
