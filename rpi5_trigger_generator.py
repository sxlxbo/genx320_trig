#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
树莓派5 GPIO触发信号生成器
功能：
1. 按键触发：按's'键发一个脉冲
2. 自动触发：每隔2秒自动发一个脉冲
"""
import RPi.GPIO as GPIO
import time
import sys

# 引脚配置（用物理引脚编号，对应树莓派Pin11）
TRIGGER_PIN = 11  # 物理引脚11 = BCM GPIO17

def setup_gpio():
    """初始化GPIO"""
    GPIO.setmode(GPIO.BOARD)  # 用物理引脚编号
    GPIO.setup(TRIGGER_PIN, GPIO.OUT, initial=GPIO.LOW)  # 初始低电平
    print("✅ 树莓派GPIO初始化完成")
    print(f"   触发引脚：物理Pin {TRIGGER_PIN} (GPIO17)")
    print(f"   输出电平：3.3V (初始低电平)")

def send_trigger_pulse():
    """发送一个触发脉冲（上升沿+1ms高电平+下降沿）"""
    GPIO.output(TRIGGER_PIN, GPIO.HIGH)  # 上升沿（低→高）
    time.sleep(0.001)  # 高电平持续1ms（1000μs）
    GPIO.output(TRIGGER_PIN, GPIO.LOW)   # 下降沿（高→低）
    print(f"🎉 树莓派已发送触发脉冲！时间：{time.strftime('%H:%M:%S')}")

def key_trigger_mode():
    """按键触发模式：按's'发脉冲，按'q'退出"""
    print("\n🔍 按键触发模式：")
    print("   按 's' 键 → 发送触发脉冲")
    print("   按 'q' 键 → 退出程序")
    try:
        while True:
            # 简单的键盘检测（无需额外库）
            import select
            if select.select([sys.stdin], [], [], 0.1)[0]:
                key = sys.stdin.read(1)
                if key == 's':
                    send_trigger_pulse()
                elif key == 'q':
                    print("\n⚠️ 用户退出")
                    break
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")

def auto_trigger_mode(interval=2):
    """自动触发模式：每隔interval秒自动发脉冲"""
    print(f"\n🔍 自动触发模式：每隔 {interval} 秒自动发送脉冲")
    print("   按 Ctrl+C 退出")
    try:
        while True:
            send_trigger_pulse()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断")

if __name__ == "__main__":
    try:
        setup_gpio()
        # 选择模式：1=按键触发，2=自动触发
        mode = input("\n请选择触发模式 (1=按键触发, 2=自动触发): ").strip()
        if mode == '1':
            key_trigger_mode()
        elif mode == '2':
            interval = input("请输入自动触发间隔（秒，默认2）: ").strip()
            interval = float(interval) if interval else 2
            auto_trigger_mode(interval)
        else:
            print("❌ 无效选择，退出")
    finally:
        GPIO.cleanup()  # 清理GPIO资源
        print("✅ GPIO资源已释放")
