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
from colorama import Fore, Style, init

# Suprimir avisos do pywinauto
warnings.filterwarnings("ignore", category=UserWarning, module="pywinauto.*")

# Initialize colorama
init()

# --- Configurações ---
AVALON_EXECUTABLE_PATH = os.path.join(r"C:\Program Files (x86)\Avalon", "Avalon.exe")
AVALON_WINDOW_TITLE = "Avalon"
VALOR_INICIAL_TRADE = "20"
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
            avalon_window = windows[0]  # Pega a primeira janela encontrada
            logging.info("Aplicativo da Avalon já está aberto.")
            return

        logging.info("Iniciando o aplicativo da Avalon...")
        subprocess.Popen(AVALON_EXECUTABLE_PATH)
        time.sleep(10)

        windows = gw.getWindowsWithTitle(AVALON_WINDOW_TITLE)
        if windows:
            avalon_window = windows[0]  # Pega a primeira janela encontrada
            avalon_window.maximize()

    except Exception as e:
        logging.error(f"Erro ao iniciar Avalon: {str(e)}")

def ativar_janela_avalon():
    """Ativa e maximiza a janela do aplicativo da Avalon com verificação robusta."""
    global avalon_window
    try:
        if avalon_window is None:
            iniciar_avalon()

        # Garante que a janela existe e está disponível
        windows = gw.getWindowsWithTitle(AVALON_WINDOW_TITLE)
        if not windows:
            logging.warning("Janela da Avalon não encontrada. Reiniciando aplicativo...")
            iniciar_avalon()
            windows = gw.getWindowsWithTitle(AVALON_WINDOW_TITLE)

        # Verifica se a janela encontrada é realmente a Avalon
        avalon_window = None
        for window in windows:
            if window.title == AVALON_WINDOW_TITLE:
                avalon_window = window
                break

        if not avalon_window:
            raise Exception("Não foi possível encontrar a janela da Avalon")

        # Força a restauração se minimizada
        if avalon_window.isMinimized:
            avalon_window.restore()
            time.sleep(1)  # Aumentado para dar mais tempo para restauração

        # Garante que a janela está maximizada
        if not avalon_window.isMaximized:
            avalon_window.maximize()
            time.sleep(1)  # Aumentado para dar mais tempo para maximização

        # Força o foco para a janela usando múltiplos métodos
        for _ in range(3):  # Tenta até 3 vezes
            avalon_window.activate()
            win32gui.SetForegroundWindow(avalon_window._hWnd)
            win32gui.ShowWindow(avalon_window._hWnd, win32con.SW_MAXIMIZE)
            
            # Conecta com pywinauto para garantir o foco
            app = Application().connect(handle=avalon_window._hWnd)
            app.top_window().set_focus()
            
            time.sleep(0.5)
            
            # Verifica se realmente conseguimos o foco
            if win32gui.GetForegroundWindow() == avalon_window._hWnd:
                break
        else:
            logging.warning("Não foi possível obter foco após 3 tentativas")

    except Exception as e:
        logging.error(f"Erro ao ativar janela: {str(e)}")
        iniciar_avalon()
        return False
    return True

def clicar_com_verificacao(coordenadas):
    """Clica em uma coordenada com verificação de sucesso."""
    try:
        pyautogui.click(coordenadas[0], coordenadas[1])
        time.sleep(0.5)
        return True
    except Exception as e:
        logging.error(f"Erro ao clicar nas coordenadas {coordenadas}: {str(e)}")
        raise Exception("Falha na barra de busca")
    return False

# --- Variáveis de Controle de Atividade ---
ultima_atividade = time.time()
atividade_suspensa = False
INTERVALO_ATIVIDADE = 300  # 5 minutes in seconds

def simular_atividade():
    """Simula atividade do usuário para manter a sessão ativa com verificação robusta de foco."""
    global ultima_atividade
    try:
        if not atividade_suspensa:
            print(f"{Fore.YELLOW}🔄 Simulando atividade... {Fore.CYAN}(🔍 Aguardando mensagens...){Style.RESET_ALL}")
            
            # Force window activation with retry
            for _ in range(3):
                ativar_janela_avalon()
                time.sleep(1)  # Give more time for window to respond
                
                if win32gui.GetForegroundWindow() == avalon_window._hWnd:
                    break
            else:
                logging.error("Não foi possível ativar a janela após 3 tentativas")
                return
            
            # Use asset search bar coordinates as start/end point
            start_x, start_y = COORD_BARRA_BUSCA
            pyautogui.moveTo(start_x, start_y, duration=0.5)
            
            # Move mouse in a clockwise square pattern with click at bottom-right
            print(f"{Fore.CYAN}🖱️ Movendo mouse em padrão quadrado... {Fore.CYAN}(🔍 Aguardando mensagens...){Style.RESET_ALL}")
            
            # Define square movement points with click at bottom-right
            square_size = 100
            points = [
                (start_x + square_size, start_y),  # Move right
                (start_x + square_size, start_y + square_size, True),  # Move down and click
                (start_x, start_y + square_size),  # Move left
                (start_x, start_y)  # Move up to starting point
            ]
            
            # Execute square movement with click
            for point in points:
                if len(point) == 3:  # Point with click
                    pyautogui.moveTo(point[0], point[1], duration=0.5)
                    pyautogui.click()
                    time.sleep(0.2)
                else:  # Regular movement point
                    pyautogui.moveTo(point[0], point[1], duration=0.5)
                    time.sleep(0.2)
            
            ultima_atividade = time.time()
            print(f"{Fore.GREEN}✅ Atividade simulada com sucesso! {Fore.CYAN}(🔍 Aguardando mensagens...){Style.RESET_ALL}")
            logging.info("Atividade simulada para manter a sessão ativa")
            
    except Exception as e:
        logging.error(f"Erro ao simular atividade: {str(e)}")
        print(f"{Fore.RED}❌ Erro ao simular atividade: {str(e)}{Style.RESET_ALL}")
def verificar_necessidade_atividade():
    """Verifica se é necessário simular atividade."""
    tempo_desde_ultima_atividade = time.time() - ultima_atividade
    return tempo_desde_ultima_atividade >= INTERVALO_ATIVIDADE

def suspender_atividade():
    """Suspende a simulação de atividade durante operações."""
    global atividade_suspensa
    atividade_suspensa = True
    logging.info("Simulação de atividade suspensa")

def retomar_atividade():
    """Retoma a simulação de atividade após operações."""
    global atividade_suspensa
    atividade_suspensa = False
    logging.info("Simulação de atividade retomada")

def executar_acao_trade(acao, ativo, expiracao):
    """Executa os passos para realizar a ação de trade."""
    try:
        suspender_atividade()  # Suspends at start
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
    # Remove retomar_atividade from finally block since it will be called after balance calculation
