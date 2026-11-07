"""Portuguese of Portugal (pt-PT) from the Brazilian source (04/11, Sergio: "termine as traduções").

The game is written in pt-BR; pt-PT keeps the text and the Brazilian setting (R$, names, the beach) and changes what a
Portuguese player reads as Brazilian: vocabulary (celular -> telemóvel, ônibus -> autocarro, sorvete -> gelado...), the
gerund after estar/ficar/continuar/andar ("está fazendo" -> "está a fazer") and the open-vowel spellings (prêmio ->
prémio, tênis -> ténis, econômico -> económico). "Você" stays (accepted and neutral in games). A native review is still
listed in PENDENCIAS. Writes Content/Localization/Mare/pt-PT.json (every string and LOCTEXT of source.json).
    python tools/ue58/i18n_pt_pt.py
"""
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[2] / 'unreal' / 'MareAlta' / 'Content' / 'Localization' / 'Mare'

WORDS = {
    'celular': 'telemóvel', 'celulares': 'telemóveis', 'ônibus': 'autocarro',
    'sorvete': 'gelado', 'sorvetes': 'gelados', 'sorveteria': 'geladaria', 'picolé': 'gelado de pau', 'picolés': 'gelados de pau',
    'suco': 'sumo', 'sucos': 'sumos', 'geladeira': 'frigorífico', 'geladeiras': 'frigoríficos',
    'banheiro': 'casa de banho', 'banheiros': 'casas de banho', 'tela': 'ecrã', 'telas': 'ecrãs',
    'garçom': 'empregado de mesa', 'garçons': 'empregados de mesa', 'garçonete': 'empregada de mesa',
    'equipe': 'equipa', 'equipes': 'equipas', 'arquivo': 'ficheiro', 'arquivos': 'ficheiros',
    'usuário': 'utilizador', 'usuários': 'utilizadores', 'registro': 'registo', 'registros': 'registos',
    'xícara': 'chávena', 'xícaras': 'chávenas', 'trem': 'comboio', 'abacaxi': 'ananás', 'abacaxis': 'ananases',
    'bermuda': 'calções', 'bermudas': 'calções', 'sunga': 'calções de banho', 'mouse': 'rato',
    'controle': 'comando', 'controles': 'comandos', 'esporte': 'desporto', 'esportes': 'desportos',
    'academia': 'ginásio', 'cardápio': 'ementa', 'cardápios': 'ementas', 'aluguel': 'aluguer', 'aluguéis': 'alugueres',
    'lanchonete': 'snack-bar', 'pegar': 'apanhar', 'pega': 'apanha', 'pegue': 'apanhe', 'pegou': 'apanhou', 'pego': 'apanho',
    'planejar': 'planear', 'planejamento': 'planeamento', 'contato': 'contacto', 'contatos': 'contactos',
    'grama': 'relva', 'gramado': 'relvado', 'fila': 'fila', 'café da manhã': 'pequeno-almoço',
    'prêmio': 'prémio', 'prêmios': 'prémios', 'tênis': 'ténis', 'quilômetro': 'quilómetro', 'quilômetros': 'quilómetros',
    'gênero': 'género', 'fenômeno': 'fenómeno', 'cômodo': 'cómodo', 'cômodos': 'cómodos', 'bebê': 'bebé', 'bebês': 'bebés',
    'Antônio': 'António', 'ônus': 'ónus', 'crônica': 'crónica', 'anônimo': 'anónimo', 'tônica': 'tónica',
    'econômico': 'económico', 'econômica': 'económica', 'gastronômico': 'gastronómico', 'gastronômica': 'gastronómica',
    'eletrônico': 'eletrónico', 'eletrônica': 'eletrónica', 'polêmica': 'polémica', 'acadêmico': 'académico',
    'estoque': 'stock', 'estoques': 'stocks', 'oi': 'olá', 'cooler': 'geleira', 'coolers': 'geleiras',
    'time': 'equipa', 'parabéns': 'parabéns', 'moça': 'rapariga', 'moço': 'rapaz', 'cara': 'tipo',
}
# "time"/"cara" are too ambiguous in mixed text (English QA strings, "cara de"): only replaced in these phrases.
UNSAFE = {'time', 'cara', 'fila', 'parabéns'}


def keep_case(word, repl):
    if word.isupper():
        return repl.upper()
    if word[:1].isupper():
        return repl[:1].upper() + repl[1:]
    return repl


def vocab(text):
    for src in sorted(WORDS, key=len, reverse=True):
        if src in UNSAFE:
            continue
        dst = WORDS[src]
        pat = re.compile(r'(?<![\w])(' + re.escape(src) + r')(?![\w])', re.IGNORECASE)
        text = pat.sub(lambda m: keep_case(m.group(1), dst), text)
    return text


AUX = r'(est(?:ou|á|ás|amos|ão|ava|avas|ávamos|avam|ar|ive|eve|ivesse|eja|ejam|ando)|fic(?:a|as|am|ar|ou|ava|amos|o)|continu(?:a|as|am|ar|ou|e|o)|and(?:a|as|am|ar|o|ou)|anda-se)'
GER = re.compile(AUX + r'(\s+)(?:(se|me|te|nos|lhe|lhes)\s+)?([a-záéíóúâêôãõç]+?)(ando|endo|indo|ondo)\b', re.IGNORECASE)


def gerund(text):
    def fix(m):
        aux, sp, pron, stem, end = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5).lower()
        inf = stem + {'ando': 'ar', 'endo': 'er', 'indo': 'ir', 'ondo': 'or'}[end]
        return f'{aux}{sp}a {inf}' + (f'-{pron}' if pron else '')
    return GER.sub(fix, text)


def to_pt(text):
    if not text or not re.search(r'[a-zà-ú]', text):
        return text
    return gerund(vocab(text))


def main():
    src = json.loads((OUT / 'source.json').read_text(encoding='utf-8'))
    tr = {'loctext': {k: to_pt(v) for k, v in src['loctext'].items()}, 'strings': {s: to_pt(s) for s in src['strings']}}
    (OUT / 'pt-PT.json').write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding='utf-8')
    changed = sum(1 for s in src['strings'] if tr['strings'][s] != s)
    print(f'pt-PT: {len(tr["strings"])} strings ({changed} adapted), {len(tr["loctext"])} loctext')


if __name__ == '__main__':
    main()
