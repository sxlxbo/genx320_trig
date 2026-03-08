from metavision_core.event_io import EventsIterator
from metavision_core.event_io.raw_reader import initiate_device
from metavision_hal import TriggerInMode
import time

def setup_external_trigger():
    # 1. 初始化相机
    device = initiate_device()
    if not device:
        print("未检测到GenX320M12")
        return

    # 2. 获取触发输入接口
    trigger_in = device.get_trigger_in()
    if not trigger_in:
        print("相机不支持外部触发")
        return

    # 3. 配置触发参数（核心）
    # 触发源：默认GPIO0；触发极性：上升沿/下降沿
    trigger_in.set_mode(TriggerInMode.ON_RISING_EDGE)  # 上升沿触发
    # trigger_in.set_mode(TriggerInMode.ON_FALLING_EDGE) # 下降沿触发
    trigger_in.enable(True)  # 启用外部触发
    print("外部触发已启用：GPIO0，上升沿")

    # 4. 等待并检测触发事件
    output_file = "external_trigger_recording.raw"
    record_duration = 5  # 触发后录制5秒
    print("等待外部触发信号...")

    while True:
        # 检测是否触发
        if trigger_in.is_triggered():
            # 获取触发时间戳（微秒，相机内部时钟）
            trigger_ts = trigger_in.get_last_trigger_timestamp()
            print(f"检测到外部触发！时间戳：{trigger_ts} μs")

            # 5. 触发后开始录制事件
            device.start_recording(output_file)
            start_time = time.time()
            mv_iterator = EventsIterator.from_device(device=device)

            for evs in mv_iterator:
                if time.time() - start_time > record_duration:
                    break
                # 可在此处理事件流

            # 停止录制
            device.stop_recording()
            print(f"录制完成，文件：{output_file}")
            break

        time.sleep(0.001)  # 1ms轮询

    # 关闭设备
    device.close()

if __name__ == "__main__":
    setup_external_trigger()
