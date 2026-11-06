"""Validação dos artefatos de simulação e dos limites editoriais da loja."""
import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('balance_model',HERE.parent/'balance_model.py')
model=importlib.util.module_from_spec(spec);spec.loader.exec_module(model)
data=model.read_data()
changes=json.loads((HERE/'proposed.json').read_text())
model.overlay(data,changes)
count=0
for folder in ['results','sensitivity_lento','sensitivity_rapido']:
    path=HERE/folder
    summary=json.loads((path/'summary.json').read_text())
    conf=json.loads((path/'configuracao.json').read_text())
    assert conf['mudancas']==changes
    assert conf['sementes']==list(range(30 if folder=='results' else 10))
    for rel,digest in json.loads((path/'inputs_sha256.json').read_text()).items():
        assert hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==digest,rel
    for sc in ['atual','proposto']:
        for profile in model.PROFILES:
            s=summary[sc][profile]
            assert s['sementes']==len(conf['sementes'])
            assert s['censurados_compras']==s['censurados_campanha']==0
            with (path/f'{sc}_{profile}_diario_seed0.csv').open() as f:rs=list(csv.DictReader(f))
            with (path/f'{sc}_{profile}_sementes.csv').open() as f:seeds=list(csv.DictReader(f))
            assert len(seeds)==s['sementes']
            for key in ['grand_hotel','salao_jogos','tela_fim_ea','campanha_completa','todas_compras']:
                values=[int(r[key]) for r in seeds if r[key]]
                assert model.quantile(values,.5)==s['marcos'][key]['p50']
                assert s['marcos'][key]['concluidos']==len(values)
            cash=data['default_save']['money']
            xp=0
            for day,r in enumerate(rs,1):
                assert int(r['dia'])==day
                income=sum(float(v or 0) for k,v in r.items() if k.startswith('renda_') and k!='renda_total')
                expense=sum(float(v or 0) for k,v in r.items() if k.startswith('despesa_'))
                assert abs(income-float(r['renda_total']))<.15
                assert abs(expense-float(r['despesas_total']))<.15
                assert abs(cash+float(r['renda_total'])-float(r['despesas_total'])-float(r['caixa']))<.04
                assert float(r['fama_xp'])>=xp
                xp=float(r['fama_xp']);cash=float(r['caixa'])
                assert int(r['fama_nivel'])==sum(xp>=x for x in model.FAME)
                assert 0<=int(r['hotel_ocupados'])<=32
                assert int(r['segundos_ativos'])<=conf['perfis'][profile]['active_seconds']
                assert math.isfinite(cash)
            count+=1
expected={'en','es','de','fr','zh-Hans','ja','ru','ko','it','pl','nl','pt-PT'}
translation=(ROOT/'docs/steam/loja_traducoes.md').read_text()
assert set(re.findall(r'^## ([\w-]+) —',translation,re.M))==expected
assert len(re.findall(r'^### Descrição longa$',translation,re.M))==12
shorts=0
for path in (ROOT/'docs/steam').glob('loja*.md'):
    texts=re.findall(r'###? Descrição curta\n\n([^\n]+)',path.read_text())
    assert all(0<len(s)<=300 for s in texts),path
    shorts+=len(texts)
assert shorts==14
report=(ROOT/'docs/ue58/BALANCEAMENTO.md').read_text()
assert '## MUDANÇAS PROPOSTAS' in report
for sc in ['Atual','Proposto']:
    for p in model.PROFILES:assert f'### {sc} — {p}, semente 0' in report
print(f'PASS: {count} séries diárias, 300 trajetórias nos resumos, caixa/fontes/despesas, fama, capacidade, hashes, configuração, propostas, 12 idiomas e {shorts} descrições curtas')
