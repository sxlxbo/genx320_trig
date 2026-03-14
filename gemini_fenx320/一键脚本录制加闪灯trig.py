import time
import metavision_hal
from gpiozero import LED

def run_hyperspectral_experiment(output_filename="experiment_01.raw", duration_sec=5):
    # ==========================================
    # 1. 硬件初始化准备
    # ==========================================
    print(">>> 正在初始化硬件...")
    # 初始化 LED 和 Trig 引脚
    cam_trig = LED(17)
    led_red = LED(18)
    led_grn = LED(22)
    led_blu = LED(23)
    led_sequence = [led_red, led_grn, led_blu]
    
    # 确保初始状态全部关闭
    for led in led_sequence: led.off()
    cam_trig.off()

    # 初始化相机
    try:
        device = metavision_hal.DeviceDiscovery.open("")
    except Exception as e:
        print(f"❌ 相机打开失败: {e}")
        return

    # 注入 Bias 参数
    i_ll_biases = device.get_i_ll_biases()
    if i_ll_biases:
        i_ll_biases.set("bias_refr", 0)       
        i_ll_biases.set("bias_diff_on", 45)   
        i_ll_biases.set("bias_diff_off", 45)  

    # 开启外部触发通道
    i_trigger_in = device.get_i_trigger_in()
    if i_trigger_in: i_trigger_in.enable(0)

    # ==========================================
    # 2. 启动相机录制 (后台进行)
    # ==========================================
    i_events_stream = device.get_i_events_stream()
    i_device_control = device.get_i_device_control()
    
    i_events_stream.log_raw_data(output_filename)
    i_events_stream.start()
    i_device_control.start()
    
    print(f"\n⏺️  相机已开始录制，后台等待中...")
    # 给相机0.5秒的缓冲时间，确保录制线程已经完全稳妥地跑起来了
    time.sleep(0.5) 

    # ==========================================
    # 3. 开始精准同步打光 (主线程接管)
    # ==========================================
    print(f"▶️  开始 LED 轮询，发射同步 Trig 信号，持续 {duration_sec} 秒...")
    
    start_time = time.time()
    try:
        # 在规定时间内不断循环
        while (time.time() - start_time) < duration_sec:
            for current_led in led_sequence:
                # 关闭所有
                for led in led_sequence: led.off()
                cam_trig.off()
                
                # 同步开启
                current_led.on()
                cam_trig.on()
                
                # 维持脉冲 1ms
                time.sleep(0.001)
                cam_trig.off()
                
                # 维持光照 49ms
                time.sleep(0.049)
                
    except KeyboardInterrupt:
        print("\n⚠️ 手动强制中断！")
    
    # ==========================================
    # 4. 安全收尾
    # ==========================================
    # 关灯
    for led in led_sequence: led.off()
    cam_trig.off()
    
    # 关相机
    i_device_control.stop()
    i_events_stream.stop()
    print(f"\n⏹️  实验结束！数据已完美对齐并保存在: {output_filename}")

if __name__ == '__main__':
    # 运行一次完整的 10 秒钟实验
    run_hyperspectral_experiment("sync_test_rgb_01.raw", 10)
