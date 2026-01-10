import discord
import threading
from fundednext_trading_system.monitoring.logger import logger

KILL_SWITCH_ACTIVE = False

COMMANDS = {
    "!kill": True,
    "!resume": False,
}

class KillSwitchBot(discord.Client):
    async def on_ready(self):
        logger.info(f"Discord Kill Switch connected as {self.user}")

    async def on_message(self, message):
        global KILL_SWITCH_ACTIVE

        if message.author == self.user:
            return

        content = message.content.lower().strip()

        if content in COMMANDS:
            KILL_SWITCH_ACTIVE = COMMANDS[content]

            state = "ACTIVATED" if KILL_SWITCH_ACTIVE else "DEACTIVATED"
            logger.critical(f"DISCORD KILL SWITCH {state}")

            await message.channel.send(
                f"🛑 Kill Switch {state}"
            )

def start_kill_switch_bot(token: str):
    intents = discord.Intents.default()
    intents.message_content = True

    bot = KillSwitchBot(intents=intents)

    thread = threading.Thread(
        target=lambda: bot.run(token),
        daemon=True
    )
    thread.start()

def check_kill_switch() -> bool:
    return KILL_SWITCH_ACTIVE
