import pyautogui
import time
import numpy as np
from PIL import ImageGrab, Image, ImageDraw

# ================= 配置参数 =================
INITIAL_CLICKS = [(646, 848), (1877, 800)] # 1号点，2号点的x,y坐标
POLYGON_POINTS = [(2188, 571), (2181, 1754), (3182, 1760), (3186, 564)] # 3号点，4号点，5号点，6号点的x,y坐标
COLOR_A = (196, 221, 235) # 7号点的颜色RGB，建议不改
COLOR_B = (254, 134, 155) # 粉色剧情进入框的颜色RGB，建议不改
Y_OFFSET = 153 # 7，8号点的y坐标差值
COLOR_TOLERANCE = 0 # 回复消息框和剧情进入框颜色识别点的RGB容差，建议不改
DRAG_DISTANCE = 300  # 向上拖动像素数，用于消息框不处于最低端时向上拉扯用，建议不改
DRAG_DURATION = 0.5  # 拖动耗时，建议不改
CHECK_COLOR = (122, 221, 255)  # 退出剧情的确认按钮的颜色，建议不改
CHECK_TOLERANCE = 5             # 确认按钮的颜色波动容差范围，建议不改
# 以下延迟均可根据实际情况调整
FOLLOWUP_CLICKS = [
    (2734, 1612, 5),# 9号点的x,y坐标，点击后延迟5秒（考虑到剧情标题加载，不同电脑性能不一样，配置低可以增加延迟）
    (3004, 92, 0.5),# 10号点的x,y坐标，点击后延迟0.5秒
    (2193, 1549, 2),# 11号点的x,y坐标，点击后延迟2秒，奖励加载要时间
    (2193, 1549, 0.5),# 12号点的x,y坐标和11号一样，注意不要在奖励范围里不然确认不了，点击后延迟0.5秒
    (719, 646, 0.5) # 13号点的x,y坐标，点击后延迟0.5秒
]
FINAL_CLICK = (719, 646)

def create_polygon_mask(points):
    """生成多边形掩膜"""
    x_coords = [p[0] for p in points]
    y_coords = [p[1] for p in points]
    
    # 计算精确包围盒
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)
    bbox = (min_x, min_y, max_x, max_y)
    
    # 计算正确尺寸
    width = max_x - min_x
    height = max_y - min_y
    
    # 创建尺寸精确的掩膜
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    rel_points = [(x - min_x, y - min_y) for (x, y) in points]
    draw.polygon(rel_points, fill=255)
    
    # 转换为布尔矩阵
    mask_np = np.array(mask) > 128
    print(f"Debug - 掩膜尺寸：{mask_np.shape}")  # 调试输出
    
    return bbox, mask_np

POLYGON_BBOX, POLYGON_MASK = create_polygon_mask(POLYGON_POINTS)

def check_stabilization():
    """稳定检测"""
    print("🔄 稳定检测中...")
    history = []
    # 预获取尺寸信息
    width = POLYGON_BBOX[2] - POLYGON_BBOX[0]
    height = POLYGON_BBOX[3] - POLYGON_BBOX[1]
    print(f"Debug - 预期尺寸：{height}x{width}")  # 高x宽
    
    prev_frame = None
    stable_counter = 0
    
    while True:
        # 截取并转换尺寸
        img = np.array(ImageGrab.grab(bbox=POLYGON_BBOX).convert('L'))
        #print(f"Debug - 实际截图尺寸：{img.shape}")  # 调试输出
        
        # 验证尺寸
        if img.shape != POLYGON_MASK.shape:
            raise ValueError(f"尺寸不匹配！掩膜：{POLYGON_MASK.shape}，截图：{img.shape}")
        
        masked = img * POLYGON_MASK
        
        history.append(masked)
        if len(history) > 5:
            history.pop(0)
        
        if len(history) >= 2:
            # 计算画面变化
            diff = np.mean(np.abs(history[-1].astype(float) - history[-2].astype(float))) / 255
            
            if diff > 0.001:  # 0.1%的像素变化视为不稳定
                stable_counter = 0
                print(f"变化率：{diff*100:.1f}%")
            else:
                stable_counter += 1
                print(f"稳定进度：{stable_counter}/10")
                
                if stable_counter >= 10:
                    print("✅ 区域已稳定")
                    return
        
        time.sleep(0.2)


# ============== 调试工具 ==============
def debug_show_mask():
    """可视化检测区域"""
    mask_img = Image.fromarray((POLYGON_MASK * 255).astype(np.uint8))
    mask_img.show()

# ============== 核心功能 ==============
def smart_click(x, y, delay=0.5):
    """边界检查"""
    # 确保点击位置在屏幕范围内
    screen_w, screen_h = pyautogui.size()
    x = max(0, min(x, screen_w-1))
    y = max(0, min(y, screen_h-1))
    
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click()
    time.sleep(delay)

def find_color_pos(target_color):
    """颜色定位"""
    img = ImageGrab.grab(bbox=POLYGON_BBOX)
    img_np = np.array(img)
    
    # 精确颜色匹配（RGB完全一致）
    r, g, b = target_color
    exact_match = (
        (img_np[:, :, 0] == r) & 
        (img_np[:, :, 1] == g) & 
        (img_np[:, :, 2] == b)
    )
    valid_mask = exact_match & POLYGON_MASK
    
    # 保存调试图像
    # debug_img = img.copy()
    # debug_draw = ImageDraw.Draw(debug_img)
    y_idx, x_idx = np.where(valid_mask)
    # for x, y in zip(x_idx, y_idx):
    #     debug_draw.rectangle([x-2, y-2, x+2, y+2], outline="red")
    # debug_img.save("color_debug.png")
    
    # 返回结果
    if len(x_idx) == 0:
        return None
    return (
        int(np.median(x_idx)) + POLYGON_BBOX[0],
        int(np.median(y_idx)) + POLYGON_BBOX[1]
    )
