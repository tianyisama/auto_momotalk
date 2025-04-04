import pyautogui
from pynput.mouse import Listener as MouseListener
import sys

print("移动鼠标到目标位置，右键记录坐标，按Ctrl+C停止")
recorded_points = []

def on_click(x, y, button, pressed):
    """ 鼠标点击回调函数 """
    if button == button.right and pressed:
        try:
            rgb = pyautogui.pixel(x, y)
        except Exception:
            rgb = pyautogui.screenshot().getpixel((x, y))
        recorded_points.append((x, y, rgb))
        print(f"\n已记录坐标：X: {x:<4} Y: {y:<4} RGB: {rgb}")

mouse_listener = MouseListener(on_click=on_click)
mouse_listener.start()

try:
    while True:
        # 获取当前鼠标坐标
        x, y = pyautogui.position()
        
        # 获取当前像素颜色
        try:
            current_rgb = pyautogui.pixel(x, y)
        except Exception:
            current_rgb = pyautogui.screenshot().getpixel((x, y))
        
        # 实时显示坐标信息
        print(f"X: {x:<4} | Y: {y:<4} | RGB: {current_rgb}", end='\r')
        sys.stdout.flush()

except KeyboardInterrupt:
    print("\n\n坐标获取已终止")
finally:

    mouse_listener.stop()
    mouse_listener.join()

    # 显示所有记录的坐标点
    if recorded_points:
        print("\n记录的坐标点列表：")
        for idx, (x, y, rgb) in enumerate(recorded_points, 1):
            print(f"点{idx}: X: {x:<4} | Y: {y:<4} | RGB: {rgb}")
    else:
        print("\n未记录任何坐标点")