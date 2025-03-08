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

async def get_grupo_nome(grupo_id):
    """Obtém o nome do grupo do Telegram usando o ID."""
    try:
        grupo = await client.get_entity(grupo_id)
        return grupo.title
    except Exception as e:
        logging.error(f"Erro ao obter o nome do grupo com ID {grupo_id}: {e}")
        return "Grupo Desconhecido"

async def conectar_telegram():
    """Conecta ao Telegram com tentativas de reconexão e exibe o nome do grupo."""
    reconnect_attempts = 0
    grupo_nome = "Grupo Desconhecido"  # Valor padrão

    grupo_nome = await get_grupo_nome(config.GRUPO_ALVO_ID) # Puxa o nome do grupo diretamente do Telegram

    while True:
        try:
            await client.start(config.PHONE_NUMBER)
            if not await client.is_user_authorized():
                await client.send_code_request(config.PHONE_NUMBER)
                await client.sign_in(config.PHONE_NUMBER, input('Código: '))
            logging.info("Conectado ao Telegram")
            print(f"Aguardando mensagens do grupo: '{grupo_nome}' (ID: {config.GRUPO_ALVO_ID})...") # Mensagem com nome e ID do grupo
            break  # Sai do loop se a conexão for bem-sucedida
        except Exception as e:
            reconnect_attempts += 1
            logging.error(f"Erro ao conectar ao Telegram (tentativa {reconnect_attempts}): {str(e)}")
            await asyncio.sleep(5)  # Espera antes de tentar novamente

@client.on(events.NewMessage(chats=config.GRUPO_ALVO_ID))
async def handler(event):
    """Handles new messages in the Telegram group."""
    try:
        msg = event.message.message
        await client.loop.run_in_executor(None, processar_mensagem, msg)  # Executa em executor para evitar bloquear
    except Exception as e:
        logging.error(f"Erro ao processar mensagem: {str(e)}")

async def main():
    print("Aguardando mensagem...") # Mensagem inicial genérica
    await conectar_telegram()
    # O Bot agora continua a rodar e escutar por mensagens devido ao client.run_until_disconnected() em conectar_telegram (chamado implicitamente por client.start)

if __name__ == '__main__':
    client.loop.run_until_complete(main())