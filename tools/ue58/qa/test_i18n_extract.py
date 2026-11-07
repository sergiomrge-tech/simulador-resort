"""Regressões: textos de unlock e títulos com hífen entram; ids não entram."""
import importlib.util
import json
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('extract',ROOT/'tools/ue58/i18n_extract.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
with tempfile.TemporaryDirectory() as tmp:
    e.ROOT=Path(tmp);data=e.ROOT/'Content/Data';data.mkdir(parents=True)
    docs={'definitions':{'chapters':[{'unlock':'Praia aberta + Escola de surfe'}]},
          'customization':{'unlock':'bar','slug':'fab:143'},
          'tutorial':{'tips':{'TableTennis':{'title':'Pingue-pongue','text':'Mova a raquete.'}}},
          'achievements':{'achievements':[{'id':'ID_NAO_LOCALIZAR','name':'Primeira conquista','description':'Conquiste algo.','condition':{'path':'/campo/nao_localizar','op':'contains','value':'chave_interna'}}],'rich_presence':[{'id':'rp_id','text':'Na praia'}]}}
    for name,d in docs.items():(data/(name+'.json')).write_text(json.dumps(d,ensure_ascii=False))
    texts=e.scan_data()
    assert {'Praia aberta + Escola de surfe','Pingue-pongue','Mova a raquete.','Primeira conquista','Conquiste algo.','Na praia'}<=texts
    assert not {'bar','fab:143','ID_NAO_LOCALIZAR','/campo/nao_localizar','contains','chave_interna','rp_id'}&texts
print('PASS: unlock de capítulo, título com hífen e textos visíveis extraídos; ids/paths/slugs/condições excluídos')
