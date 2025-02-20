import re
import logging
from datetime import datetime, timedelta

def extrair_informacoes(mensagem):
    try:
        linhas = [linha.strip() for linha in mensagem.split('\n') if linha.strip()]

        # Extrair Ativo
        ativo = None
        for linha in linhas:
            if "🌎 Ativo:" in linha:
                ativo = linha.split("🌎 Ativo:")[1].strip()
                break

        # Extrair Ação (Compra/Venda)
        acao = None
        for linha in linhas:
            if "🟥Direção:🔽ABAIXO🔽" in linha:
                acao = "VENDIDO"
                break
            elif "🟩Direção:🔼ACIMA🔼" in linha:
                acao = "COMPRADO"
                break

        # Extrair Horário
        hora_str = None
        for linha in linhas:
            if "⏰ Entrada:" in linha:
                hora_str = linha.split("⏰ Entrada:")[1].strip()
                break

        # Extrair Tempo de Expiração
        expiracao = None
        for linha in linhas:
            if "⏳ Expiração: M2" in linha:
                expiracao = "M2"
                break
            elif "⏳ Expiração: M3" in linha:
                expiracao = "M3"
                break
            elif "⏳ Expiração: M5" in linha:
                expiracao = "M5"
                break

        if not all([ativo, acao, hora_str, expiracao]):
            raise ValueError("Padrão não reconhecido")

        return ativo, acao, hora_str, expiracao

    except Exception as e:
        logging.error(f"Erro extração: {str(e)}")
        return None, None, None, None

def calcular_tempos(hora_str):
    try:
        if not re.match(r"^\d{2}:\d{2}$", hora_str):
            raise ValueError("Formato inválido")

        hoje = datetime.now().date()
        hora = datetime.strptime(hora_str, "%H:%M").time()
        dt = datetime.combine(hoje, hora)

        if dt <= datetime.now():
            dt += timedelta(days=1)

        return dt

    except Exception as e:
        logging.error(f"Erro cálculo tempo: {str(e)}")
        raise