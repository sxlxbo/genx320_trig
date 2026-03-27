#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派 5 连续外部触发脉冲发送端
用途：按固定时间间隔持续发送脉冲（带时间漂移补偿）
"""
import time
from gpiozero import DigitalOutputDevice

# ================= 配置参数 =================
TRIGGER_OUT_PIN = 17    # 输出脉冲的 GPIO 引脚 (BCM 编码)
TOTAL_DURATION = 15.0   # 总发送时长（秒）
INTERVAL = 0.1          # 脉冲发送间隔（秒），0.1秒 = 10Hz 频率
PULSE_WIDTH = 0.001     # 每次脉冲保持高电平的时间（1 毫秒）
# ============================================

def send_continuous_pulses(pin_num, duration, interval, pulse_width):
    """在规定时间内，以固定间隔发送脉冲"""
    # 初始化引脚，默认拉低
    trigger_pin = DigitalOutputDevice(pin_num, initial_value=False)
    
    print("="*45)
    print(" ⏱️ 树莓派 5 自动脉冲发送器 (GenX320 测试) ")
    print("="*45)
    print(f"🔌 GPIO 引脚: {pin_num}")
    print(f"⏳ 总运行时长: {duration} 秒")
    print(f"⏱️ 发送频率: {1/interval:.1f} Hz (每 {interval} 秒一次)")
    print(f"📐 脉冲宽度: {pulse_width * 1000} ms")
    print("="*45)
    print("\n🚀 开始发送脉冲 (按 Ctrl+C 可提前终止)...")

    start_time = time.time()
    next_trigger_time = start_time
    pulse_count = 0

    try:
        # 只要当前时间还没超过总时长，就继续发
        while time.time() - start_time < duration:
            # 1. 发送一次脉冲
            trigger_pin.on()
            time.sleep(pulse_width)
            trigger_pin.off()
            pulse_count += 1
            
            # 终端进度打印（使用 \r 覆盖同一行，避免刷屏）
            elapsed = time.time() - start_time
            print(f"   正在发送... 进度: {elapsed:.1f}/{duration}s | 已发送: {pulse_count} 个", end="\r")

            # 2. 计算下一次应该触发的绝对时间（核心：防止时间漂移）
            next_trigger_time += interval
            
            # 3. 计算需要休眠多久才能到达下一次触发时间
            sleep_time = next_trigger_time - time.time()
            
            # 如果 sleep_time 大于 0，说明时间充裕，进行休眠；
            # 如果小于 0，说明系统卡顿导致代码执行超时了，直接进入下一次循环追赶进度
            if sleep_time > 0:
                time.sleep(sleep_time)

        print(f"\n\n✅ 发送完成！在 {duration} 秒内共成功发送了 {pulse_count} 个脉冲。")

    except KeyboardInterrupt:
        print(f"\n\n⚠️ 用户手动提前终止。已发送 {pulse_count} 个脉冲。")
    finally:
        # 退出时务必清理引脚状态
        trigger_pin.close()
        print("👋 GPIO 资源已释放，引脚已恢复安全电平。")

if __name__ == "__main__":
    send_continuous_pulses(TRIGGER_OUT_PIN, TOTAL_DURATION, INTERVAL, PULSE_WIDTH)
