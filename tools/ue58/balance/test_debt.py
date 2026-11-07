"""Testes do contrato proposto e da conciliação, sem Unreal."""
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('balance_model',HERE.parent/'balance_model.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=m.read_data()

def make(demo=False):
 x=m.Model(d,'medio',0,{'before_hotel_share':0,'after_hotel_share':0},demo)
 x.day=1;x.money=1100000;x.reserve=1200;x.income=Counter();x.expenses=Counter()
 return x

x=make();start=x.money
for amount in [0,-1,True,1.5,None,110000001]:assert x.pay_debt(amount)==0
assert x.money==start and x.debt_paid_cents==0
assert x.pay_debt(1)==1 and x.debt_paid_cents==1
assert x.pay_debt(24999999)==24999999 and 'divida:quarter' in x.milestones
assert x.pay_debt(75000000)==75000000
assert x.debt_paid_cents==100000000 and 'divida_quitada' in x.milestones
assert all('divida:'+k in x.milestones for k in ['quarter','half','three_quarters'])
assert x.expenses['divida']==1000000 and abs(start-x.money-1000000)<1e-8
assert x.pay_debt(1)==0
x=make();x.money=1;assert x.pay_debt(101)==0 and x.money==1
x=make(True);assert x.pay_debt(25000000)==25000000 and x.pay_debt(1)==0
assert 'divida_quitada' not in x.milestones
x.day=15;x.debt_day();assert x.debt_reminders==0  # não cobrar pagamento indisponível na demo
x=make();x.day=8;x.debt_day();assert x.debt_reminders==1 and x.money==1100000
x.day=15;x.debt_day();assert x.debt_reminders==2 and x.money==1100000
x=make();x.money=1200;x.reserve=1200;x.income['teste']=100000;x.debt_policy={'before_hotel_share':.5,'after_hotel_share':.5};x.debt_day();assert x.debt_paid_cents==0
print('PASS: centavos, transação, recusa sem débito, 25/50/75/100%, conservação de caixa, teto demo e lembrete sem juros/multa.')
