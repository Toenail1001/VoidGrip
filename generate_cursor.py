import cv2
import numpy as np
import struct
import ctypes
import os

# Create a 32x32 transparent image (BGRA)
img = np.zeros((32, 32, 4), dtype=np.uint8)

# Center is (16, 16). Draw a circle
center = (16, 16)
radius = 14
cv2.circle(img, center, radius, (220, 220, 220, 255), -1) # light gray circle
cv2.circle(img, center, radius, (100, 100, 100, 255), 2)  # dark gray border

# Draw an inner dot
cv2.circle(img, center, 3, (100, 100, 100, 255), -1)

# Draw Up arrow
pts_up = np.array([[16, 5], [10, 11], [13, 11], [16, 8], [19, 11], [22, 11]], np.int32)
cv2.fillPoly(img, [pts_up], (80, 80, 80, 255))
cv2.polylines(img, [pts_up], True, (50, 50, 50, 255), 1)

# Draw Down arrow
pts_down = np.array([[16, 27], [10, 21], [13, 21], [16, 24], [19, 21], [22, 21]], np.int32)
cv2.fillPoly(img, [pts_down], (80, 80, 80, 255))
cv2.polylines(img, [pts_down], True, (50, 50, 50, 255), 1)

ret, png_data = cv2.imencode('.png', img)
png_bytes = png_data.tobytes()

with open('scroll.cur', 'wb') as f:
    f.write(struct.pack('<HHH', 0, 2, 1))
    f.write(struct.pack('<BBBBHHII', 32, 32, 0, 0, 16, 16, len(png_bytes), 22))
    f.write(png_bytes)

print("Created scroll.cur")

_user32 = ctypes.windll.user32
IMAGE_CURSOR = 2
LR_LOADFROMFILE = 0x0010
h = _user32.LoadImageW(0, os.path.abspath("scroll.cur"), IMAGE_CURSOR, 0, 0, LR_LOADFROMFILE)
print("Cursor Handle returned by LoadImageW:", h)
if h == 0:
    import ctypes.wintypes
    err = ctypes.GetLastError()
    print("Failed to load cursor. Error code:", err)
