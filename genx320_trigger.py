#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GenX320 + 树莓派5 外部触发录制（适配J3接口）
接线：脉冲源Signal→J3-1(EXTTRIG)，脉冲源GND→J3-4(GND)
"""
from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device, RawReader
from metavision_hal import TriggerInMode, DeviceException
import time
import os
import sys

def init_camera():
    """初始化GenX320相机，返回设备对象"""
    try:
        # 初始化相机设备
        device = initiate_device()
        if not device:
            print("❌ 未检测到GenX320相机，请检查转接板连接！")
            sys.exit(1)
        print("✅ 相机初始化成功：GenX320M12")
        return device
    except DeviceException as e:
        print(f"❌ 相机初始化失败：{e}")
        sys.exit(1)

def configure_external_trigger(device):
    """配置外部触发（适配J3接口，映射为gpio0）"""
    try:
        # 获取触发输入接口
        trigger_in = device.get_trigger_in()
        if not trigger_in:
            print("❌ 相机不支持外部触发功能！")
            sys.exit(1)
        
        # 核心配置：J3接口映射为gpio0，上升沿触发
        trigger_in.set_source("gpio0")  # 关键：指定J3接口对应的触发源
        trigger_in.set_mode(TriggerInMode.ON_RISING_EDGE)  # 上升沿触发（可改ON_FALLING_EDGE）
        trigger_in.enable(True)  # 启用外部触发
        
        print("✅ 外部触发配置完成：")
        print(f"  - 触发源：gpio0（对应J3-1 EXTTRIG）")
        print(f"  - 触发模式：上升沿（Rising Edge）")
        print(f"  - 地线：J3-4 GND")
        return trigger_in
    except DeviceException as e:
        print(f"❌ 触发配置失败：{e}")
        sys.exit(1)

def trigger_recording(device, trigger_in):
    """等待触发信号，触发后录制事件数据"""
    # 录制参数配置
    record_duration = 30  # 触发后录制30秒（可自定义）
    save_dir = "./trigger_records"  # 录制文件保存目录
    os.makedirs(save_dir, exist_ok=True)  # 确保目录存在
    # 生成带时间戳的文件名，避免覆盖
    file_name = f"genx320_trigger_{int(time.time())}.raw"
    save_path = os.path.join(save_dir, file_name)

    print("\n🔍 等待外部触发信号（脉冲源接J3-1）...")
    print(f"   触发后将录制{record_duration}秒，文件保存至：{save_path}")
    print("   按 Ctrl+C 退出程序")

    try:
        # 循环检测触发信号（防抖：连续检测2次触发才确认）
        trigger_count = 0
        while True:
            if trigger_in.is_triggered():
                trigger_count += 1
                # 防抖：连续2次检测到触发才确认（避免毛刺误触发）
                if trigger_count >= 2:
                    # 获取触发时间戳（微秒，与事件同步）
                    trigger_ts = trigger_in.get_last_trigger_timestamp()
                    print(f"\n🎉 检测到有效触发！触发时间戳：{trigger_ts} μs")
                    
                    # 启动录制
                    print(f"📹 开始录制（{record_duration}秒）...")
                    device.start_recording(save_path)
                    start_time = time.time()

                    # 读取事件流，维持录制
                    mv_iterator = EventsIterator.from_device(device=device)
                    for evs in mv_iterator:
                        # 录制时长到则停止
                        if time.time() - start_time > record_duration:
                            break
                        # 可选：打印实时事件数（调试用）
                        # print(f"实时事件数：{len(evs)}", end="\r")

                    # 停止录制
                    device.stop_recording()
                    print(f"✅ 录制完成！文件已保存：{save_path}")
                    
                    # 读取并打印触发事件（验证）
                    verify_trigger(save_path)
                    break
            else:
                trigger_count = 0  # 未检测到触发，重置计数
            time.sleep(0.001)  # 1ms轮询，降低CPU占用

    except KeyboardInterrupt:
        print("\n⚠️ 用户终止程序")
    except Exception as e:
        print(f"❌ 录制失败：{e}")
        # 异常时确保停止录制
        if device.is_recording():
            device.stop_recording()

def verify_trigger(raw_file):
    """验证录制文件中的触发事件"""
    try:
        reader = RawReader(raw_file)
        trigger_events = reader.get_ext_trigger_events()
        if trigger_events:
            print("📊 触发事件验证：")
            for idx, (ts, polarity) in enumerate(trigger_events):
                print(f"  - 触发{idx+1}：时间戳={ts} μs，极性={polarity}")
        else:
            print("⚠️ 录制文件中未检测到触发事件，请检查接线！")
    except Exception as e:
        print(f"❌ 验证触发事件失败：{e}")

if __name__ == "__main__":
    # 主流程：初始化相机 → 配置触发 → 等待触发并录制
    device = init_camera()
    trigger_in = configure_external_trigger(device)
    trigger_recording(device, trigger_in)
    
    # 清理资源
    device.close()
    print("\n✅ 程序正常退出，相机资源已释放")
