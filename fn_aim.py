import cv2
import numpy as np
import mss
import win32api
import win32con
import time
import threading
import pygame

CONFIG = {
    'FOV_RADIUS': 180,
    'SMOOTHNESS': 0.25
}

sct = mss.mss()
sw = win32api.GetSystemMetrics(0)
sh = win32api.GetSystemMetrics(1)
cx, cy = sw // 2, sh // 2
r = CONFIG['FOV_RADIUS']
current_boxes = []
target_pos = None

def draw_overlay():
    pygame.init()
    screen = pygame.display.set_mode((sw, sh), pygame.NOFRAME | pygame.SRCALPHA)
    hwnd = pygame.display.get_wm_info()["window"]
    win32api.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST | win32con.WS_EX_TOOLWINDOW)
    win32api.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
    
    while True:
        screen.fill((0, 0, 0, 0))
        pygame.draw.circle(screen, (0, 255, 140), (cx, cy), r, 2)
        for b in current_boxes:
            pygame.draw.rect(screen, (255, 0, 0), b, 2)
        pygame.display.flip()
        time.sleep(0.01)

def logic_loop():
    global current_boxes, target_pos
    while True:
        bbox = {'left': cx-r, 'top': cy-r, 'width': r*2, 'height': r*2}
        img = np.array(sct.grab(bbox))[:, :, :3]
        mask = cv2.inRange(cv2.cvtColor(img, cv2.COLOR_BGR2HSV), np.array([0, 40, 70]), np.array([20, 255, 255]))
        contours, _ = cv2.findContours(cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8)), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        current_boxes = []
        bd, bt = 9999, None
        
        for c in contours:
            if 50 < cv2.contourArea(c) < 5000:
                x, y, w, h = cv2.boundingRect(c)
                M = cv2.moments(c)
                if M['m00'] != 0:
                    tx, ty = int(M['m10']/M['m00']), int(M['m01']/M['m00'])
                    current_boxes.append((cx-r+x, cy-r+y, w, h))
                    d = ((tx-r)**2 + (ty-r)**2)**0.5
                    if d < bd:
                        bd, bt = d, (tx, ty)
        
        target_pos = bt
        
        if win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0 and target_pos:
            dx = int((target_pos[0] - r) * (1 - CONFIG['SMOOTHNESS']))
            dy = int((target_pos[1] - r) * (1 - CONFIG['SMOOTHNESS']))
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)
            
        time.sleep(0.015)

threading.Thread(target=draw_overlay, daemon=True).start()
logic_loop()
