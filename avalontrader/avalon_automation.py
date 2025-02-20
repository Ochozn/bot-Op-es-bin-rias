import pyautogui
import pygetwindow as gw
import time
import logging
import subprocess
import os
import warnings
from pywinauto import Application
import win32gui
import win32con

# Suprimir avisos do pywinauto
warnings.filterwarnings("ignore", category=UserWarning, module="pywinauto.*")

# --- Configurações ---
AVALON_EXECUTABLE_PATH = os.path.join(r"C:\Program Files (x86)\Avalon", "AvalonBroker.exe")
AVALON_WINDOW_TITLE = "Avalon"
VALOR_INICIAL_TRADE = "100"
MAX_RETRIES = 3
RETRY_DELAY = 2

# --- Coordenadas ---
COORD_BARRA_BUSCA = (194, 148)
COORD_ATIVO = (526, 298)
COORD_SELETOR_TEMPO = (1831, 229)
COORD_2_MINUTOS = (1638, 582)  # Coordenadas para 2 minutos
COORD_3_MINUTOS = (1643, 619)  # Coordenadas para 3 minutos
COORD_5_MINUTOS = (1652, 664)
COORD_COMPRAR = (1842, 445)
COORD_VENDER = (1835, 511)
COORD_AMOUNT = (1821, 161)

# --- Variáveis ---
avalon_window = None

def iniciar_avalon():
    """Inicia o aplicativo da Avalon se não estiver aberto."""
    global avalon_window
    try:
        windows = gw.getWindowsWithTitle(AVALON_WINDOW_TITLE)
        if windows:
            avalon_window = windows  # Pega a primeira janela encontrada
            logging.info("Aplicativo da Avalon já está aberto.")
            return

        logging.info("Iniciando o aplicativo da Avalon...")
        subprocess.Popen(AVALON_EXECUTABLE_PATH)
        time.sleep(10)

        windows = gw.getWindowsWithTitle(AVALON_WINDOW_TITLE)
        if windows:
            avalon_window = windows  # Pega a primeira janela encontrada
            avalon_window.maximize()

    except Exception as e:
        logging.error(f"Erro ao iniciar Avalon: {str(e)}")

def ativar_janela_avalon():
    """Ativa e maximiza a janela do aplicativo da Avalon."""
    global avalon_window
    try:
        if avalon_window is None:
            iniciar_avalon()

        if avalon_window.isMinimized:
            avalon_window.restore()

        avalon_window.activate()
        avalon_window.maximize()
        time.sleep(1)

        app = Application().connect(handle=avalon_window._hWnd)
        app.top_window().set_focus()

    except Exception as e:
        logging.error(f"Erro ao ativar janela: {str(e)}")
        iniciar_avalon()

def clicar_com_verificacao(coordenadas, tentativas=3):
    """Clica em coordenadas com verificação robusta."""
    x, y = coordenadas
    for _ in range(tentativas):
        try:
            pyautogui.click(x, y)
            time.sleep(1)
            return True
        except Exception as e:
            logging.warning(f"Falha ao clicar em {coordenadas}: {str(e)}")
    return False

def executar_acao_trade(acao, ativo, expiracao):
    """Executa os passos para realizar a ação de trade."""
    try:
        ativar_janela_avalon()

        if not clicar_com_verificacao(COORD_BARRA_BUSCA):
            raise Exception("Falha na barra de busca")

        pyautogui.write(ativo)
        time.sleep(1)

        if not clicar_com_verificacao(COORD_ATIVO):
            raise Exception("Falha ao selecionar ativo")

        time.sleep(4)

        if not clicar_com_verificacao(COORD_SELETOR_TEMPO):
            raise Exception("Falha no seletor de tempo")

        time.sleep(0.5)

        # Selecionar o tempo de expiração
        if expiracao == "M2":
            clicar_com_verificacao(COORD_2_MINUTOS)
        elif expiracao == "M3":
            clicar_com_verificacao(COORD_3_MINUTOS)
        elif expiracao == "M5":
            clicar_com_verificacao(COORD_5_MINUTOS)
        else:
            raise ValueError("Tempo de expiração inválido")

        if not clicar_com_verificacao(COORD_AMOUNT):
            raise Exception("Falha no campo de valor")

        pyautogui.hotkey('ctrl', 'a')
        pyautogui.press('backspace')
        pyautogui.write(VALOR_INICIAL_TRADE)
        time.sleep(0.5)

        coord = COORD_COMPRAR if acao == "COMPRADO" else COORD_VENDER
        if not clicar_com_verificacao(coord):
            raise Exception("Falha na ação de compra/venda")

        return time.time()

    except Exception as e:
        logging.critical(f"Erro na execução do trade: {str(e)}")
        raise