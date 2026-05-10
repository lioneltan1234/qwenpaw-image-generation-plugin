# -*- coding: utf-8 -*-
# pylint: disable=too-many-return-statements,too-many-branches,too-many-locals
"""Doubao Seedream-5.0-lite image generation tool."""
import base64
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

import httpx

from agentscope.message import ImageBlock, TextBlock
from agentscope.tool import ToolResponse
from qwenpaw.constant import DEFAULT_MEDIA_DIR

logger = logging.getLogger(__name__)

# Default config values
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/plan/v3"
DEFAULT_MODEL = "doubao-seedream-5.0-lite"
DEFAULT_TIMEOUT = 60.0
DEFAULT_SIZE = "2K"
DEFAULT_N = 1


def _get_tool_config() -> dict:
    """Get tool config from plugin registry.

    Returns:
        Tool configuration dictionary
    """
    try:
        from qwenpaw.plugins.registry import PluginRegistry

        registry = PluginRegistry()
        tool_config = registry.get_tool_config(
            "generate_image_doubao",
            "",
        )
        return tool_config if tool_config else {}
    except Exception:
        return {}


async def generate_image_doubao(
    prompt: str,
    size: str = DEFAULT_SIZE,
    n: int = DEFAULT_N,
    style: str = "auto",
    image: Optional[Union[str, List[str]]] = None,
    web_search: bool = False,
) -> ToolResponse:
    """Generate images using Doubao Seedream-5.0-lite model.

    Args:
        prompt:
            Text description of the image to generate.
            Be specific and detailed for best results.
        size:
            Output image resolution. Options: "2K", "3K".
            Defaults to "2K".
        n:
            Number of images to generate (1-4).
            Defaults to 1.
        style:
            Image style. Options: "auto", "realistic", "anime", "artistic".
            Defaults to "auto".
        image:
            Optional reference image(s) for image-to-image generation.
            Can be a local file path, URL, or base64 encoded image.
            Supports single image or list of images (up to 14 reference images
            for advanced features).
        web_search:
            Enable web search to enhance image generation with
            real-time information. Only supported by
            doubao-seedream-5.0-lite. Defaults to False.

    Returns:
        ToolResponse:
            Contains the generated image(s) and metadata.

    Example:
        >>> result = await generate_image_doubao(
        ...     prompt="一只在咖啡馆窗边看雨的橘猫",
        ...     size="2K",
        ...     n=1,
        ...     style="realistic",
        ... )
    """
    # Get tool config
    tool_config = _get_tool_config()
    if not tool_config:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Error: Tool not configured. "
                        "Please set your API key in the tool settings."
                    ),
                ),
            ],
        )

    api_key = tool_config.get("api_key")
    if not api_key:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Error: API key not configured. "
                        "Please set your Doubao API key in the tool settings."
                    ),
                ),
            ],
        )

    base_url = tool_config.get("base_url", "").strip()
    if not base_url:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Error: Base URL not configured. "
                        "Please set your Doubao Base URL in the tool settings."
                    ),
                ),
            ],
        )

    timeout = tool_config.get("timeout", DEFAULT_TIMEOUT)
    if timeout is None or timeout <= 0:
        timeout = DEFAULT_TIMEOUT
    else:
        timeout = float(timeout)

    # Validate parameters
    valid_sizes = {"2K", "3K"}
    if size not in valid_sizes:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Error: Invalid size '{size}'. "
                        f"Must be one of: {', '.join(valid_sizes)}"
                    ),
                ),
            ],
        )

    valid_styles = {"auto", "realistic", "anime", "artistic"}
    if style not in valid_styles:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Error: Invalid style '{style}'. "
                        f"Must be one of: {', '.join(valid_styles)}"
                    ),
                ),
            ],
        )

    if n < 1 or n > 4:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: n must be between 1 and 4.",
                ),
            ],
        )

    if not prompt or not prompt.strip():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: prompt cannot be empty.",
                ),
            ],
        )

    # Build endpoint URL
    endpoint = f"{base_url.rstrip('/')}/images/generations"

    # Build request payload
    payload: dict = {
        "model": DEFAULT_MODEL,
        "prompt": prompt.strip(),
        "size": size,
        "n": n,
        "style": style,
    }

    # Handle reference images
    if image:
        processed_images = _process_reference_images(image)
        if isinstance(processed_images, ToolResponse):
            return processed_images
        payload["image"] = processed_images

    # Add web_search for 5.0-lite
    if web_search:
        payload["web_search"] = True

    # Make API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                endpoint,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.TimeoutException:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Request timed out after {timeout}s.",
                ),
            ],
        )
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_data = e.response.json()
            error_detail = error_data.get("error", {}).get(
                "message",
                error_data.get("message", str(e)),
            )
        except Exception:
            error_detail = str(e)
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: API request failed: {error_detail}",
                ),
            ],
        )
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Unexpected error: {str(e)}",
                ),
            ],
        )

    # Parse response
    return _parse_response(data, n)


