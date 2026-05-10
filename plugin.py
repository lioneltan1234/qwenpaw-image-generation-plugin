# -*- coding: utf-8 -*-
"""Image Generation Tool Plugin Entry Point."""
import importlib.util
import logging
import os

from qwenpaw.plugins.api import PluginApi

logger = logging.getLogger(__name__)


class ImageGenerationToolPlugin:
    """Image Generation Tool Plugin.

    Registers the generate_image tool into the Agent's toolkit.
    This is a pure backend plugin - no frontend code required.
    """

    def register(self, api: PluginApi) -> None:
        """Register the image generation tool.

        Args:
            api: PluginApi instance
        """
        logger.info("Registering Image Generation tool...")
        # Register startup hook to add tool to toolkit
        api.register_startup_hook(
            hook_name="register_image_generation_tool",
            callback=self._register_tool,
            priority=50,
        )
        logger.info("✓ Image Generation tool plugin registered")

    def _register_tool(self) -> None:
        """Register the generate_image tool to Agent toolkit.

        This is called during application startup.
        """
        try:
            # Load tool module
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            tool_path = os.path.join(plugin_dir, "tool.py")
            spec = importlib.util.spec_from_file_location(
                "image_generation_tool",
                tool_path,
            )
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            generate_image = tool_module.generate_image

            # Register tool function globally
            import qwenpaw.agents.tools as tools_module

            setattr(tools_module, "generate_image", generate_image)
            if "generate_image" not in tools_module.__all__:
                tools_module.__all__.append("generate_image")
            logger.info("✓ Registered tool function: generate_image")

            # Add tool to current agent's config
            from qwenpaw.config.config import (
                BuiltinToolConfig,
                load_agent_config,
                save_agent_config,
            )
            from qwenpaw.app.agent_context import get_current_agent_id

            tool_name = "generate_image"
            try:
                agent_id = get_current_agent_id()
                if not agent_id:
                    logger.warning(
                        "No current agent ID found, "
                        "tool will be registered later",
                    )
                    return

                agent_config = load_agent_config(agent_id)
                if not agent_config.tools:
                    from qwenpaw.config.config import ToolsConfig

                    agent_config.tools = ToolsConfig()

                if tool_name not in agent_config.tools.builtin_tools:
                    agent_config.tools.builtin_tools[
                        tool_name
                    ] = BuiltinToolConfig(
                        name=tool_name,
                        enabled=False,
                        description=(
                            "使用 OpenAI 兼容接口生成图片"
                        ),
                        display_to_user=True,
                        async_execution=False,
                        icon="🎨",
                    )
                    save_agent_config(agent_id, agent_config)
                    logger.info(f"✓ Added tool to agent config: {agent_id}")
            except Exception as e:
                logger.warning(f"Failed to update agent config: {e}")

        except Exception as e:
            logger.error(f"Failed to register Image Generation tool: {e}")
