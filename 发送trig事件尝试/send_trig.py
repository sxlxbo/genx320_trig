#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派 5 外部触发脉冲发送端 (适配 gpiozero)
用途：向事件相机发送精确的上升沿脉冲
"""
import time
from gpiozero import DigitalOutputDevice

# 配置发送脉冲的 GPIO 引脚 (BCM 编码)
TRIGGER_OUT_PIN = 17
# 脉冲保持高电平的持续时间（秒），1毫秒 (0.001s) 对相机来说已经足够长且稳定
PULSE_WIDTH = 0.001 

def setup_pin(pin_num):
    """初始化输出引脚，默认拉低（低电平）"""
    print(f"🔌 初始化 GPIO {pin_num} 为输出模式，默认低电平...")
    # initial_value=False 确保引脚一上来就是 0V，避免开机毛刺
    return DigitalOutputDevice(pin_num, initial_value=False)

def send_trigger_pulse(pin_obj):
    """发送一次单发脉冲（上升沿 -> 等待 -> 下降沿）"""
    print("  ⬆️ 拉高电平 (Rising Edge)...")
    pin_obj.on()  # 触发上升沿
    
    time.sleep(PULSE_WIDTH)  # 保持高电平
    
    print("  ⬇️ 拉低电平 (Falling Edge)...")
    pin_obj.off() # 恢复低电平

if __name__ == "__main__":
    print("="*45)
    print(" 🎯 树莓派 5 脉冲发送器 (GenX320 测试专用) ")
    print("="*45)
    print(f"配置信息:")
    print(f" - 输出引脚: GPIO {TRIGGER_OUT_PIN}")
    print(f" - 脉冲宽度: {PULSE_WIDTH * 1000} ms")
    print("="*45)
    
    # 初始化引脚
    trigger_pin = setup_pin(TRIGGER_OUT_PIN)
    
    try:
        pulse_count = 0
        while True:
            # 交互式提示，按回车发送脉冲
            cmd = input("\n👉 按 [Enter] 键发送一次触发脉冲 (输入 'q' 退出): ")
            
            if cmd.lower() == 'q':
                break
                
            pulse_count += 1
            print(f"\n[第 {pulse_count} 次触发]")
            send_trigger_pulse(trigger_pin)
            print("✅ 脉冲发送完毕！(此时你的接收端脚本应该开始 30 秒倒计时了)")
            
    except KeyboardInterrupt:
        print("\n⚠️ 用户手动退出")
    finally:
        # 退出时清理引脚状态
        trigger_pin.close()
        print("👋 GPIO 资源已释放。")
