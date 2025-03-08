import logging
from avalon_automation import (
    iniciar_avalon, 
    ativar_janela_avalon, 
    verificar_necessidade_atividade,  # Add this import
    simular_atividade  # Add this import too since it's used
)
from telegram_client import client, conectar_telegram
import asyncio
import threading
from trade_execution import stop_threads_event, voltar_ao_inicio_event
from colorama import Fore, Style, init
import signal
import sys
from datetime import datetime
import os

# --- Inicialização do Colorama ---
init(autoreset=True)

# --- Configuração de logging ---
logging.basicConfig(filename='app.log', filemode='w',
                    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# --- Logo ASCII ---
AVALON_LOGO = f"""
{Fore.CYAN}
  █████╗ ██╗   ██╗ █████╗ ██╗      ██████╗ ███╗   ██╗
 ██╔══██╗██║   ██║██╔══██╗██║     ██╔═══██╗████╗  ██║
 ███████║██║   ██║███████║██║     ██║   ██║██╔██╗ ██║
 ██╔══██║╚██╗ ██╔╝██╔══██║██║     ██║   ██║██║╚██╗██║
 ██║  ██║ ╚████╔╝ ██║  ██║███████╗╚██████╔╝██║ ╚████║
 ╚═╝  ╚═╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
{Style.RESET_ALL}
"""

def signal_handler(sig, frame):
    print(f"\n{Fore.RED}🚫 Interrupção recebida, encerrando...{Style.RESET_ALL}")
    stop_threads_event.set()
    os._exit(0)  # Força a saída imediata

async def activity_loop():
    while not stop_threads_event.is_set():
        if verificar_necessidade_atividade():
            simular_atividade()
        await asyncio.sleep(1)  # Check every second

# --- Função Principal ---
async def main():
    signal.signal(signal.SIGINT, signal_handler)
    print(AVALON_LOGO)
    print(f"{Fore.GREEN}✅ Sistema de Automação Avalon Iniciado{Style.RESET_ALL}\n")

    # Inicia o Avalon
    iniciar_avalon()
    ativar_janela_avalon()

    # Conecta ao Telegram
    await conectar_telegram()

    # Inicia o loop de atividade em uma tarefa separada
    activity_task = asyncio.create_task(activity_loop())

    # Mantém o script rodando
    print(f"{Fore.CYAN}🔍 Aguardando mensagens...{Style.RESET_ALL}")
    logging.info("Aguardando mensagens...")
    
    try:
        while True:
            await client.loop.run_in_executor(None, voltar_ao_inicio_event.wait)
            voltar_ao_inicio_event.clear()
            print(f"{Fore.CYAN}🔄 Aguardando nova rodada de mensagens...{Style.RESET_ALL}")
            await client.run_until_disconnected()
            
    except Exception as e:
        logging.error(f"Erro crítico: {e}")
        print(f"{Fore.RED}⛔ Erro crítico: {e}{Style.RESET_ALL}")
    finally:
        stop_threads_event.set()
        activity_task.cancel()  # Cancel the activity task
        try:
            await activity_task  # Wait for task to be cancelled
        except asyncio.CancelledError:
            pass
        logging.info("Script parado.")
        print(f"\n{Fore.RED}⏹️ Script parado.{Style.RESET_ALL}")
        if client.is_connected():
            client.disconnect()

# --- Ponto de Entrada ---
if __name__ == "__main__":
    with client:
        try:
            client.loop.run_until_complete(main())
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}⏹️ Script interrompido pelo usuário.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}⛔ Erro fatal: {e}{Style.RESET_ALL}")