def _process_reference_images(
    image: Union[str, List[str]],
) -> Union[List[str], ToolResponse]:
    """Process reference image(s) to base64 or URL format.

    Args:
        image: Single or list of image paths/URLs/base64

    Returns:
        List of processed image strings, or ToolResponse on error
    """
    if isinstance(image, str):
        images = [image]
    else:
        images = list(image)

    # Limit to 14 reference images (Doubao Seedream limit)
    if len(images) > 14:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text="Error: Maximum 14 reference images supported.",
                ),
            ],
        )

    processed = []
    for img in images:
        img = img.strip()
        if not img:
            continue

        # URL - pass through as-is
        if img.startswith(("http://", "https://")):
            processed.append(img)
        # Base64 - pass through as-is
        elif img.startswith("data:image/"):
            processed.append(img)
        # Local file path
        else:
            result = _file_to_base64(img)
            if isinstance(result, ToolResponse):
                return result
            processed.append(result)

    return processed


def _file_to_base64(file_path: str) -> Union[str, ToolResponse]:
    """Convert local file to base64 data URL.

    Args:
        file_path: Path to local image file

    Returns:
        Base64 data URL string, or ToolResponse on error
    """
    path = Path(os.path.expanduser(file_path))
    if not path.exists():
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: File not found: {file_path}",
                ),
            ],
        )

    # Validate file extension
    valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    if path.suffix.lower() not in valid_extensions:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Error: Unsupported image format: {path.suffix}. "
                        f"Supported: {', '.join(valid_extensions)}"
                    ),
                ),
            ],
        )

    try:
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".bmp": "image/bmp",
            ".gif": "image/gif",
        }.get(path.suffix.lower(), "image/png")

        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Failed to read image file: {str(e)}",
                ),
            ],
        )


def _parse_response(data: dict, n: int) -> ToolResponse:
    """Parse API response and build ToolResponse.

    Args:
        data: API response JSON
        n: Number of images requested

    Returns:
        ToolResponse with image blocks and text
    """
    content: list = []

    # Handle different response formats
    if "data" not in data:
        # Error response
        error_msg = data.get("error", {}).get(
            "message",
            data.get("message", "Unknown error"),
        )
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Error: {error_msg}")],
        )

    image_list = data["data"]
    if not image_list:
        return ToolResponse(
            content=[
                TextBlock(type="text", text="Error: No images returned."),
            ],
        )

    image_count = len(image_list)

    # Build result text
    result_text = f"✅ 成功生成 {image_count} 张图片：\n\n"
    for i, item in enumerate(image_list, 1):
        url = item.get("url", "")
        b64_json = item.get("b64_json", "")
        revised_prompt = item.get("revised_prompt", "")

        if url:
            result_text += f"**第 {i} 张** ({item.get('size', size)}):\n"
            result_text += f"🔗 {url}\n\n"
        elif b64_json:
            # Save base64 as file
            saved_path = _save_b64_image(b64_json, i)
            if saved_path:
                result_text += f"**第 {i} 张**:\n"
                result_text += f"💾 {saved_path}\n\n"

        if revised_prompt and revised_prompt != prompt:
            result_text += f"_优化提示词: {revised_prompt}\n\n"

    # Add usage info if available
    if "usage" in data:
        usage = data["usage"]
        if "web_search" in usage and usage["web_search"] > 0:
            result_text += f"🔍 联网搜索次数: {usage['web_search']}\n"

    content.append(TextBlock(type="text", text=result_text.strip()))

    return ToolResponse(content=content)


def _save_b64_image(b64_json: str, index: int) -> Optional[str]:
    """Save base64 image data to file.

    Args:
        b64_json: Base64 encoded image JSON
        index: Image index for filename

    Returns:
        Path to saved file, or None on error
    """
    try:
        import json

        decoded = json.loads(b64_json)
        image_data = base64.b64decode(decoded)

        output_dir = Path(DEFAULT_MEDIA_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"doubao_seedream_{index}.png"
        output_path = output_dir / filename

        with open(output_path, "wb") as f:
            f.write(image_data)

        return str(output_path)
    except Exception as e:
        logger.error(f"Failed to save base64 image: {e}")
        return None
