"""Contrato genérico para 36 conquistas; validador/evaluador de referência sem Steam/UE."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PATH=ROOT/'unreal/MareAlta/Content/Data/achievements.json'


def resolve(state,path):
    node=state
    for token in path.lstrip('/').split('/'):
        key=token.replace('~1','/').replace('~0','~')
        if not isinstance(node,dict) or key not in node:return None
        node=node[key]
    return node


def evaluate(c,state):
    if 'all' in c:return all(evaluate(child,state) for child in c['all'])
    value=resolve(state,c['path'])
    agg=c.get('aggregate')
    if agg=='count':value=len(value) if isinstance(value,list) else 0
    elif agg=='sum':value=sum(v for v in value.values() if type(v) in (int,float)) if isinstance(value,dict) else 0
    target=c['value'];op=c['op']
    if op=='contains':return isinstance(value,list) and target in value
    if op=='>=':return type(value) in (int,float) and type(target) in (int,float) and value>=target
    if op=='==':return type(value) is type(target) and value==target
    raise ValueError('comparação desconhecida')


def check():
    errors=[]
    def error(key,msg):errors.append({'arquivo':'achievements.json','campo':key,'problema':msg})
    try:d=json.loads(PATH.read_text());original=json.loads((ROOT/'docs/steam/conquistas.json').read_text())
    except (OSError,ValueError) as e:return [{'arquivo':str(PATH),'campo':'/','problema':str(e)}]
    rows=d.get('achievements',[]);ids=[a['id'] for a in rows]
    if len(rows)!=36 or set(ids)!={a['id'] for a in original['achievements']} or len(set(ids))!=36:error('/achievements','as 36 ids editoriais devem permanecer únicas')
    def validate(c,key):
        if 'all' in c:
            if set(c)!={'all'} or not isinstance(c['all'],list) or not c['all']:error(key,'all inválido');return
            for child in c['all']:validate(child,key)
        else:
            if set(c)-{'path','aggregate','op','value'} or not {'path','op','value'}<=set(c):error(key,'folha inválida');return
            if not isinstance(c['path'],str) or not c['path'].startswith('/') or '*' in c['path']:error(key,'JSON Pointer inválido')
            if c['op'] not in ['==','>=','contains']:error(key,'op não genérico')
            if c.get('aggregate') not in [None,'sum','count']:error(key,'agregador desconhecido')
    editorial={a['id']:a for a in original['achievements']}
    for a in rows:
        validate(a['condition'],'/'+a['id'])
        source=editorial.get(a['id'],{})
        if a.get('demo')!=source.get('demo') or a.get('hidden')!=source.get('hidden'):error(a['id'],'flag editorial alterada')
        for key in ['name','description']:
            if a.get(key)!=source.get(key,{}).get('pt-BR'):error(a['id']+'/'+key,'texto editorial alterado')
        if not a.get('_source'):error(a['id'],'falta proveniência do campo')
    if len(d.get('rich_presence',[]))!=10:error('/rich_presence','esperados 10 textos de presença')
    # Não pode conceder nada em save vazio nem tratar bool como contador.
    for a in rows:
        if evaluate(a['condition'],{}):error(a['id'],'conquista concedida em save vazio')
    return errors


def self_test():
    assert not check()
    base={'path':'/n','op':'>=','value':1}
    for v,expected in [(None,False),(False,False),(True,False),(0,False),(1,True),(2,True),('1',False)]:assert evaluate(base,{'n':v})==expected
    assert evaluate({'all':[base,{'path':'/ready','op':'==','value':True}]},{'n':1,'ready':True})
    assert not evaluate({'all':[base,{'path':'/ready','op':'==','value':True}]},{'n':1,'ready':1})
    assert evaluate({'path':'/fish','aggregate':'sum','op':'>=','value':2},{'fish':{'a':1,'b':1,'debug':'ignored'}})
    assert evaluate({'path':'/album','aggregate':'count','op':'>=','value':2},{'album':[{},{}]})
    assert evaluate({'path':'/known','op':'contains','value':'coqueiro'},{'known':['coqueiro']})
    assert not evaluate({'path':'/known','op':'contains','value':'coqueiro'},{'known':'coqueiro'})
    print('PASS: 36 conquistas, IDs/flags/textos editoriais; limiares, tipos, AND, soma, contagem e contains genéricos')
if __name__=='__main__':self_test()
