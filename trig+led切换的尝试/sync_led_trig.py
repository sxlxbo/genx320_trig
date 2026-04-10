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
LED_COUNT = 256         # 16x16 软屏
TOTAL_DURATION = 15.0   # 总运行时间 (秒)
INTERVAL = 0.1          # 切换间隔 (10Hz)
# ============================================

# 定义要循环切换的颜色 (红, 绿, 蓝, 白)
COLORS = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]

def sync_led_and_trigger():
    # 初始化触发引脚
    trigger_pin = DigitalOutputDevice(TRIGGER_OUT_PIN, initial_value=False)
    
    # 初始化 SPI NeoPixel (树莓派 5 推荐用法)
    # spi 默认使用 GPIO 10
    spi = board.SPI()
    pixels = neopixel.NeoPixel_SPI(spi, LED_COUNT, pixel_order=neopixel.GRB, auto_write=False)
    pixels.brightness = 0.2 # 限制亮度，防止烧毁

    print("="*45)
    print(" 💡 树莓派 5 光照同步触发系统 ")
    print("="*45)
    print(f"🔌 触发引脚: GPIO {TRIGGER_OUT_PIN} | LED 引脚: GPIO 10 (SPI)")
    print(f"⏳ 时长: {TOTAL_DURATION}s | 频率: {1/INTERVAL:.1f}Hz")
    print("="*45)
    print("\n🚀 开始执行同步序列 (按 Ctrl+C 提前终止)...")

    start_time = time.time()
    next_trigger_time = start_time
    pulse_count = 0
    color_idx = 0

    try:
        while time.time() - start_time < TOTAL_DURATION:
            # 1. 内存中填入下一帧颜色 (极快，不输出物理信号)
            pixels.fill(COLORS[color_idx])
            
            # 2. 拉高触发引脚，确立时间零点
            trigger_pin.on()
            
            # 3. 推送颜色数据到软屏 (~7.68ms 延迟)
            # 在推流的同时，触发引脚保持高电平，形成脉冲宽度
            pixels.show() 
            
            # 4. 拉低触发引脚，脉冲结束
            trigger_pin.off()
            
            pulse_count += 1
            color_idx = (color_idx + 1) % len(COLORS)
            
            # 终端进度打印
            elapsed = time.time() - start_time
            print(f"   正在同步... 进度: {elapsed:.1f}/{TOTAL_DURATION}s | 脉冲: {pulse_count} | 颜色: {COLORS[color_idx]}", end="\r")

            # 5. 时间漂移补偿与等待
            next_trigger_time += INTERVAL
            sleep_time = next_trigger_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)

        print(f"\n\n✅ 运行完成！共发送了 {pulse_count} 个同步脉冲并切换了颜色。")

    except KeyboardInterrupt:
        print(f"\n\n⚠️ 用户手动提前终止。")
    finally:
        # 清理资源，熄灭 LED
        trigger_pin.close()
        pixels.fill((0, 0, 0))
        pixels.show()
        print("👋 软屏已熄灭，GPIO 资源已释放。")

if __name__ == "__main__":
    sync_led_and_trigger()
