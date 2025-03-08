import time
import threading
import logging
from datetime import datetime, timedelta
from avalon_automation import executar_acao_trade, COORD_COMPRAR, COORD_VENDER, COORD_AMOUNT, VALOR_INICIAL_TRADE
from utils import extrair_informacoes, calcular_tempos
from image_processing import (
    obter_valor_banca,
    obter_regiao_posicao_atual,
    extrair_posicao_atual,
    take_region_screenshot,
    ler_tempo_com_ocr,
    COORD_EXPIRATION_TIMER
)
import pyautogui
from colorama import Fore, Style, init

# --- Inicialização do Colorama ---
init(autoreset=True)

# --- Configuração do Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Variáveis Globais com Controle de Thread ---
lock = threading.Lock()
status_info_event = threading.Event()
stop_threads_event = threading.Event()
voltar_ao_inicio_event = threading.Event()
shared_posicao = {"Open": 0.0, "Current Price": 0.0}
shared_tempo_restante = {"tempo": None}

# ================= FUNÇÕES DE PROCESSAMENTO =================

def processar_mensagem(mensagem):
    """Processa mensagens do Telegram com tratamento robusto de erros."""
    try:
        logging.info(f"Mensagem recebida: {mensagem[:100]}...")

        if "✅ ENTRADA CONFIRMADA✅" in mensagem:
            print(f"\n{Fore.GREEN}🎯 Sinal de Trade Rápido Detectado!{Style.RESET_ALL}")
            
            # Suspende a simulação de atividade assim que detectar sinal válido
            from avalon_automation import suspender_atividade
            suspender_atividade()

            # Extração de informações com retentativas
            for _ in range(3):
                ativo, acao, hora_str, expiracao = extrair_informacoes(mensagem)  # Extraindo 'expiracao'
                if all([ativo, acao, hora_str, expiracao]):
                    break
                time.sleep(1)
            else:
                raise ValueError("Falha ao extrair informações após 3 tentativas")

            # Validação do horário
            entrada_dt = calcular_tempos(hora_str)
            if entrada_dt < datetime.now():
                raise ValueError(f"Horário inválido: {entrada_dt.strftime('%H:%M:%S')}")

            print(f"{Fore.CYAN}⏰ Operação programada para: {entrada_dt.strftime('%H:%M:%S')}{Style.RESET_ALL}")
            executar_operacao(ativo, acao, entrada_dt, expiracao)  # Passando 'expiracao'

        else:
            print(f"{Fore.YELLOW}⚠️ Mensagem ignorada (não é um trade){Style.RESET_ALL}")

    except Exception as e:
        logging.error(f"Erro no processamento: {str(e)}")
        print(f"{Fore.RED}❌ Erro crítico: {str(e)}{Style.RESET_ALL}")

# ================= THREADS DE VERIFICAÇÃO =================

def verificar_expiration(stop_event):
    """Monitora o tempo restante com tratamento robusto."""
    while not stop_event.is_set():
        try:
            x1, y1, x2, y2 = COORD_EXPIRATION_TIMER
            screenshot = take_region_screenshot(x1, y1, x2 - x1, y2 - y1)
            tempo_str = ler_tempo_com_ocr(screenshot)

            with lock:
                if tempo_str.isdigit() and len(tempo_str) == 4:
                    minutos = int(tempo_str[:2])
                    segundos = int(tempo_str[2:])
                    tempo_total = minutos * 60 + segundos
                else:
                    tempo_total = None

                shared_tempo_restante["tempo"] = tempo_total

        except Exception as e:
            logging.error(f"Erro expiration: {str(e)}")
        time.sleep(0.1)

def verificar_status(ativo, acao, stop_event):
    """Verifica o status da operação com conversão segura."""
    while not stop_event.is_set():
        try:
            img = obter_regiao_posicao_atual()
            posicao = extrair_posicao_atual(img)

            with lock:
                if posicao:
                    shared_posicao["Open"] = float(posicao.get("Open", 0.0))
                    shared_posicao["Current Price"] = float(posicao.get("Current Price", 0.0))

        except Exception as e:
            logging.error(f"Erro status: {str(e)}")
        time.sleep(0.1)

# ================= FUNÇÃO PRINCIPAL =================

