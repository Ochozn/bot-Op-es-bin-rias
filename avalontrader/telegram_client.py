from telethon import TelegramClient, events
import config
import logging
import asyncio
from trade_execution import processar_mensagem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create a Telegram client
client = TelegramClient('avalonsession', config.API_ID, config.API_HASH)

async def conectar_telegram():
    """Connects to Telegram with reconnection attempts."""
    reconnect_attempts = 0
    while True:
        try:
            await client.start(config.PHONE_NUMBER)
            if not await client.is_user_authorized():
                await client.send_code_request(config.PHONE_NUMBER)
                await client.sign_in(config.PHONE_NUMBER, input('Código: '))
            logging.info("Conectado ao Telegram")
            break  # Exit the loop if connection is successful
        except Exception as e:
            reconnect_attempts += 1
            logging.error(f"Erro ao conectar ao Telegram (tentativa {reconnect_attempts}): {str(e)}")
            await asyncio.sleep(5)  # Wait before retrying

@client.on(events.NewMessage(chats=config.GRUPO_ALVO_ID))
async def handler(event):
    """Handles new messages in the Telegram group."""
    try:
        msg = event.message.message
        await client.loop.run_in_executor(None, processar_mensagem, msg)  # Run in executor to avoid blocking
    except Exception as e:
        logging.error(f"Erro ao processar mensagem: {str(e)}")