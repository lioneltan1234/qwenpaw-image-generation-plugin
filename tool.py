# -*- coding: utf-8 -*-
# pylint: disable=too-many-return-statements,too-many-branches,too-many-locals
"""OpenAI-compatible image generation tool for QwenPaw."""
import base64
import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional, Union

import httpx

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse
from qwenpaw.constant import DEFAULT_MEDIA_DIR

logger = logging.getLogger(__name__)

# Default config values
DEFAULT_TIMEOUT = 60.0
DEFAULT_SIZE = "2K"
DEFAULT_N = 1
DEFAULT_OUTPUT_DIR = Path.home() / "Pictures" / "QwenPaw_Generated"
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _get_tool_config() -> dict:
    """Get tool config from plugin registry.

    Returns:
        Tool configuration dictionary
    """
    try:
        from qwenpaw.plugins.registry import PluginRegistry
        from qwenpaw.app.agent_context import get_current_agent_id

        registry = PluginRegistry()
        agent_id = get_current_agent_id() or "default"
        tool_config = registry.get_tool_config(
            "generate_image",
            agent_id,
        )
        return tool_config if tool_config else {}
    except Exception:
        return {}


async def generate_image(
    prompt: str,
    size: str = DEFAULT_SIZE,
    n: int = DEFAULT_N,
    style: str = "auto",
    image: Optional[Union[str, List[str]]] = None,
    web_search: bool = False,
) -> ToolResponse:
    """Generate images using any OpenAI-compatible image generation API.

    Supports Doubao Seedream, GPT Image, Flux, Stable Diffusion, and more.
    Simply configure the corresponding model, API key, and base URL.

    Args:
        prompt:
            Text description of the image to generate.
            Be specific and detailed for best results.
        size:
            Output image resolution. Options: "2K", "3K".
            Defaults to "2K".
            Note: Some models may not support this parameter.
        n:
            Number of images to generate (1-4).
            Defaults to 1.
        style:
            Image style. Options: "auto", "realistic", "anime", "artistic".
            Defaults to "auto".
            Note: Some models may not support this parameter.
        image:
            Optional reference image(s) for image-to-image generation.
            Can be a local file path, URL, or base64 encoded image.
            Supports single image or list of images (up to 14 reference images).
        web_search:
            Enable web search to enhance image generation with
            real-time information. Only supported by some models
            (e.g. doubao-seedream-5.0-lite). Defaults to False.

    Returns:
        ToolResponse:
            Contains the generated image(s) and metadata.

    Example:
        >>> result = await generate_image(
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
                        "Please set your API key in the tool settings."
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
                        "Please set your Base URL in the tool settings."
                    ),
                ),
            ],
        )

    # Security: enforce HTTPS
    if not base_url.startswith("https://"):
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Error: Base URL must use HTTPS to protect your API key."
                    ),
                ),
            ],
        )

    model = tool_config.get("model", "").strip()
    if not model:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        "Error: Model not configured. "
                        "Please set your model name in the tool settings."
                    ),
                ),
            ],
        )

    timeout = tool_config.get("timeout", DEFAULT_TIMEOUT)
    if timeout is None or timeout <= 0:
        timeout = DEFAULT_TIMEOUT
    else:
        try:
            timeout = float(timeout)
        except (ValueError, TypeError):
            timeout = DEFAULT_TIMEOUT

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
        "model": model,
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

    # Add web_search for supported models
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

    # Parse response (pass original prompt for revised_prompt comparison)
    return _parse_response(data, size, prompt.strip())


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

    # Limit to 14 reference images
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
    # Security: reject path traversal attempts
    normalized = os.path.normpath(file_path)
    if ".." in normalized:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Invalid path traversal detected: {file_path}",
                ),
            ],
        )

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

    # Security: enforce file size limit
    try:
        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            return ToolResponse(
                content=[
                    TextBlock(
                        type="text",
                        text=(
                            f"Error: File too large ({file_size / 1024 / 1024:.1f}MB). "
                            f"Maximum size is {MAX_FILE_SIZE / 1024 / 1024:.0f}MB."
                        ),
                    ),
                ],
            )
    except OSError as e:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Cannot read file metadata: {str(e)}",
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
        logger.exception(f"Failed to read image file {file_path}: {e}")
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=f"Error: Failed to read image file: {str(e)}",
                ),
            ],
        )


def _parse_response(
    data: dict,
    requested_size: str,
    prompt: str = "",
) -> ToolResponse:
    """Parse API response and build ToolResponse.

    Args:
        data: API response JSON
        requested_size: The size that was requested
        prompt: The original prompt (for revised_prompt comparison)

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
        b64_data = item.get("b64_json", "")
        revised_prompt = item.get("revised_prompt", "")
        item_size = item.get("size", requested_size)

        if url:
            result_text += f"**第 {i} 张** ({item_size}):\n"
            result_text += f"🔗 {url}\n\n"
        elif b64_data:
            # Save base64 as file
            saved_path = _save_b64_image(b64_data, i)
            if saved_path:
                result_text += f"**第 {i} 张**:\n"
                result_text += f"💾 {saved_path}\n\n"

        # Only show revised_prompt if it differs from original
        if revised_prompt and revised_prompt != prompt:
            result_text += f"_优化提示词: {revised_prompt}\n\n"

    # Add usage info if available
    if "usage" in data:
        usage = data["usage"]
        if "web_search" in usage and usage["web_search"] > 0:
            result_text += f"🔍 联网搜索次数: {usage['web_search']}\n"

    content.append(TextBlock(type="text", text=result_text.strip()))

    return ToolResponse(content=content)


def _save_b64_image(b64_data: str, index: int) -> Optional[str]:
    """Save base64 image data to file.

    Args:
        b64_data: Base64 encoded image data
        index: Image index for filename

    Returns:
        Path to saved file, or None on error
    """
    try:
        # Directly decode - b64_data is a plain base64 string, not JSON
        image_data = base64.b64decode(b64_data)

        output_dir = DEFAULT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        # UUID-based filename to avoid collisions
        filename = f"generated_image_{uuid.uuid4().hex[:8]}_{index}.png"
        output_path = output_dir / filename

        with open(output_path, "wb") as f:
            f.write(image_data)

        return str(output_path)
    except Exception as e:
        logger.exception(f"Failed to save base64 image: {e}")
        return None
