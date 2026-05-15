# 第一步
sudo dtoverlay genx320
# 第二步
./rp5_setup_v4l.sh
# 第三步
metavision_viewer


# 录制
metavision_viewer -o wenjianming.raw      然后按q键或者eac键即可，不能按ctrl+c这样终止程序，文件应该没有保存


# 播放
metavision_viewer =i wenjianming.raw
