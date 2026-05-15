# 第一步
sudo dtoverlay genx320
# 第二步
./rp5_setup_v4l.sh
# 第三步
metavision_viewer


# 录制
metavision_viewer -o wenjianming.raw      按空格键开始录制，然后按空格键便停止录制了


# 播放
metavision_viewer =i wenjianming.raw
