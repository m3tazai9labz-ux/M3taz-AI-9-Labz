"""Discord bot — M3ta'z A.I. 9 Labz.

Supports:
  - DM messages → personal context
  - Server channels → mapped to business context by channel name / category
  - Slash commands: /ask, /task, /research, /status
"""

from __future__ import annotations

import logging
import asyncio

import discord
from discord import app_commands

import config
from orchestration.router import M3tazRouter, IncomingMessage

logger = logging.getLogger(__name__)

# Channel name → business context mapping
CHANNEL_CONTEXT_MAP = {
    "lotus": "lotus_group",
    "lotus-group": "lotus_group",
    "business": "lotus_group",
    "eagle-eye": "eagle_eye",
    "eagle_eye": "eagle_eye",
    "family": "family",
    "meta": "meta",
    "metaos": "meta",
    "q3bi": "meta",
    "general": "personal",
}


def _resolve_context(channel_name: str) -> str:
    """Map Discord channel name to a business context."""
    name = channel_name.lower().replace(" ", "-")
    for key, ctx in CHANNEL_CONTEXT_MAP.items():
        if key in name:
            return ctx
    return "personal"


class M3tazDiscordBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self._router = M3tazRouter()

    async def setup_hook(self) -> None:
        self.tree.add_command(_ask_command(self._router))
        self.tree.add_command(_task_command(self._router))
        self.tree.add_command(_status_command())
        await self.tree.sync()
        logger.info("Discord slash commands synced")

    async def on_ready(self) -> None:
        logger.info("Discord bot ready: %s (id=%s)", self.user, self.user.id)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # Only respond to DMs or @mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_mention = self.user in message.mentions
        if not (is_dm or is_mention):
            return

        # Strip mention from text
        text = message.content
        for mention in message.mentions:
            text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
        text = text.strip()

        if not text:
            await message.reply("Hey! What can I help you with?")
            return

        channel_name = message.channel.name if hasattr(message.channel, "name") else "dm"
        chat_context = _resolve_context(channel_name)

        async with message.channel.typing():
            msg = IncomingMessage(
                platform="discord",
                user_id=str(message.author.id),
                username=message.author.display_name,
                chat_id=str(message.channel.id),
                text=text,
                chat_context=chat_context,
            )
            result = await self._router.route(msg)

        # Discord has a 2000 char limit per message
        response = result.text
        if len(response) <= 1900:
            await message.reply(response)
        else:
            # Split into chunks
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await message.channel.send(chunk)
                await asyncio.sleep(0.5)


def _ask_command(router: M3tazRouter) -> app_commands.Command:
    @app_commands.command(name="ask", description="Ask M3ta'z AI a question")
    @app_commands.describe(question="Your question")
    async def ask(interaction: discord.Interaction, question: str) -> None:
        await interaction.response.defer()
        channel_name = interaction.channel.name if hasattr(interaction.channel, "name") else "dm"
        msg = IncomingMessage(
            platform="discord",
            user_id=str(interaction.user.id),
            username=interaction.user.display_name,
            chat_id=str(interaction.channel_id),
            text=question,
            chat_context=_resolve_context(channel_name),
        )
        result = await router.route(msg)
        await interaction.followup.send(result.text[:1900])
    return ask


def _task_command(router: M3tazRouter) -> app_commands.Command:
    @app_commands.command(name="task", description="Assign a multi-step task to the AI workforce")
    @app_commands.describe(task="Describe the task you want completed")
    async def task(interaction: discord.Interaction, task: str) -> None:
        await interaction.response.defer()
        channel_name = interaction.channel.name if hasattr(interaction.channel, "name") else "dm"
        msg = IncomingMessage(
            platform="discord",
            user_id=str(interaction.user.id),
            username=interaction.user.display_name,
            chat_id=str(interaction.channel_id),
            text=f"[TASK] {task}",
            chat_context=_resolve_context(channel_name),
        )
        result = await router.route(msg)
        await interaction.followup.send(f"Task dispatched to **{result.backend_used}**:\n\n{result.text[:1800]}")
    return task


def _status_command() -> app_commands.Command:
    @app_commands.command(name="status", description="Check M3ta'z Hub status")
    async def status(interaction: discord.Interaction) -> None:
        lines = [
            "**M3ta'z A.I. 9 Labz — Status**",
            "",
            "Platform Adapters: Telegram ✅ | Discord ✅ | Slack ✅ | WhatsApp ✅",
            "AI Backends: Open WebUI | Eigent AI | Agent Zero | AFFiNE | OpenClaw | Ollama",
            "Knowledge Base: AFFiNE",
            "",
            "Use `/ask` for questions, `/task` for multi-step work.",
        ]
        await interaction.response.send_message("\n".join(lines))
    return status


def run_discord_bot() -> None:
    if not config.DISCORD_BOT_TOKEN:
        logger.warning("DISCORD_BOT_TOKEN not set — Discord bot will not start")
        return
    bot = M3tazDiscordBot()
    bot.run(config.DISCORD_BOT_TOKEN, log_handler=None)
