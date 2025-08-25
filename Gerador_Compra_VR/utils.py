import pandas as pd
from datetime import datetime
from workalendar.america import Brazil

cal = Brazil()

def dias_uteis(mes: int, ano: int, uf: str = "SP"):
    """Retorna número de dias úteis no mês considerando feriados nacionais e estaduais"""
    dias = pd.bdate_range(f"{ano}-{mes}-01", f"{ano}-{mes}-28")
    return [d for d in dias if not cal.is_holiday(d)]

def dias_uteis_periodo(inicio, fim):
    """Retorna número de dias úteis no mês considerando feriados nacionais e estaduais"""
    dias = pd.bdate_range(inicio, fim)
    return len([d for d in dias if not cal.is_holiday(d)])
