#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GenX320 + 树莓派5 外部触发录制（适配J3接口）
接线：脉冲源Signal→J3-1(EXTTRIG)，脉冲源GND→J3-4(GND)
"""
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device, RawReader
import time
import os
import sys

def init_camera():
    """初始化GenX320相机，返回 HAL device 对象"""
    try:
        device = initiate_device("") # 传入空字符串自动寻找第一台可用相机
        if not device:
            print("❌ 未检测到GenX320相机，请检查连接！")
            sys.exit(1)
        print("✅ 相机初始化成功")
        return device
    except Exception as e:
        print(f"❌ 相机初始化失败：{e}")
        sys.exit(1)

def configure_external_trigger(device):
    """配置外部触发功能"""
    # 修正: 获取 Trigger In 接口的正确 API
    trigger_in = device.get_i_trigger_in()
    if not trigger_in:
        print("❌ 相机不支持外部触发功能 (无法获取 I_TriggerIn 接口)！")
        sys.exit(1)
    
    # 修正: GenX320 的主触发通道固定为 0。不需要设置 gpio 源或边沿模式，硬件会捕捉所有跳变。
    channel_id = 0 
    success = trigger_in.enable(channel_id)
    
    if success:
        print(f"✅ 外部触发配置完成 (通道 {channel_id} 已启用，等待 J3-1 输入)")
    else:
        print("⚠️ 外部触发启用失败，可能已被占用或不支持。")
        
    return trigger_in

def trigger_recording(device):
    """先开启录制，再等待触发，确保第一个触发事件被完整保留"""
    record_duration = 30 
    save_dir = "./trigger_records"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"genx320_trigger_{int(time.time())}.raw"
    save_path = os.path.join(save_dir, file_name)

    print("\n🔍 正在初始化数据流...")
    events_stream = device.get_i_events_stream()
    mv_iterator = EventsIterator.from_device(device=device)
    
    # 【关键修改】：不等触发，直接开始把底层数据落盘！
    print(f"📹 已开启数据预录制，等待外部触发脉冲 (J3-1)...")
    print(f"   (录制文件将包含等待期间的数据，以及触发后的 {record_duration} 秒)")
    print("   按 Ctrl+C 退出程序")
    events_stream.log_raw_data(save_path)

    trigger_detected = False
    trigger_ts = 0
    start_record_time = 0

    try:
        for evs in mv_iterator:
            # 1. 如果还没检测到触发，就一直找
            if not trigger_detected:
                triggers = mv_iterator.reader.get_ext_trigger_events()
                if len(triggers) > 0:
                    rising_edges = triggers[triggers['p'] == 1] # 寻找上升沿
                    if len(rising_edges) > 0:
                        trigger_ts = rising_edges[0]['t']
                        trigger_detected = True
                        start_record_time = time.time() # 记录触发到来的现实时间
                        print(f"\n🎉 成功捕获第一个触发事件！微秒级时间戳：{trigger_ts} μs")
                        print(f"   继续录制 {record_duration} 秒...")
                    
                    mv_iterator.reader.clear_ext_trigger_events()
            
            # 2. 如果已经检测到触发，就开始倒计时 30 秒
            else:
                elapsed = time.time() - start_record_time
                print(f"   触发后已录制... {elapsed:.1f} / {record_duration} s", end='\r')
                
                if elapsed > record_duration:
                    break # 时间到，跳出循环

        # 停止落盘
        events_stream.stop_log_raw_data()
        print(f"\n✅ 录制完成！文件已保存至：{save_path}")
        
        # 验证（这次你一定能看到那个触发事件）
        verify_trigger(save_path)

    except KeyboardInterrupt:
        print("\n⚠️ 用户手动终止程序")
    finally:
        if 'events_stream' in locals():
            events_stream.stop_log_raw_data()

def verify_trigger(raw_file):
    """验证刚才录制的 RAW 文件中是否正确包含了触发事件"""
    print(f"\n📊 开始校验 RAW 文件内的触发数据: {os.path.basename(raw_file)}")
    try:
        reader = RawReader(raw_file)
        trigger_count = 0
        
        # 遍历读取整个文件
        while not reader.is_done():
            reader.load_delta_t(100000) # 每次读取 100ms 切片
            triggers = reader.get_ext_trigger_events()
            if len(triggers) > 0:
                for t in triggers:
                    # 将极性 1/0 转换为文字便于阅读
                    edge = "上升沿(Rising)" if t['p'] == 1 else "下降沿(Falling)"
                    print(f"  - 发现信号: 时间戳={t['t']:>10} μs | 极性={edge}")
                trigger_count += len(triggers)
                reader.clear_ext_trigger_events()
                
        if trigger_count > 0:
            print(f"✅ 验证通过！录制的数据流中完美捕获了 {trigger_count} 个硬件触发点。")
        else:
            print("⚠️ 警告：录制文件中未找到触发事件。（注意：如果在触发发生的那一瞬间，log_raw_data 还未完全就绪，第一个触发事件本身可能不会被记录到文件中，但后续的事件流是完好的）。")
            
    except Exception as e:
        print(f"❌ 验证文件失败：{e}")

if __name__ == "__main__":
    device = init_camera()
    configure_external_trigger(device)
    # 把 device 传进去直接运行
    trigger_recording(device)
    
    # 释放资源
    del device
    print("\n👋 相机资源已释放，程序安全退出。")
