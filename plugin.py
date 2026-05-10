# -*- coding: utf-8 -*-
"""Doubao Seedream Tool Plugin Entry Point."""
import importlib.util
import logging
import os

from qwenpaw.plugins.api import PluginApi

logger = logging.getLogger(__name__)


class DoubaoSeedreamToolPlugin:
    """Doubao Seedream Tool Plugin.

    Registers the generate_image_doubao tool into the Agent's toolkit.
    This is a pure backend plugin - no frontend code required.
    """

    def register(self, api: PluginApi) -> None:
        """Register the Doubao Seedream tool.

        Args:
            api: PluginApi instance
        """
        logger.info("Registering Doubao Seedream tool...")
        # Register startup hook to add tool to toolkit
        api.register_startup_hook(
            hook_name="register_doubao_seedream_tool",
            callback=self._register_tool,
            priority=50,
        )
        logger.info("✓ Doubao Seedream tool plugin registered")

    def _register_tool(self) -> None:
        """Register the generate_image_doubao tool to Agent toolkit.

        This is called during application startup.
        """
        try:
            # Load tool module
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            tool_path = os.path.join(plugin_dir, "tool.py")
            spec = importlib.util.spec_from_file_location(
                "doubao_seedream_tool",
                tool_path,
            )
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            generate_image_doubao = tool_module.generate_image_doubao

            # Register tool function globally
            import qwenpaw.agents.tools as tools_module

            setattr(tools_module, "generate_image_doubao", generate_image_doubao)
            if "generate_image_doubao" not in tools_module.__all__:
                tools_module.__all__.append("generate_image_doubao")
            logger.info("✓ Registered tool function: generate_image_doubao")

            # Add tool to current agent's config
            from qwenpaw.config.config import (
                BuiltinToolConfig,
                load_agent_config,
                save_agent_config,
            )
            from qwenpaw.app.agent_context import get_current_agent_id

            tool_name = "generate_image_doubao"
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
                            "使用火山引擎 Doubao Seedream-5.0-lite 生成图片"
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
            logger.error(f"Failed to register Doubao Seedream tool: {e}")