def executar_operacao(ativo, acao, entrada_dt, expiracao):  # Adicionando parâmetro 'expiracao'
    """Executa a operação completa com um fluxo resiliente."""
    global stop_threads_event
    execucao_final_realizada = False

    try:
        # --- Fase 1: Pré-Execução ---
        print(f"\n{Fore.BLUE}⏳ Iniciando contagem regressiva...{Style.RESET_ALL}")

        # Subtrai 15 segundos para o setup
        entrada_dt -= timedelta(seconds=15)

        while datetime.now() < entrada_dt:
            segundos_restantes = (entrada_dt - datetime.now()).total_seconds()
            print(f"{Fore.YELLOW}⏳ Tempo restante: {int(segundos_restantes // 60):02d}:{int(segundos_restantes % 60):02d}", end="\r")
            time.sleep(0.1)

        # --- Fase 2: Execução ---
        print(f"\n{Fore.GREEN}🚀 Executando {acao} em {ativo}{Style.RESET_ALL}")

        # Passo 1: Obter valor inicial com retentativas
        valor_inicial = None
        for _ in range(5):
            valor_inicial = obter_valor_banca()
            if valor_inicial is not None:
                print(f"{Fore.CYAN}💰 Valor detectado da banca: {valor_inicial:.2f}{Style.RESET_ALL}")
                break
            time.sleep(2)
        else:
            raise ValueError("Falha crítica: Não foi possível ler o saldo após 5 tentativas")

        # Passo 2: Executar ação de trade (agora com 'expiracao')
        executar_acao_trade(acao, ativo, expiracao)  # Passando 'expiracao'
        time.sleep(1)

        # Passo 3: Configurar valor do trade
        pyautogui.click(COORD_AMOUNT)
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(VALOR_INICIAL_TRADE)
        time.sleep(0.5)

        # Passo 4: Executar compra/venda
        coord = COORD_COMPRAR if acao == "COMPRADO" else COORD_VENDER
        pyautogui.click(coord)
        time.sleep(2)

        # --- Fase 3: Monitoramento Contínuo ---
        stop_threads_event.clear()
        expiration_thread = threading.Thread(target=verificar_expiration, args=(stop_threads_event,))
        status_thread = threading.Thread(target=verificar_status, args=(ativo, acao, stop_threads_event))

        expiration_thread.start()
        status_thread.start()

        # --- Loop Principal com Atualização em Tempo Real ---
        ultima_atualizacao = time.time()
        while True:
            try:
                with lock:
                    current_price = shared_posicao["Current Price"]
                    open_price = shared_posicao["Open"]
                    tempo_restante = shared_tempo_restante["tempo"]

                # Exibir status continuamente com atualização mais frequente
                if time.time() - ultima_atualizacao >= 0.1:
                    em_lucro = (current_price > open_price) if acao == "COMPRADO" else (current_price < open_price)
                    status = f"{Fore.GREEN}↑ LUCRO" if em_lucro else f"{Fore.RED}↓ PREJUÍZO"
                    tempo_restante_str = f"{tempo_restante // 60:02d}:{tempo_restante % 60:02d}" if tempo_restante else "N/A"
                    print(f"\r{Fore.CYAN}📊 {ativo} | {Fore.YELLOW}🕒 {tempo_restante_str} | {status}{Style.RESET_ALL}", end="")
                    ultima_atualizacao = time.time()

                # Verificar condição de saída com controle de execução final
                if tempo_restante and tempo_restante <= 5 and not execucao_final_realizada:
                    print(f"\n{Fore.BLUE}⏳ Tempo crítico detectado! Aguardando 6s...{Style.RESET_ALL}")
                    execucao_final_realizada = True
                    stop_threads_event.set()
                    expiration_thread.join(timeout=5)
                    status_thread.join(timeout=5)
                    time.sleep(6)

                    # Get the final balance
                    valor_final = obter_valor_banca()
                    if valor_final is None:
                        valor_final = valor_inicial

                    # Calculate and display the result
                    lucro = valor_final - valor_inicial
                    resultado = f"{Fore.GREEN}💰✅ Lucro: +{lucro:.2f}" if lucro > 0 else f"{Fore.RED}📉❌ Prejuízo: {lucro:.2f}"
                    print(f"{resultado}{Style.RESET_ALL}")

                    # Reset the shared position and remaining time
                    with lock:
                        shared_posicao["Open"] = 0.0
                        shared_posicao["Current Price"] = 0.0
                        shared_tempo_restante["tempo"] = None

                    # Retoma a simulação de atividade após o cálculo final da banca
                    from avalon_automation import retomar_atividade
                    retomar_atividade()
                    
                    voltar_ao_inicio_event.set()
                    break

            except Exception as e:
                print(f"\n{Fore.YELLOW}⚠️ Erro temporário: {str(e)}{Style.RESET_ALL}")
                time.sleep(1)

    except Exception as e:
        logging.critical(f"Erro fatal: {str(e)}")
        print(f"{Fore.RED}⛔ {str(e)}{Style.RESET_ALL}")
        stop_threads_event.set()