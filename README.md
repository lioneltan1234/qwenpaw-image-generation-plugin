# QwenPaw Image Generation Plugin

A multi-model image generation tool plugin for [QwenPaw](https://github.com/agentscope-ai/QwenPaw), compatible with any **OpenAI-compatible** image generation API.

## Supported Models

| Model | Base URL Example | Model Name Example |
|-------|----------------|-------------------|
| Doubao Seedream | `https://ark.cn-beijing.volces.com/api/plan/v3` | `doubao-seedream-5.0-lite` |
| GPT Image 2 | `https://api.openai.com/v1` | `gpt-image-2` |
| Other Compatible APIs | Custom | Custom |

## Features

- 🎨 **Text-to-Image** — Generate high-quality images from text descriptions
- 🖼️ **Reference Image Generation** — Support 1-14 reference images for style/content transfer
- 📐 **Multiple Resolutions** — Support 2K and 3K resolution output (model-dependent)
- 🔍 **Web Search** — Some models support web search enhancement (enable via tool call)
- 🖌️ **Multiple Styles** — `auto` / `realistic` / `anime` / `artistic` (model-dependent)

## Installation

### Option 1: GitHub Zipball (Recommended)

```bash
qwenpaw plugin install https://github.com/lioneltan1234/qwenpaw-image-generation-plugin/archive/refs/heads/main.zip
```

### Option 2: Local Installation

```bash
# Clone the repo
git clone https://github.com/lioneltan1234/qwenpaw-image-generation-plugin.git

# Install the plugin
qwenpaw plugin install ./qwenpaw-image-generation-plugin
```

## Configuration

### 1. Get API Key and Endpoint

Obtain from your service provider:
- **API Key**
- **Base URL**
- **Model Name**

### 2. Configure the Plugin in QwenPaw

1. Restart QwenPaw to load the plugin
2. Open Web UI → Tools
3. Find the `generate_image` tool
4. Fill in the configuration:
   - **API Key**: API Key (required)
   - **Base URL**: API Base URL (required)
   - **Model Name**: Model ID (required)
   - **Default Size**: `2K` or `3K` (optional)
   - **Timeout**: Timeout in seconds (optional, default 60)
5. **Enable** the tool

## Usage

After installation and enabling, simply describe the image you want to generate:

```
Generate an image: Shanghai Bund at sunset, golden light, vintage film style
```

### Tool Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | str | required | Image description, the more detailed the better |
| `size` | str | `"2K"` | Resolution: `"2K"` or `"3K"` |
| `n` | int | `1` | Number of images to generate (1-4) |
| `style` | str | `"auto"` | Style: `auto` / `realistic` / `anime` / `artistic` |
| `image` | str/List | None | Reference image(s) (local path, URL, or base64) |
| `web_search` | bool | `False` | Enable web search enhancement (some models only) |

### Examples

```python
# Text-to-image
result = await generate_image(
    prompt="A ginger cat sleeping peacefully by a cafe window, warm tones, photographic style",
    size="2K",
    style="realistic",
)

# Reference image generation
result = await generate_image(
    prompt="Apply the style of this image to: a cyberpunk mechanical cat",
    size="3K",
    image="/path/to/reference.jpg",
)

# Multiple images
result = await generate_image(
    prompt="Flower arrangement in glass bottles from different angles, photography style",
    n=3,
    size="2K",
)
```

## Dependencies

- Python >= 3.10
- httpx >= 0.24.0
- QwenPaw >= 1.1.6

## Project Structure

```
qwenpaw-image-generation-plugin/
├── plugin.json       # Plugin metadata
├── plugin.py         # Plugin registration logic (startup hook)
├── tool.py           # Tool function implementation
├── requirements.txt  # Python dependencies
├── README.md         # English documentation
└── README_zh.md     # Chinese documentation
```

## References

- [QwenPaw Plugin System](https://github.com/agentscope-ai/QwenPaw/tree/main/plugins)
- [OpenAI Image Generation API](https://platform.openai.com/api/docs/guides/image-generation)
- [Volcano Engine Ark API](https://www.volcengine.com/docs/6492/2172373)

## License

MIT
