import time
import metavision_hal

def record_hyperspectral_raw(output_filename="hyperspectral_sample_01.raw", record_time_sec=10):
    print(f"正在初始化 GenX320 相机...")
    try:
        device = metavision_hal.DeviceDiscovery.open("")
    except Exception as e:
        print(f"相机打开失败: {e}")
        return

    # 1. 获取 Bias 接口
    i_ll_biases = device.get_i_ll_biases()
    if i_ll_biases:
        # [新增调试功能] 打印修改前的默认参数，供你参考
        print("\n--- GenX320 原始 Bias 参数 ---")
        for bias_name in ["bias_diff_on", "bias_diff_off", "bias_refr", "bias_fo", "bias_hpf"]:
            val = i_ll_biases.get(bias_name)
            print(f"{bias_name}: {val}")

        # 注入特调的数字量 Bias 参数 (针对 LED 高频闪烁)
        # 注意：这里的数值必须严格在 GenX320 的有效范围内！
        i_ll_biases.set("bias_refr", 0)       # 降到最低，追求极短死区时间
        i_ll_biases.set("bias_diff_on", 45)   # 提高阈值 (默认25，最大60)
        i_ll_biases.set("bias_diff_off", 45)  # 提高阈值 (默认28，最大50)
        # bias_fo 和 bias_hpf 暂时保持默认即可
        print("✅ 成功注入高频硬核 Bias 参数！\n")
    else:
        print("⚠️ 无法获取 Bias 控制接口！")

    # 2. 开启外部触发通道 0
    i_trigger_in = device.get_i_trigger_in()
    if i_trigger_in:
        i_trigger_in.enable(0)
        print("✅ 成功开启外部触发通道！")

    # 3. 获取数据流接口并设置录制文件
    i_events_stream = device.get_i_events_stream()
    i_device_control = device.get_i_device_control()
    
    i_events_stream.log_raw_data(output_filename)
    print(f"⏺️  准备就绪，数据将保存在: {output_filename}")

    # 4. 开始录制
    print(f"▶️  开始录制，持续 {record_time_sec} 秒... (此时你应该在另一个终端启动 LED 闪烁程序)")
    i_events_stream.start()
    i_device_control.start()

    try:
        start_time = time.time()
        while (time.time() - start_time) < record_time_sec:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n手动中断录制。")
    finally:
        # 5. 安全关闭，保存文件
        i_device_control.stop()
        i_events_stream.stop()
        print(f"⏹️  录制结束，文件已安全保存: {output_filename}")

if __name__ == '__main__':
    record_hyperspectral_raw("test_led_sync_01.raw", 10)
