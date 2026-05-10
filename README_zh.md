# QwenPaw Image Generation Plugin

为 [QwenPaw](https://github.com/agentscope-ai/QwenPaw) 打造的多模型图片生成工具插件，兼容任何 **OpenAI 风格**的图片生成 API。

## 支持的模型

| 模型 | Base URL 示例 | 模型名称示例 |
|------|-------------|------------|
| Doubao Seedream | `https://ark.cn-beijing.volces.com/api/plan/v3` | `doubao-seedream-5.0-lite` |
| GPT Image 2 | `https://api.openai.com/v1` | `gpt-image-2` |
| 其他兼容 API | 自定义 | 自定义 |

## 功能特性

- 🎨 **文生图** — 用文字描述生成高质量图片
- 🖼️ **参考图生成** — 支持上传 1-14 张参考图进行风格/内容迁移
- 📐 **多种分辨率** — 支持 2K 和 3K 分辨率输出（部分模型）
- 🔍 **联网搜索** — 部分模型支持联网搜索增强（需工具调用时开启）
- 🖌️ **多种风格** — `auto` / `realistic` / `anime` / `artistic`（部分模型）

## 安装

### 方式一：GitHub Zipball（推荐）

```bash
qwenpaw plugin install https://github.com/lioneltan1234/qwenpaw-image-generation-plugin/archive/refs/heads/main.zip
```

### 方式二：本地安装

```bash
# 克隆仓库
git clone https://github.com/lioneltan1234/qwenpaw-image-generation-plugin.git

# 安装插件
qwenpaw plugin install ./qwenpaw-image-generation-plugin
```

## 配置

### 1. 获取 API Key 和端点

根据你使用的服务商，在其控制台获取：
- **API Key**
- **Base URL**
- **模型名称**

### 2. 在 QwenPaw 中配置插件

1. 重启 QwenPaw 使插件生效
2. 打开 Web UI → 工具设置（Tools）
3. 找到 `generate_image` 工具
4. 填入以下配置：
   - **API Key**: API Key（必填）
   - **Base URL**: API Base URL（必填）
   - **模型名称**: 模型 ID（必填）
   - **默认分辨率**: `2K` 或 `3K`（可选）
   - **请求超时**: 超时秒数（可选，默认 60）
5. **启用**工具

## 使用方法

安装并启用后，直接在对话中描述你想生成的图片即可：

```
帮我生成一张：日落时分的上海外滩，泛黄的光线，复古胶片风格
```

### 工具参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | str | 必填 | 图片描述，越详细越好 |
| `size` | str | `"2K"` | 分辨率：`"2K"` 或 `"3K"` |
| `n` | int | `1` | 生成数量（1-4） |
| `style` | str | `"auto"` | 风格：`auto` / `realistic` / `anime` / `artistic` |
| `image` | str/List | None | 参考图（本地路径、URL 或 base64） |
| `web_search` | bool | `False` | 是否启用联网搜索增强（部分模型支持） |

### 使用示例

```python
# 文生图
result = await generate_image(
    prompt="一只橘猫在咖啡馆窗边安静地睡觉，暖色调，摄影风格",
    size="2K",
    style="realistic",
)

# 参考图生成
result = await generate_image(
    prompt="把这张图的风格应用到：一只赛博朋克风格的机械猫",
    size="3K",
    image="/path/to/reference.jpg",
)

# 多张生成
result = await generate_image(
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
qwenpaw-image-generation-plugin/
├── plugin.json       # 插件元数据
├── plugin.py         # 插件注册逻辑（startup hook）
├── tool.py           # 工具函数实现
├── requirements.txt  # Python 依赖
└── README.md         # 本文件
```

## 参考

- [QwenPaw 插件系统文档](https://github.com/agentscope-ai/QwenPaw/tree/main/plugins)
- [OpenAI Image Generation API](https://platform.openai.com/api/docs/guides/image-generation)
- [火山引擎 Ark API 文档](https://www.volcengine.com/docs/6492/2172373)

## License

MIT
