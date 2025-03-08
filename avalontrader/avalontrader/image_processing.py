# image_processing.py
from PIL import ImageGrab
import cv2
import numpy as np
import pytesseract
import re
import logging
import time
import os

# Define prints directory path
PRINTS_DIR = os.path.join(os.path.dirname(__file__), 'prints')

# Ensure prints directory exists
os.makedirs(PRINTS_DIR, exist_ok=True)

# Configuração do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# --- Coordenadas da Interface ---
COORD_BANCA = (1448, 31, 1623, 119)          # left, top, right, bottom
COORD_OPEN_POSITIONS = (1023, 773, 1381, 844) # Região das posições abertas
COORD_EXPIRATION_TIMER = (574, 797, 620, 825) # Temporizador de expiração

# --- Configuração de Logging ---
logging.basicConfig(level=logging.INFO)

def obter_regiao_posicao_atual():
    """Captura e processa a região das posições abertas."""
    try:
        # Captura da região
        screenshot = ImageGrab.grab(bbox=COORD_OPEN_POSITIONS)
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # Pré-processamento intensivo
        img = cv2.resize(img, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
        img = cv2.GaussianBlur(img, (3, 3), 0)
        img = cv2.threshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 0, 255, 
                          cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        return img
    except Exception as e:
        logging.error(f"Erro na captura da posição: {str(e)}")
        return None

def extrair_posicao_atual(imagem):
    """Extrai valores numéricos com tratamento robusto de formatos."""
    try:
        if imagem is None:
            return None

        # OCR com configuração otimizada
        texto = pytesseract.image_to_string(imagem, config='--psm 6')
        
        # Expressão regular aprimorada
        numeros = re.findall(r"[\d.,]+", texto)
        
        # Função de parse seguro
        def parse_num(num_str):
            try:
                # Remove caracteres inválidos e trata múltiplos separadores
                clean = num_str.replace(' ', '').replace(',', '.')
                parts = clean.split('.')
                
                if len(parts) > 1:
                    # Combina parte inteira e decimal
                    return float(f"{''.join(parts[:-1])}.{parts[-1]}")
                return float(clean)
            except:
                return 0.0

        if len(numeros) >= 2:
            return {
                "Open": parse_num(numeros[0]),
                "Current Price": parse_num(numeros[1])
            }
        return None
        
    except Exception as e:
        logging.error(f"Erro na extração: {str(e)} | Texto: '{texto}'")
        return None

def obter_valor_banca(tentativas=5):
    """Obtém o saldo da conta com tratamento avançado de OCR."""
    for tentativa in range(tentativas):
        try:
            # Captura da região
            screenshot = ImageGrab.grab(bbox=COORD_BANCA)
            img = np.array(screenshot)
            
            # Pré-processamento intensivo
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            gray = cv2.convertScaleAbs(gray, alpha=1.8, beta=40)
            thresh = cv2.threshold(gray, 0, 255, 
                                 cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            # OCR com configuração especializada
            texto = pytesseract.image_to_string(
                thresh, 
                config='--psm 6 -c tessedit_char_whitelist=0123456789.,'
            )
            
            # Limpeza avançada do texto
            texto_limpo = (
                texto.strip()
                .replace(" ", "")
                .replace(",", ".")  # Unifica separadores decimais
            )
            
            # Tratamento de múltiplos pontos
            partes = texto_limpo.split('.')
            if len(partes) > 1:
                texto_final = ''.join(partes[:-1]) + '.' + partes[-1]
            else:
                texto_final = texto_limpo
                
            texto_final = texto_final.lstrip('.')  # Remove pontos iniciais
            
            # Conversão final
            valor = float(texto_final) if texto_final else None
            
            if valor:
                print(f"💰 Valor detectado da banca: {valor:,.2f}")
                return valor
                
            raise ValueError("Valor inválido")
            
        except Exception as e:
            logging.warning(f"Tentativa {tentativa+1}/{tentativas} falhou: {str(e)} | Texto: '{texto}'")
            time.sleep(1)
    return None

def take_region_screenshot(x, y, width, height):
    """Captura uma região específica com tratamento de erro."""
    try:
        screenshot = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    except Exception as e:
        logging.error(f"Falha na captura: {str(e)}")
        return None

def ler_tempo_com_ocr(imagem):
    """Lê o tempo restante com fallback seguro."""
    try:
        if imagem is None or imagem.size == 0:
            return "0000"
            
        # Melhoria de qualidade
        lab = cv2.cvtColor(imagem, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8,8))
        l_clahe = clahe.apply(l)
        processed = cv2.merge((l_clahe, a, b))
        final = cv2.cvtColor(processed, cv2.COLOR_LAB2BGR)
        
        # OCR com filtro numérico
        texto = pytesseract.image_to_string(
            final, 
            config='--psm 6 -c tessedit_char_whitelist=0123456789'
        )
        return re.sub(r"[^\d]", "", texto).zfill(4)[:4]
        
    except Exception as e:
        logging.error(f"Erro na leitura do tempo: {str(e)}")
        return "0000"