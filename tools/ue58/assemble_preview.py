"""Assemble an already tested Windows preview on D:, keeping player data out of ZIP."""
import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--qa', required=True, type=Path)
parser.add_argument('--source', type=Path, default=Path('D:/Builds/MareAltaUE58_AudioVisual_2026-10-28/Windows'))
parser.add_argument('--output', type=Path, default=Path('D:/Downloads/MareAltaResort_UE58_AudioVisual_2026-10-28'))
args = parser.parse_args()
result = json.loads((args.qa/'package-result.json').read_text(encoding='utf-8-sig'))
if not result['passed'] or not result.get('audio_mix_passed',False) or result.get('visual_review_required', True):
    raise SystemExit('Exige teste funcional e revisão visual aprovados do pacote.')
if args.output.drive.upper() != 'D:' or args.output.exists():
    raise SystemExit('Use uma pasta NOVA no D; instalações existentes não são sobrescritas.')
if Path(result['executable']).resolve() != (args.source/'MareAlta.exe').resolve():
    raise SystemExit('O executável verificado não corresponde ao pacote de origem.')
args.output.mkdir(parents=True)
shutil.copytree(args.source, args.output/'Windows', ignore=shutil.ignore_patterns('*.pdb'))
(args.output/'Jogar.cmd').write_text('@echo off\r\nstart "" "%~dp0Windows\\MareAlta.exe" -MareSaveRoot="%~dp0userdata" -UserDir="%~dp0userdata\\Unreal" -windowed -ResX=1280 -ResY=720\r\n', encoding='ascii')
(args.output/'Jogar.vbs').write_text('Option Explicit\r\nDim sh, fs, base, cmd\r\nSet sh=CreateObject("WScript.Shell")\r\nSet fs=CreateObject("Scripting.FileSystemObject")\r\nbase=fs.GetParentFolderName(WScript.ScriptFullName)\r\nsh.CurrentDirectory=base & "\\Windows"\r\ncmd=Chr(34) & base & "\\Windows\\MareAlta.exe" & Chr(34) & " -MareSaveRoot=" & Chr(34) & base & "\\userdata" & Chr(34) & " -UserDir=" & Chr(34) & base & "\\userdata\\Unreal" & Chr(34) & " -windowed -ResX=1280 -ResY=720"\r\nsh.Run cmd, 1, False\r\n', encoding='ascii')
(args.output/'LEIA-ME.txt').write_text('''MARÉ ALTA RESORT — PRÉVIA UE5.8 / ÁUDIO, VISUAL E NATAÇÃO — 28/10/2026

Abra Jogar.vbs (ou Jogar.cmd). Não precisa instalar a Unreal Engine.
Mantenha toda a pasta Windows junto dos atalhos. Saves desta prévia ficam em
userdata, ao lado dos atalhos. A versão e o progresso Godot não são alterados.

WASD: andar/nadar | Mouse: olhar | E: interagir | B: celular
Espaço: pular em terra / subir na água | Ctrl ou Shift: mergulhar
Shift em terra: correr | Esc: pausar, salvar, qualidade e sair

No celular, crie a empresa e abra o quiosque. Produtos já estão prontos:
retire nas estações dentro do quiosque e entregue aos clientes no balcão.
O pagamento é automático. Você pode contratar um único atendente.

Esta é uma PRÉVIA DA MIGRAÇÃO, com cenário, quiosque e natação para teste.
Inclui reggae instrumental original, ambiente e efeitos sem vozes, quatro volumes
no menu Esc, luz diurna/noturna, letreiros e materiais refinados.
Não equivale ao jogo inteiro convertido: outros negócios, clima completo,
vida marinha, opções completas e o restante dos capítulos continuam pendentes.
A câmera ainda não tem braços/corpo com animação de natação.

Requer Windows 64 bits e GPU compatível com DirectX 12 / Shader Model 6.
Se o Windows pedir o Visual C++ Runtime, instale o redistribuível x64 da Microsoft.
Começa em janela 1280x720, limite de 60 FPS. Esc permite qualidade média/alta.

Fonte e continuidade: github.com/sergiomrge-tech/simulador-resort
Branch: codex/ue58-migration
''', encoding='utf-8-sig')
root = Path(__file__).resolve().parents[2]
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
hashes = {p.relative_to(args.output).as_posix(): hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
          for p in (args.output/'Windows').rglob('*') if p.is_file() and p.suffix in ('.exe', '.pak', '.ucas', '.utoc')}
(args.output/'manifest.json').write_text(json.dumps({'commit': commit, 'engine': '5.8.3', 'preview': True,
    'qa': result, 'sha256': hashes}, ensure_ascii=False, indent=2), encoding='utf-8')
archive = args.output.with_suffix('.zip')
if archive.exists():
    raise SystemExit('ZIP existente preservado; escolha outro destino.')
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as bundle:
    for path in args.output.rglob('*'):
        if path.is_file() and 'userdata' not in path.relative_to(args.output).parts:
            bundle.write(path, path.relative_to(args.output.parent))
print(json.dumps({'folder': str(args.output), 'zip': str(archive), 'bytes': archive.stat().st_size,
                  'sha256': hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()}, indent=2))
