"""PIE round-trip regression; requires the editor's explicit isolated QA profile.

Launch UE with -MareSaveRoot=D:/CodexTemp/ue58-persistence-20261027, MCP on 8000.
Run with --seed to recreate this disposable fixture before the first PIE session.
No original save or game installation is opened or modified.
"""
import argparse
import json
import time
import math
from pathlib import Path
from mcp_client import UnrealClient

PROJECT = Path(__file__).resolve().parents[2]
PROFILE = Path('D:/CodexTemp/ue58-persistence-20261027')
SLOT = PROFILE / 'slot1.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def seed():
    data = PROJECT / 'unreal/MareAlta/Content/Data'
    state = load(data / 'default_save.json')
    world = load(data / 'world.json')
    state.update(money=1000, minutes=600, day=1)
    state['company'].update(created=True, name='Teste de persistência', physical=True,
                            kiosk_open=False, carry='', staff_carry='')
    state['staff']['atendente'] = False
    state['unlocked']['kiosk_tables'] = True
    state['qa_unknown'] = {'preserve': ['future-key', 17]}
    state['ue_orders'] = {'qa-order': {'name': 'Ana', 'items': ['suco', 'coco_gelado'],
                                      'remaining': ['coco_gelado'], 'unknown': 'keep'}}

    def guest(identifier, name, stage, counter, table, plan, delivered, position, elapsed=0):
        return dict(id=identifier, name=name, variant=3, stage=stage, counter=counter,
                    table=table, order='qa-order' if counter == 0 else '', plan=plan,
                    delivered=delivered, position=position, destination=position,
                    yaw=90, elapsed=elapsed, consumed=False, future_meta={'favorite': 'mar'})

    spot = world['tables'][4]['pos']
    seated = [spot[0] * 100, spot[2] * 100, spot[1] * 100 + 88]
    state['ue_dirty_tables'] = {'1': ['suco', 'coco_gelado', 'sorvete_morango', 'batata_frita']}
    state['ue_kiosk'] = dict(version=1, day=1, arrival=30, unknown_snapshot='keep', guests=[
        guest('qa-partial', 'Ana', 2, 0, 0, ['suco', 'coco_gelado'], ['suco'], [3870, -1653, 98]),
        guest('qa-seated', 'Maria', 4, -1, 2, ['porcao_peixe'], ['porcao_peixe'], seated, 1)],
        player={'position': [3870, -1405, 100], 'view': [0, 0, -90], 'future_player': 'keep'},
        doors={'Porta da casa': False, 'Porta do banheiro': False})
    PROFILE.mkdir(parents=True, exist_ok=True)
    SLOT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def run(client):
    report = {'checks': [], 'snapshots': {}}

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report['checks'].append(name)

    def probe(phase='inspect', dish=''):
        value = json.loads(client.call('mare_mcp.MareMigrationTools', 'gameplay_probe', phase=phase, dish=dish))
        if 'error' in value:
            raise AssertionError(value['error'])
        return value

    def start():
        client.call('EditorToolset.EditorAppToolset', 'StartPIE', options={
            'bSimulate': False, 'playMode': 'PlayMode_InViewPort', 'warmupSeconds': .25})
        return probe('pause')

    def stop():
        client.call('EditorToolset.EditorAppToolset', 'StopPIE')

    def person(snapshot, identifier):
        return next(p for p in snapshot['people'] if p['save_id'] == identifier)

    def retain(name, snapshot):
        report['snapshots'][name] = snapshot
        return snapshot

    try:
        first = retain('initial', start())
        check('restore partial order with one held product', person(first, 'qa-partial')['held_count'] == 1)
        check('restore consumed-product history', person(first, 'qa-partial')['delivered'] == ['suco'])
        check('restore seated customer pose', 'EATING' in person(first, 'qa-seated')['stage'])
        check('restore four matching used dishes', len(first['used_dishes']) == 4)
        check('reserve busy and dirty seats', all(i in first['reserved_tables'] for i in (0, 1, 2)))
        probe('save')
        stop()
        second = retain('partial_reload', start())
        check('reload does not charge or pay again', second['cash'] == 1000)
        check('no duplicated held products', person(second, 'qa-partial')['held_count'] == 1)
        check('no duplicated used dishes', len(second['used_dishes']) == 4)
        probe('resume')
        probe('position_fridge')
        probe('interact')
        picked = probe('pickup', 'coco_gelado')
        probe('pause')
        stock = load(SLOT)['stock']
        stop()
        carrying = retain('carrying_reload', start())
        check('player carry survives reload', carrying['carry'] == 'coco_gelado')
        check('stock deducted once across reload', load(SLOT)['stock'] == stock)
        probe('resume')
        probe('position_customer')
        delivered = retain('delivered', probe('interact'))
        atomic = load(SLOT)
        saved = next(p for p in atomic['ue_kiosk']['guests'] if p['id'] == 'qa-partial')
        check('automatic payment exactly once', delivered['cash'] == 1012 and delivered['carry'] == '')
        check('completed order removed atomically', 'qa-order' not in atomic['ue_orders'])
        check('transaction snapshot includes final product', sorted(saved['delivered']) == ['coco_gelado', 'suco'] and saved['stage'] == 3)
        check('unknown customer fields preserved', saved['future_meta'] == {'favorite': 'mar'})
        probe('pause')
        stop()
        complete = retain('completed_reload', start())
        check('completed sale survives reload without duplicate payment', complete['cash'] == 1012)
        check('customer carries both paid products', person(complete, 'qa-partial')['held_count'] == 2)
        check('cleaning target removes its matching dishes', len(probe('clean', '1')['used_dishes']) == 0)
        for _ in range(20):
            probe('resume')
            time.sleep(1)
            consumed = probe('pause')
            if person(consumed, 'qa-seated')['consumed']:
                break
        retain('consumed', consumed)
        maria = person(consumed, 'qa-seated')
        check('seated customer finishes consumption', maria['consumed'] and 'EATING' in maria['stage'])
        cleaned = probe('clean', '2')
        check('clean chair remains reserved while occupied', 2 in cleaned['reserved_tables'])
        probe('resume')
        time.sleep(.5)
        cleaned = probe('pause')
        check('cleaned dishes do not respawn', not any('Table_2' in p['table'] for p in cleaned['used_dishes']))
        probe('save')
        stop()
        after_clean = retain('cleaned_reload', start())
        check('consumption flag survives reload', person(after_clean, 'qa-seated')['consumed'])
        check('cleaned dishes stay absent after reload', not any('Table_2' in p['table'] for p in after_clean['used_dishes']))
        probe('sleep')
        sleeping = load(SLOT)
        check('sleep saves no old customers or orders', not sleeping['ue_kiosk']['guests'] and not sleeping['ue_orders'])
        stop()
        morning = retain('morning', start())
        check('no customers resurrect next day', not morning['people'] and not morning['open'])
        current = load(SLOT)
        check('unknown root fields preserved', current['qa_unknown'] == {'preserve': ['future-key', 17]})
        check('unknown native snapshot fields preserved', current['ue_kiosk']['unknown_snapshot'] == 'keep')
        check('unknown player fields preserved', current['ue_kiosk']['player']['future_player'] == 'keep')
        stop()
        current = load(SLOT)
        current['ue_orders'] = {'legacy-unbound': {'name': 'Rafael', 'remaining': ['coco_gelado'], 'old_field': 'keep'}}
        current['ue_kiosk']['guests'] = []
        SLOT.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
        unbound = retain('legacy_recovered', start())
        check('old unbound order gains a physical customer', any(p['order'] == 'legacy-unbound' for p in unbound['people']))
        check('legacy remaining-only order restores only unpaid item', next(p for p in unbound['people'] if p['order'] == 'legacy-unbound')['plan'] == ['coco_gelado'])
        probe('save')
        stop()
        unbound = start()
        check('recovered arrival survives reload without freezing', any(p['order'] == 'legacy-unbound' and 'APPROACHING' in p['stage'] for p in unbound['people']))
        for _ in range(25):
            probe('resume')
            time.sleep(1)
            unbound = probe('pause')
            if any(p['order'] == 'legacy-unbound' and 'PRODUCTS' in p['stage'] for p in unbound['people']):
                break
        retain('legacy_at_counter', unbound)
        check('recorded order can reach counter while closed', any(p['order'] == 'legacy-unbound' and 'PRODUCTS' in p['stage'] for p in unbound['people']))
        check('recovery never repeats earlier payment', unbound['cash'] == 1012)
        stop()
        current = load(SLOT)
        current['minutes'] = 600
        current['company']['kiosk_open'] = True
        current['ue_kiosk']['guests'].append(dict(id='qa-neworder', name='João', variant=0,
            stage=1, counter=1, table=2, order='', plan=[], delivered=[],
            position=[3730, -1653, 98], destination=[3730, -1653, 98], yaw=90,
            elapsed=0, consumed=False))
        SLOT.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
        start()
        probe('resume')
        probe('position_customer', '1')
        created = retain('new_order', probe('interact'))
        record = person(created, 'qa-neworder')
        atomic = load(SLOT)
        saved = next(p for p in atomic['ue_kiosk']['guests'] if p['id'] == 'qa-neworder')
        check('new order transaction already binds customer id', bool(record['order']) and saved['order'] == record['order'] and saved['stage'] == 2)
        check('noting order never charges or consumes stock', created['cash'] == 1012 and atomic['stock'] == current['stock'])
        probe('pause')
        stop()
        restored = retain('new_order_reload', start())
        check('new order survives reload with same owner', person(restored, 'qa-neworder')['order'] == record['order'])
        check('no extra orphan customer after transaction reload', len(restored['people']) == 2)
        stop()
        current = load(SLOT)
        definitions = load(PROJECT / 'unreal/MareAlta/Content/Data/definitions.json')
        current['staff']['atendente'] = True
        current['company'].update(kiosk_open=False, carry='', staff_carry='coco_gelado')
        for item, amount in definitions['dishes']['coco_gelado']['uses'].items():
            current['stock'][item] -= amount
        current['ue_dirty_tables'] = {}
        current['ue_orders'] = {'staff-order': {'name': 'Ana', 'items': ['coco_gelado'], 'remaining': ['coco_gelado']}}
        current['ue_kiosk']['guests'] = [dict(id='qa-staff-customer', name='Ana', variant=3,
            stage=2, counter=0, table=0, order='staff-order', plan=['coco_gelado'], delivered=[],
            position=[3870, -1653, 98], destination=[3870, -1653, 98], yaw=90, elapsed=0, consumed=False)]
        current['ue_kiosk']['attendant'] = {'position': [3920, -1240, 98], 'yaw': -90, 'future_staff': 'keep'}
        current['ue_kiosk']['player'] = {'position': [3670, -1300, 100], 'view': [0, 0, -90]}
        SLOT.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding='utf-8')
        staff = retain('staff_carry', start())
        employee = [p for p in staff['people'] if p['employee']]
        check('restore exactly one attendant with their held product', len(employee) == 1 and employee[0]['held_count'] == 1)
        check('restore never charges another hire fee', staff['cash'] == current['money'])
        stop()
        staff = start()
        check('attendant reload does not duplicate withdrawn stock', load(SLOT)['stock'] == current['stock'])
        for _ in range(20):
            probe('resume')
            time.sleep(.5)
            staff = probe('pause')
            if staff['cash'] > current['money']:
                break
        retain('staff_delivered', staff)
        check('restored attendant resumes delivery and payment once', staff['cash'] == current['money'] + 12)
        stop()
        staff = retain('staff_after_delivery_reload', start())
        check('staff delivery reload preserves exact payment and stock', staff['cash'] == current['money'] + 12 and load(SLOT)['stock'] == current['stock'])
        check('delivered staff product is not resurrected in hand', all(p['held_count'] == 0 for p in staff['people'] if p['employee']))
        check('unknown attendant fields preserved', load(SLOT)['ue_kiosk']['attendant']['future_staff'] == 'keep')
        probe('resume')
        probe('position_door')
        door = probe('interact')
        probe('pause')
        probe('save')
        stop()
        door_reload = retain('open_door_reload', start())
        check('open house door survives reload', any(d['name'] == 'Porta da casa' and d['opened'] for d in door_reload['doors']))
        check('player position survives reload', math.dist(door['location'], door_reload['location']) < 20)
        report['passed'] = True
        return report
    finally:
        try:
            stop()
        except Exception:
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--output', default='D:/CodexTemp/ue58-persistence-report.json')
    args = parser.parse_args()
    connection = UnrealClient()
    status = json.loads(connection.call('mare_mcp.MareMigrationTools', 'migration_status'))
    if Path(status.get('qa_save_root', '')).resolve() != PROFILE.resolve():
        raise RuntimeError('Editor must use the exact isolated QA profile described above')
    if args.seed:
        seed()
    result = run(connection)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': result['passed'], 'checks': result['checks']}, ensure_ascii=True))
