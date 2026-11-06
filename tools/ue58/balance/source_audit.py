"""Registra a presença das novidades pedidas sem simular sistemas inexistentes.

A extração é textual e conservadora. Não equivale a executar ou compilar C++.
Uma revisão de Source muda os hashes e exige conferir de novo o modelo.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/'unreal/MareAlta/Source/MareAlta'
DATA=ROOT/'unreal/MareAlta/Content/Data'


def body(file,signature):
    path=SOURCE/file
    if not path.exists():return ''
    text=path.read_text(encoding='utf-8-sig')
    start=text.find(signature)
    if start<0:return ''
    start=text.find('{',start);depth=0
    # Os consumidores analisados não contêm chaves em literais; remover comentários
    # evita tomar um comentário de documentação como evidência de implementação.
    text=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/','',text[start:])
    for i,char in enumerate(text):
        if char=='{':depth+=1
        elif char=='}':
            depth-=1
            if depth==0:return text[:i+1]
    return ''


def audit():
    sim=(SOURCE/'MareSimulation.cpp').read_text(encoding='utf-8-sig')
    restaurant=json.loads((DATA/'restaurant.json').read_text())
    fame=body('MareSimulation.cpp','void UMareSimulation::AddFame(')
    opening=body('MareSimulation.cpp','double UMareSimulation::KioskCloseHour(')
    buying=body('MareSimulation.cpp','bool UMareSimulation::BuyExpansion(')
    sleep=body('MareSimulation.cpp','void UMareSimulation::Sleep(')
    rental=body('MareBusiness.cpp','bool UMareSimulation::IsBusinessOpen(')+body('MareRental.cpp','void UMareSimulation::RentalHour(')
    rental_price=body('MareRental.cpp','double UMareSimulation::RentalPrice(')+body('MareSimulation.cpp','double UMareSimulation::BusinessRate(')
    hotel_data=DATA/'hotel_events.json';hotel_source=SOURCE/'MareHotelEvents.cpp'
    flags={
        'hotel_events':hotel_data.exists() and hotel_source.exists(),
        'fama_negativa':bool(fame) and not re.search(r'if\s*\(\s*Xp\s*<=\s*0\s*\)\s*return',fame),
        'neon_ate_21': 'TEXT("neon")' in opening+buying,
        'aluguel_fecha_tempestade': any(x in rental for x in ['IsSeaRough(', 'TEXT("tempestade")']),
        'aluguel_bonus_mare_alta':'TEXT("mare")' in rental,
        'evento_restaurante_ao_dormir':'bPast' in body('MareRestaurant.cpp','void UMareSimulation::RestaurantHour('),
        'critic':'critic' in restaurant,
        'fresh_fish':'fresh_fish' in restaurant,
    }
    inspected=['MareSimulation.cpp','MareBusiness.cpp','MareRental.cpp','MareRestaurant.cpp','MareHotelRooms.cpp','MareHotelEvents.cpp']
    return {'tipo':'inspeção textual; confirma presença, não correção funcional',
            'novidades':flags,
            'hotel_events_arquivos':{'json':hotel_data.exists(),'cpp':hotel_source.exists()},
            'fonte_sha256':{f:hashlib.sha256((SOURCE/f).read_bytes()).hexdigest() for f in inspected},
            'relogio':{'minutos_jogo_por_segundo':1,'inicio_dia':8,'fim_dia':24,'minutos_reais_dia':16},
            'nota':'Sistemas presentes foram revistos. Fórmulas monetárias seguem C++; tempos de ações são hipóteses explícitas.'}


if __name__=='__main__':print(json.dumps(audit(),ensure_ascii=False,indent=2))
