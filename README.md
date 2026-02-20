# 初叶🍂 MetingAPI 点歌插件

基于 MetingAPI 的点歌插件，支持QQ音乐、网易云、酷狗、酷我等音源。

**当前版本：v1.0.3**

## 功能特性

- 支持多音源：QQ音乐、网易云、酷狗、酷我
- 会话级音源切换，不影响其他会话
- 智能语音分段发送，自动处理超过2分钟的歌曲
- 简单易用的命令交互
- 支持自定义 API 模板，最大限度兼容各种 MetingAPI

## 安装

1. （1）将插件目录 `astrbot_plugin_meting` 放入 AstrBot 的 `data/plugins` 目录
（2）WebUI中从链接安装:https://github.com/chuyegzs/astrbot_plugin_meting
2. 在 AstrBot WebUI 的插件管理处启用该插件
3. 在插件配置中设置 MetingAPI 模板

## 配置

在 AstrBot WebUI 的插件配置页面中，设置以下参数：

### MetingAPI 模板
- **描述**：MetingAPI 调用模板，使用占位符替换参数
- **占位符**：
  - `:server` - 音源（tencent/netease/kugou/kuwo）
  - `:type` - 请求类型（search/url/pic/lrc等）
  - `:id` - 搜索关键词或歌曲ID
  - `:r` - 随机数（自动生成时间戳）
- **示例**：`https://api.i-meto.com/meting/api?server=:server&type=:type&id=:id&r=:r`
- **初叶🍂免费音源（会员状态直接访问https://musicapi.chuyel.top）**：`https://musicapi.chuyel.top/meting/api?server=:server&type=:type&id=:id&r=:r`

### 默认音源
- **描述**：默认使用的音乐平台
- **可选值**：
  - `tencent` - QQ音乐
  - `netease` - 网易云音乐
  - `kugou` - 酷狗音乐
  - `kuwo` - 酷我音乐
- **默认值**：`netease`

### 搜索结果显示数量
- **描述**：搜索结果显示的歌曲数量
- **可选值**：5-30（整数）
- **默认值**：10

## 使用方法

### 切换音源

在当前会话中切换音乐平台，不影响其他会话：

- `切换QQ音乐` - 切换到QQ音乐
- `切换网易云` - 切换到网易云
- `切换酷狗` - 切换到酷狗
- `切换酷我` - 切换到酷我

### 搜索歌曲

使用当前会话的音源搜索歌曲：

```
搜歌 一期一会
```

搜索后会显示歌曲列表，包含歌曲名和歌手信息（显示数量可在后台配置，默认10首）。

### 播放歌曲

在搜索结果后，使用以下命令播放指定序号的歌曲：

```
点歌 1
```

其中 `1` 是歌曲序号，可以是搜索结果中的任意序号（如：点歌 1、点歌 2、点歌 3...）。

**注意**：`点歌` 和数字之间必须有空格。

插件会自动：
1. 获取歌曲播放地址
2. 下载歌曲文件
3. 如果歌曲时长超过2分钟，自动分段录制
4. 逐段发送语音消息
5. 播放完成后提示

## 依赖

插件需要以下依赖库（会在安装插件时自动安装）：

- `aiohttp>=3.8.0` - 异步 HTTP 请求
- `pydub>=0.25.1` - 音频处理

**注意**：`pydub` 需要系统安装 FFmpeg。请确保系统已安装 FFmpeg 并在 PATH 中。

### FFmpeg 安装

**Windows:**
```bash
# 使用 winget
winget install ffmpeg

# 或手动下载：https://ffmpeg.org/download.html
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

## 技术说明

### 音源映射

| 用户输入 | API 参数 |
|---------|---------|
| QQ音乐 | tencent |
| 网易云 | netease |
| 酷狗 | kugou |
| 酷我 | kuwo |

### API 模板示例

不同 MetingAPI 服务的模板格式可能不同，以下是常见格式：

**标准格式：**
```
https://api.example.com/meting/api?server=:server&type=:type&id=:id&r=:r
```

**简化格式：**
```
https://api.example.com/api?server=:server&type=:type&id=:id
```

**其他格式：**
```
https://api.example.com/meting?server=:server&type=:type&id=:id&r=:r
```

### 语音分段机制

QQ 语音时长上限为2分钟，插件会自动将长歌曲分割为多个2分钟以内的片段：
- 每段时长：最多120秒（可配置）
- 格式：WAV
- 发送方式：逐段发送，每段间隔1秒

### 数据存储

- 会话音源设置存储在内存中，重启后恢复为默认音源
- 搜索结果临时存储在内存中，仅用于当前会话
- 下载的音频文件存储在系统临时目录，播放完成后自动删除

## 常见问题

### Q: 提示"请先在插件配置中设置 MetingAPI 模板"
A: 请在 AstrBot WebUI 的插件配置页面中填写正确的 MetingAPI 模板。

### Q: 搜索歌曲时提示"网络错误"
A: 请检查：
1. MetingAPI 模板是否正确
2. 网络连接是否正常
3. MetingAPI 服务是否可用

### Q: 播放歌曲时提示"缺少 pydub 依赖"
A: 请确保已安装 FFmpeg，并重新安装插件依赖。

### Q: 语音无法发送
A: 请检查：
1. 当前平台是否支持语音消息
2. FFmpeg 是否正确安装
3. 系统临时目录是否有写入权限

## 开发

### 项目结构

```
astrbot_plugin_meting/
├── main.py              # 插件主代码
├── metadata.yaml        # 插件元数据
├── _conf_schema.json    # 配置文件 Schema
├── requirements.txt     # Python 依赖
├── README.md           # 说明文档
├── LICENSE             # 许可证
└── .gitignore         # Git 忽略文件
```

### 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 致谢

- [初叶🍂MetingAPI](https://github.com/chuyegzs/Meting-UI-API) - 初叶🍂二次开发的MetingAPI
- [MetingAPI](https://github.com/metowolf/Meting) - 音乐 API 服务
- [AstrBot](https://github.com/AstrBotDevs/AstrBot) - AstrBot机器人框架

## 支持

如有问题或建议，欢迎加入 初叶🍂Furry 开发者的QQ群：1048889481（必点Star）
