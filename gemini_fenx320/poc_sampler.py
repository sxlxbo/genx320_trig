from gpiozero import LED
import time

# 1. 映射引脚 (使用 BCM 编号)
cam_trig = LED(17) # 接相机的 EXT_TRIG
led_red = LED(18)  # 接红光 LED
led_grn = LED(22)  # 接绿光 LED
led_blu = LED(23)  # 接蓝光 LED

# 将要轮询的 LED 放入列表
led_sequence = [led_red, led_grn, led_blu]

print("初始化完成。即将开始 LED 轮询与相机触发验证...")
print("按 Ctrl+C 停止运行")

try:
    while True:
        for current_led in led_sequence:
            # --- 阶段 A：状态重置 ---
            # 确保所有灯和触发引脚都是关闭的
            for led in led_sequence:
                led.off()
            cam_trig.off()
            
            # --- 阶段 B：高保真同步开启 ---
            # 瞬间同时点亮当前颜色的 LED，并向相机发送触发信号 (拉高电平)
            current_led.on()
            cam_trig.on()
            
            # --- 阶段 C：维持触发脉冲 ---
            # 保持触发引脚高电平 1 毫秒 (这足够 GenX320 识别到一个有效的外同步脉冲了)
            time.sleep(0.001) 
            cam_trig.off() # 脉冲发送完毕，拉低相机触发引脚
            
            # --- 阶段 D：维持光照并等待 ---
            # 继续保持当前 LED 亮起 49 毫秒，让相机在这段时间内捕捉因为换灯产生的光强跳变事件
            # (1ms 触发 + 49ms 亮起 = 50ms 一个周期)
            time.sleep(0.049) 

except KeyboardInterrupt:
    print("\n收到停止指令，正在关闭所有硬件...")
    for led in led_sequence:
        led.off()
    cam_trig.off()
    print("安全退出，验证结束。")
