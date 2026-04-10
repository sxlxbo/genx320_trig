#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GenX320 + 树莓派5 外部触发录制（适配LED同步实验）
接线：脉冲源(GPIO 17) -> J3-1(EXTTRIG)，树莓派GND -> J3-4(GND)
"""
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device, RawReader
import time
import os
import sys

def init_camera():
    try:
        device = initiate_device("") 
        if not device:
            print("❌ 未检测到GenX320相机，请检查连接！")
            sys.exit(1)
        print("✅ 相机初始化成功")
        return device
    except Exception as e:
        print(f"❌ 相机初始化失败：{e}")
        sys.exit(1)

def configure_external_trigger(device):
    trigger_in = device.get_i_trigger_in()
    if not trigger_in:
        print("⚠️ 未检测到软件触发开关，进入底层硬件直通模式。")
        return None
    channel_id = 0 
    if trigger_in.enable(channel_id):
        print(f"✅ 外部触发配置完成 (通道 {channel_id} 已启用)")
    return trigger_in

def trigger_recording(device):
    record_duration = 15 # 与发送端的时间保持一致或略长
    save_dir = "./trigger_records"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"genx320_led_sync_{int(time.time())}.raw"
    save_path = os.path.join(save_dir, file_name)

    print("\n🔍 正在初始化数据流...")
    events_stream = device.get_i_events_stream()
    mv_iterator = EventsIterator.from_device(device=device)
    
    print(f"📹 已开启数据预录制，等待第一个 LED 同步脉冲 (J3-1)...")
    events_stream.log_raw_data(save_path)

    trigger_detected = False
    start_record_time = 0

    try:
        for evs in mv_iterator:
            if not trigger_detected:
                triggers = mv_iterator.reader.get_ext_trigger_events()
                if len(triggers) > 0:
                    rising_edges = triggers[triggers['p'] == 1]
                    if len(rising_edges) > 0:
                        trigger_ts = rising_edges[0]['t']
                        trigger_detected = True
                        start_record_time = time.time()
                        print(f"\n🎉 捕获首个 LED 切换脉冲！基准时间戳：{trigger_ts} μs")
                        print(f"   继续录制 {record_duration} 秒...")
                    mv_iterator.reader.clear_ext_trigger_events()
            else:
                elapsed = time.time() - start_record_time
                print(f"   同步录制中... {elapsed:.1f} / {record_duration} s", end='\r')
                if elapsed > record_duration:
                    break 

        events_stream.stop_log_raw_data()
        print(f"\n✅ 录制完成！文件已保存至：{save_path}")
        verify_trigger(save_path)

    except KeyboardInterrupt:
        print("\n⚠️ 用户手动终止程序")
    finally:
        if 'events_stream' in locals():
            events_stream.stop_log_raw_data()

def verify_trigger(raw_file):
    print(f"\n📊 开始校验 RAW 文件内的触发点: {os.path.basename(raw_file)}")
    try:
        reader = RawReader(raw_file)
        trigger_count = 0
        while not reader.is_done():
            reader.load_delta_t(100000) 
            triggers = reader.get_ext_trigger_events()
            if len(triggers) > 0:
                trigger_count += len(triggers)
                reader.clear_ext_trigger_events()
        if trigger_count > 0:
            print(f"✅ 验证通过！完美捕获了 {trigger_count} 个硬件触发点。")
        else:
            print("⚠️ 警告：录制文件中未找到触发事件。")
    except Exception as e:
        print(f"❌ 验证文件失败：{e}")

if __name__ == "__main__":
    device = init_camera()
    configure_external_trigger(device)
    trigger_recording(device)
    del device
    print("\n👋 资源释放，安全退出。")
