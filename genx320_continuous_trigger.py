#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GenX320 + 树莓派5：连续触发录制模式
功能：
1. 第一次触发：开始全程录制
2. 后续每次触发：标记触发时间戳（不中断录制）
3. 按 'q' 键：停止录制并退出
接线：树莓派Pin11→GenX320 J3-1，Pin9→J3-4
"""
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device, RawReader
from metavision_hal import TriggerInMode, DeviceException
import time
import os
import sys
import select

def init_camera():
    """初始化GenX320相机"""
    try:
        device = initiate_device()
        if not device:
            print("❌ 未检测到GenX320相机，请检查连接！")
            sys.exit(1)
        print("✅ 相机初始化成功：GenX320M12")
        return device
    except DeviceException as e:
        print(f"❌ 相机初始化失败：{e}")
        sys.exit(1)

def configure_external_trigger(device):
    """配置外部触发（适配J3接口）"""
    try:
        trigger_in = device.get_trigger_in()
        if not trigger_in:
            print("❌ 相机不支持外部触发！")
            sys.exit(1)
        
        trigger_in.set_source("gpio0")  # J3接口映射为gpio0
        trigger_in.set_mode(TriggerInMode.ON_RISING_EDGE)  # 上升沿触发
        trigger_in.enable(True)
        
        print("✅ 外部触发配置完成：")
        print(f"  - 触发源：gpio0（J3-1 EXTTRIG）")
        print(f"  - 触发模式：上升沿")
        print(f"  - 地线：J3-4 GND")
        return trigger_in
    except DeviceException as e:
        print(f"❌ 触发配置失败：{e}")
        sys.exit(1)

def check_key_press():
    """非阻塞检测键盘输入（按q退出）"""
    dr, dw, de = select.select([sys.stdin], [], [], 0.01)
    if dr:
        key = sys.stdin.read(1)
        return key.lower() == 'q'
    return False

def continuous_trigger_recording(device, trigger_in):
    """连续触发录制：第一次触发开始，按q停止"""
    # 录制文件配置
    save_dir = "./continuous_records"
    os.makedirs(save_dir, exist_ok=True)
    file_name = f"genx320_continuous_{int(time.time())}.raw"
    save_path = os.path.join(save_dir, file_name)

    print("\n🔍 等待第一次外部触发信号...")
    print("   第一次触发后开始全程录制")
    print("   后续每次触发会在事件流中标记时间戳")
    print("   按 'q' 键停止录制并退出\n")

    # 状态变量
    is_recording = False
    trigger_count = 0
    mv_iterator = None

    try:
        while True:
            # 1. 检测是否按q键
            if check_key_press():
                if is_recording:
                    print("\n⚠️ 检测到 'q' 键，正在停止录制...")
                    device.stop_recording()
                    print(f"✅ 录制完成！文件保存至：{save_path}")
                    # 验证触发事件
                    verify_triggers(save_path)
                else:
                    print("\n⚠️ 未开始录制，直接退出")
                break

            # 2. 检测触发信号
            if trigger_in.is_triggered():
                trigger_ts = trigger_in.get_last_trigger_timestamp()
                trigger_count += 1

                if not is_recording:
                    # 第一次触发：开始录制
                    print(f"🎉 第1次触发！开始全程录制...")
                    print(f"   触发时间戳：{trigger_ts} μs")
                    device.start_recording(save_path)
                    is_recording = True
                    # 启动事件流读取（维持录制）
                    mv_iterator = EventsIterator.from_device(device=device)
                else:
                    # 后续触发：仅标记时间戳
                    print(f"✅ 第{trigger_count}次触发！时间戳：{trigger_ts} μs")

            # 3. 读取事件流（维持录制状态，必须有这一步）
            if is_recording and mv_iterator is not None:
                try:
                    next(mv_iterator)
                except StopIteration:
                    pass

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序")
        if is_recording:
            device.stop_recording()
            print(f"✅ 录制已停止，文件保存至：{save_path}")
    except Exception as e:
        print(f"❌ 录制失败：{e}")
        if is_recording:
            device.stop_recording()

def verify_triggers(raw_file):
    """验证录制文件中的所有触发事件"""
    try:
        reader = RawReader(raw_file)
        trigger_events = reader.get_ext_trigger_events()
        if trigger_events:
            print(f"\n📊 触发事件验证（共{len(trigger_events)}次）：")
            for idx, (ts, polarity) in enumerate(trigger_events):
                print(f"  - 触发{idx+1}：时间戳={ts} μs，极性={polarity}")
        else:
            print("\n⚠️ 录制文件中未检测到触发事件，请检查接线！")
    except Exception as e:
        print(f"❌ 验证触发事件失败：{e}")

if __name__ == "__main__":
    # 主流程
    device = init_camera()
    trigger_in = configure_external_trigger(device)
    continuous_trigger_recording(device, trigger_in)
    device.close()
    print("\n✅ 程序正常退出，相机资源已释放")