def is_point_in_polygon(point, polygon):
    """判断点位是否在多边形内"""
    x, y = point
    n = len(polygon)
    inside = False
    
    px1, py1 = polygon[0]
    for i in range(n+1):
        px2, py2 = polygon[i % n]
        if y > min(py1, py2):
            if y <= max(py1, py2):
                if x <= max(px1, px2):
                    if py1 != py2:
                        xints = (y - py1) * (px2 - px1) / (py2 - py1) + px1
                    if px1 == px2 or x <= xints:
                        inside = not inside
        px1, py1 = px2, py2
    return inside

def get_polygon_center(polygon):
    """计算多边形中心点"""
    x = [p[0] for p in polygon]
    y = [p[1] for p in polygon]
    return (int(np.mean(x)), int(np.mean(y)))

def smart_drag(center):
    """拖动屏幕以免出现回复消息不在画面内"""
    drag_start = center
    drag_end = (drag_start[0], drag_start[1] - DRAG_DISTANCE)
    
    pyautogui.moveTo(drag_start, duration=0.2)
    pyautogui.dragTo(drag_end, button='left', duration=DRAG_DURATION)
    time.sleep(0.5)  # 拖动后缓冲

def check_pixel_color(pos, target_color, tolerance=0):
    """精确检查指定坐标颜色"""
    x, y = pos
    img = ImageGrab.grab(bbox=(x, y, x+1, y+1))  # 截取单像素
    pixel = img.getpixel((0, 0))
    
    # 计算颜色差异
    diff = sum(abs(p - t) for p, t in zip(pixel, target_color))
    return diff <= tolerance * 3  # 允许各通道累计差异

# ============== 主流程 ==============
def main():
    try:
        while True:
            print("\n===== 新一轮循环开始 =====")
            
            # 阶段1: 点击
            print("🚀 执行初始点击")
            for x, y in INITIAL_CLICKS:
                pyautogui.click(x, y)
                time.sleep(1)

            # 阶段2: 并行检测
            stabilization_history = []
            stable_counter = 0
            poly_center = get_polygon_center(POLYGON_POINTS)

            while True:
                # 实时截图处理
                current_frame = np.array(ImageGrab.grab(bbox=POLYGON_BBOX).convert('L'))
                masked_frame = current_frame * POLYGON_MASK
                
                # 画面变化检测
                stabilization_history.append(masked_frame)
                if len(stabilization_history) > 5:
                    stabilization_history.pop(0)
                
                if len(stabilization_history) >= 2:
                    diff = np.mean(np.abs(stabilization_history[-1].astype(float) - 
                                  stabilization_history[-2].astype(float)) / 255)
                    if diff <= 0.001:  # 符合稳定条件
                        stable_counter += 1
                        print(f"稳定进度：{stable_counter}/10")
                        if stable_counter >= 10:
                            print("✅ 区域已稳定")
                            # 稳定后执行最终操作
                            print("⚠️ 未发现目标颜色，执行最终点击")
                            smart_click(*FINAL_CLICK)
                            break
                    else:
                        stable_counter = 0
                        print(f"画面变化：{diff*100:.2f}%")
                
                # 持续颜色检测
                a_pos = find_color_pos(COLOR_A)
                if a_pos:
                    click_point = (a_pos[0], a_pos[1] + Y_OFFSET)
                    print(f"✅ 实时发现颜色A @ {a_pos}，目标点击位置：{click_point}")

                    if not is_point_in_polygon(click_point, POLYGON_POINTS):
                        print("⚠️ 点击位置超出检测区域，执行拖动")
                        smart_drag(poly_center)
                        # 重置检测状态
                        stabilization_history = []
                        stable_counter = 0
                        time.sleep(1.5)  # 增加等待时间确保拖动完成
                        continue
                        
                    smart_click(*click_point)
                    stabilization_history = []
                    stable_counter = 0
                    continue
                
                b_pos = find_color_pos(COLOR_B)
                if b_pos:
                    print(f"🔥 实时发现颜色B @ {b_pos}")
                    smart_click(*b_pos)
                    
                    # 执行后续点击序列
                    click_index = 0
                    while click_index < len(FOLLOWUP_CLICKS):
                        x, y, delay = FOLLOWUP_CLICKS[click_index]
                        
                        smart_click(x, y, delay)
                        
                        # 防止进入剧情后黑屏过长退出无效
                        if click_index == 1:
                            check_pos = FOLLOWUP_CLICKS[click_index+1][:2]
                            print(f"🔍 开始验证位置 {check_pos} 的颜色")
                            
                            # 循环验证直到颜色符合
                            while not check_pixel_color(check_pos, CHECK_COLOR, CHECK_TOLERANCE):
                                print("⚠️ 颜色验证未通过，重新执行上一步")
                                smart_click(x, y, delay)
                                time.sleep(1)
                            
                            print("✅ 颜色验证通过")
                        
                        click_index += 1

                    break
                
                time.sleep(0.2)  # 检测间隔

            print("等待1.5秒开始下一轮...")
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n🛑 操作已中断")


if __name__ == "__main__":
    # 调试时取消注释以下内容
    # debug_show_mask()
    main()