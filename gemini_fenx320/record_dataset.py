import time
import metavision_hal

def record_hyperspectral_raw(output_filename="hyperspectral_sample_01.raw", record_time_sec=5):
    print(f"正在初始化 GenX320 相机...")
    try:
        device = metavision_hal.DeviceDiscovery.open("")
    except Exception as e:
        print(f"相机打开失败: {e}")
        return

    # 1. 注入特调的 Bias 参数 (针对 LED 高频闪烁)
    i_ll_biases = device.get_i_ll_biases()
    if i_ll_biases:
        i_ll_biases.set("bias_fo", 1500)      # 提高响应带宽，抓取锐利跳变
        i_ll_biases.set("bias_refr", 200)     # 缩短死区时间，防止漏掉高频事件
        i_ll_biases.set("bias_diff_on", 350)  # 提高阈值，过滤底噪
        i_ll_biases.set("bias_diff_off", 350)
        print("✅ 成功注入高频硬核 Bias 参数！")

    # 2. 开启外部触发通道 0 (这是必须的，否则 .raw 里没有触发信号)
    i_trigger_in = device.get_i_trigger_in()
    if i_trigger_in:
        i_trigger_in.enable(0)
        print("✅ 成功开启外部触发通道！")

    # 3. 获取数据流接口并设置录制文件
    i_events_stream = device.get_i_events_stream()
    i_device_control = device.get_i_device_control()
    
    # 告诉底层 HAL 库，把收到的所有原始数据原封不动地写入这个 .raw 文件
    i_events_stream.log_raw_data(output_filename)
    print(f"⏺️  准备就绪，数据将保存在: {output_filename}")

    # 4. 开始录制
    print(f"▶️  开始录制，持续 {record_time_sec} 秒...")
    i_events_stream.start()
    i_device_control.start()

    try:
        start_time = time.time()
        # 保持录制状态直到达到设定时间
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
    # 你可以在这里修改保存的文件名和录制时长
    record_hyperspectral_raw("test_apple_01.raw", 10)
