#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派 5 LED 同步触发控制端 (适配 SPI 驱动)
用途：同步发送触发脉冲并切换 WS2812B 颜色
接线：WS2812B DIN -> 树莓派 GPIO 10 (SPI0 MOSI, 物理引脚19)
      触发信号 -> 树莓派 GPIO 17 (物理引脚11)
"""
import time
import board
import neopixel_spi as neopixel
from gpiozero import DigitalOutputDevice

# ================= 配置参数 =================
TRIGGER_OUT_PIN = 17    # 触发输出引脚
LED_COUNT = 256         # 软屏总像素数
TOTAL_DURATION = 15.0   # 总运行时间 (秒)
INTERVAL = 0.1          # 切换间隔 (0.1秒 = 10Hz)

# 【安全锁】最高亮度强制设为 0.2 (20%)，防止烧毁树莓派
SAFE_BRIGHTNESS = 0.2
# ============================================

# 严格定义 R-G-B 序列及对应的名称，方便终端显示
COLOR_SEQUENCE = [
    {"name": "🔴 红 (R)", "rgb": (255, 0, 0)},
    {"name": "🟢 绿 (G)", "rgb": (0, 255, 0)},
    {"name": "🔵 蓝 (B)", "rgb": (0, 0, 255)}
]

def get_center_block_indices():
    """获取 16x16 矩阵中心 4x4 (16个灯) 的索引号"""
    indices = []
    # 提取中心区域 (第 6~9 行，第 6~9 列)
    for row in range(6, 10):
        for col in range(6, 10):
            idx = row * 16 + col
            if idx < 256:
                indices.append(idx)
    return indices

def sync_led_and_trigger():
    trigger_pin = DigitalOutputDevice(TRIGGER_OUT_PIN, initial_value=False)
    
    spi = board.SPI()
    pixels = neopixel.NeoPixel_SPI(spi, LED_COUNT, pixel_order=neopixel.GRB, auto_write=False)
    pixels.brightness = SAFE_BRIGHTNESS 

    print("="*50)
    print(" 💡 树莓派 R-G-B 同步触发系统 (安全低功耗版) ")
    print(f" ⏱️ 频率: {1/INTERVAL:.1f}Hz | 时长: {TOTAL_DURATION}s")
    print(" ⚠️ 警告：已强制限制只点亮中心 4x4 区域！")
    print("="*50)

    start_time = time.time()
    next_trigger_time = start_time
    pulse_count = 0
    seq_idx = 0
    
    # 获取要点亮的 16 个像素索引
    target_pixels = get_center_block_indices()

    try:
        while time.time() - start_time < TOTAL_DURATION:
            # 获取当前周期应该显示的颜色字典
            current_color_info = COLOR_SEQUENCE[seq_idx]
            color_rgb = current_color_info["rgb"]
            color_name = current_color_info["name"]
            
            # 1. 内存清零 (先把所有灯设为黑色，不输出)
            for i in range(LED_COUNT):
                pixels[i] = (0, 0, 0)
                
            # 2. 内存中将 4x4 区域设为当前颜色
            for i in target_pixels:
                pixels[i] = color_rgb
            
            # 3. 同步原点：拉高 Trigger 信号 (向相机报告：马上要变色了！)
            trigger_pin.on()
            
            # 4. 执行点亮：将数据推送到软屏 (伴随微秒级硬件延迟)
            pixels.show() 
            
            # 5. 结束脉冲：拉低 Trigger
            trigger_pin.off()
            
            pulse_count += 1
            
            # 终端进度打印 (增加当前颜色显示)
            elapsed = time.time() - start_time
            print(f"   进度: {elapsed:>4.1f}/{TOTAL_DURATION}s | 脉冲: {pulse_count:>3} | 当前颜色: {color_name}  ", end="\r")

            # 指向下一个颜色 (0->1->2->0 循环)
            seq_idx = (seq_idx + 1) % len(COLOR_SEQUENCE)

            # 时间漂移补偿与休眠
            next_trigger_time += INTERVAL
            sleep_time = next_trigger_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        print(f"\n\n✅ 运行完成！共发送 {pulse_count} 个脉冲，完美循环 R-G-B。")

    except KeyboardInterrupt:
        print(f"\n\n⚠️ 用户手动终止。")
    finally:
        trigger_pin.close()
        # 退出时务必安全清零所有灯
        for i in range(LED_COUNT):
            pixels[i] = (0, 0, 0)
        pixels.show()
        print("👋 软屏已安全熄灭，GPIO 释放。")

if __name__ == "__main__":
    sync_led_and_trigger()
