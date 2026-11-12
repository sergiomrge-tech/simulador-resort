"""Modelo de referência do contrato State.prog.debt, em centavos; não é runtime UE."""
from copy import deepcopy
from decimal import Decimal


def cents(reais):
    return int(Decimal(str(reais))*100)


def migrate(state, config, day):
    result=deepcopy(state)
    prog=result.setdefault('prog',{})
    if 'debt' not in prog:
        prog['debt']={'version':config['schema_version'],'principal_cents':cents(config['principal']),
                      'paid_cents':0,'created_day':day,'last_payment_day':day,'last_reminder_day':0,
                      'intro_seen':False,'milestones_seen':[],'finale_seen':False}
    return result


def pending(state, config, demo=False):
    d=state['prog']['debt'];paid=d['paid_cents'];principal=d['principal_cents']
    marks=[m['id'] for m in config['milestones'] if paid>=int(Decimal(str(m['fraction']))*principal)
           and m['id'] not in d['milestones_seen']]
    return marks,not demo and paid==principal and not d['finale_seen']


def pay(state, config, amount_cents, day, demo=False, save_ok=True):
    """Rejeita integralmente; só retorna estado alterado quando a gravação foi aceita."""
    original=deepcopy(state);result=migrate(state,config,day);d=result['prog']['debt']
    paid=d['paid_cents'];principal=d['principal_cents'];cap=min(principal,cents(config['demo_payment_cap'])) if demo else principal
    cash=result['money_cents']
    valid=(type(amount_cents) is int and amount_cents>0 and amount_cents<=principal-paid
           and amount_cents<=cash and amount_cents<=cap-paid)
    if not valid or not save_ok:return original,False
    result['money_cents']-=amount_cents;d['paid_cents']+=amount_cents;d['last_payment_day']=day
    # O ledger do Book e day_out também fazem parte do rollback no C++.
    return result,True


def remind(state, config, day, demo=False):
    result=migrate(state,config,day);d=result['prog']['debt']
    cap=min(d['principal_cents'],cents(config['demo_payment_cap'])) if demo else d['principal_cents']
    due=(d['paid_cents']<cap and day-max(d['created_day'],d['last_payment_day'],d['last_reminder_day'])>=config['reminder_every_days'])
    if due:d['last_reminder_day']=day
    return result,due
