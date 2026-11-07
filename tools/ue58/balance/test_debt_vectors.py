"""Vetores fixos contra o contrato persistente e o modelo econômico existente."""
import importlib.util
import json
from copy import deepcopy
from collections import Counter
from pathlib import Path
from debt_contract import migrate,pay,pending,remind
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
config=json.loads((ROOT/'unreal/MareAlta/Content/Data/debt.json').read_text())
spec=importlib.util.spec_from_file_location('balance_model',HERE.parent/'balance_model.py')
balance=importlib.util.module_from_spec(spec);spec.loader.exec_module(balance)
count=0
for case in json.loads((HERE/'debt_vectors.json').read_text())['cases']:
 state=migrate(case['initial'],config,case['created_day']);demo=case['demo']
 for a in case['actions']:
  before=deepcopy(state)
  if 'pay' in a:
   amount={'NaN':float('nan'),'Infinity':float('inf')}.get(a['pay'],a['pay']) if isinstance(a['pay'],str) else a['pay']
   state,ok=pay(state,config,amount,a['day'],demo,a['save_ok']);d=state['prog']['debt'];e=a['expect']
   marks,finale=pending(state,config,demo)
   actual=dict(ok=ok,paid_cents=d['paid_cents'],balance_cents=d['principal_cents']-d['paid_cents'],money_cents=state['money_cents'],pending=marks,finale=finale)
   assert actual==e,(case['id'],a,actual)
   if not ok:assert state==before
   if a['save_ok']:
    m=balance.Model(balance.read_data(),'medio',0,None,demo);m.income=Counter();m.expenses=Counter();m.money=before['money_cents']/100;m.debt_paid_cents=before['prog']['debt']['paid_cents'];m.day=a['day']
    got=m.pay_debt(amount);assert (got>0)==ok,(case['id'],'economic parity')
    assert m.debt_paid_cents==d['paid_cents'] and round(m.money*100)==state['money_cents']
  elif 'remind' in a:
   state,due=remind(state,config,a['remind'],demo);assert due==a['expect_reminder'],(case['id'],a)
   assert state['money_cents']==before['money_cents']
   assert state['prog']['debt']['paid_cents']==before['prog']['debt']['paid_cents']
  elif 'migrate' in a:
   assert migrate(state,dict(config,principal=2000000),99)==state
   for k,v in case['initial'].items():
    if k!='prog':assert state[k]==v
   for k,v in case['initial'].get('prog',{}).items():assert state['prog'][k]==v
  elif 'ack' in a:
   marks,finale=pending(state,config,demo);state['prog']['debt']['milestones_seen']+=marks
   if finale:state['prog']['debt']['finale_seen']=True
  else:assert pending(state,config,demo)==(a['pending'],a['finale'])
  # Load/save JSON não perde centavos nem reconhecimentos.
  assert json.loads(json.dumps(state))==state
  count+=1
print(f'PASS: {len(json.loads((HERE/"debt_vectors.json").read_text())["cases"])} vetores, {count} ações; persistência, pagamentos, lembretes e paridade com balance_model.')
