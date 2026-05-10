# Doubao Seedream Tool Plugin for QwenPaw

为 [QwenPaw](https://github.com/agentscope-ai/QwenPaw) 打造的图片生成工具插件，基于**火山引擎 Doubao Seedream-5.0-lite** 模型。

## 功能特性

- 🎨 **文生图** — 用文字描述生成高质量图片
- 🖼️ **参考图生成** — 支持上传 1-14 张参考图进行风格/内容迁移
- 📐 **多种分辨率** — 支持 2K 和 3K 分辨率输出
- 🔍 **联网搜索** — 启用后模型可搜索互联网信息（商品、天气等）
- 🖌️ **多种风格** — `auto` / `realistic` / `anime` / `artistic`

## 安装

### 方式一：从 GitHub 安装（推荐）

```bash
qwenpaw plugin install https://github.com/lioneltan1234/qwenpaw-doubao-seedream-plugin
```

### 方式二：本地安装

```bash
# 克隆仓库
git clone https://github.com/lioneltan1234/qwenpaw-doubao-seedream-plugin.git

# 安装插件
qwenpaw plugin install ./qwenpaw-doubao-seedream-plugin
```

## 配置

### 1. 获取火山引擎 API Key

1. 访问 [火山引擎控制台](https://console.volcengine.com/)
2. 开通 **Ark API** 服务
3. 在「模型推理」→「视觉模型」中找到 `doubao-seedream-5.0-lite`
4. 创建 API Key

### 2. 在 QwenPaw 中配置插件

1. 重启 QwenPaw 使插件生效
2. 打开 Web UI → 工具设置（Tools）
3. 找到 `generate_image_doubao` 工具
4. 填入以下配置：
   - **API Key**: 火山引擎 API Key（必填）
   - **Base URL**: `https://ark.cn-beijing.volces.com/api/plan/v3`（可选，默认值）
   - **默认分辨率**: `2K` 或 `3K`（可选）
   - **请求超时**: 超时秒数（可选，默认 60）
5. **启用**工具

## 使用方法

安装并启用后，直接在对话中描述你想生成的图片即可：

```
帮我用 Doubao 生成一张：日落时分的上海外滩，泛黄的光线，复古胶片风格
```

### 工具参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | str | 必填 | 图片描述，越详细越好 |
| `size` | str | `"2K"` | 分辨率：`"2K"` 或 `"3K"` |
| `n` | int | `1` | 生成数量（1-4） |
| `style` | str | `"auto"` | 风格：`auto` / `realistic` / `anime` / `artistic` |
| `image` | str/List | None | 参考图（本地路径、URL 或 base64） |
| `web_search` | bool | `False` | 是否启用联网搜索增强 |

### 使用示例

```python
# 文生图
result = await generate_image_doubao(
    prompt="一只橘猫在咖啡馆窗边安静地睡觉，暖色调，摄影风格",
    size="2K",
    style="realistic",
)

# 参考图生成
result = await generate_image_doubao(
    prompt="把这张图的风格应用到：一只赛博朋克风格的机械猫",
    size="3K",
    image="/path/to/reference.jpg",
)

# 多张生成
result = await generate_image_doubao(
    prompt="不同角度的玻璃瓶中的插花摄影",
    n=3,
    size="2K",
)
```

## 依赖

- Python >= 3.10
- httpx >= 0.24.0
- QwenPaw >= 1.1.6

## 项目结构

```
qwenpaw-doubao-seedream-plugin/
├── plugin.json       # 插件元数据
├── plugin.py         # 插件注册逻辑（startup hook）
├── tool.py           # 工具函数实现
├── requirements.txt  # Python 依赖
└── README.md         # 本文件
```

## 参考

- [火山引擎 Ark API 文档](https://www.volcengine.com/docs/6492/2172373)
- [Doubao Seedream-5.0-lite 模型说明](https://www.volcengine.com/docs/6492/2172373)
- [QwenPaw 插件系统文档](https://github.com/agentscope-ai/QwenPaw/tree/main/plugins)

## License

MIT
