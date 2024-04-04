# push_bark
一个将打印机状态实时推送到Bark的Moonraker插件

完全参考[kluoyun/push_wechat](https://github.com/kluoyun/push_wechat/blob/main/README.md) 大佬的基础上改的.感恩

![image](IMG_1036.jpg)

* 功能单一，纯粹是为了自用.
* 后续如果有可能看要不要合并一下

# 安装

```bash
wget https://raw.githubusercontent.com/lzyyauto/push_bark/main/push_bark.py -O ~/moonraker/moonraker/components/push_bark.py
sudo systemctl restart moonraker

```

# 配置

* 在moonraker.conf中加入如下配置

```cfg
[push_bark]
# Bark 推送url
base_url: https://api.day.app
# Bark 设备ID
bark_id: xxxxxxxxxx
# 消息类型
msg_type: bark
```
可以参考examples.conf 参数很简单