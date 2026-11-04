"""Full-detail garments for every dressed MetaHuman (mare_metahuman.hi_garments), five High builds per editor session
(a MetaHuman build keeps ~10 GB alive), then the people listed in --medium are rebuilt at Medium in their own folder.

  python tools/ue58/hi_garments.py [Name ...] [--medium Name,Name]      log: D:/CodexTemp/hi_garments.log

The people stay Medium (Sergio, 03/11: "deixe no médium"); only their clothes come from the High build, because the
Medium build decimates the Fab T-shirts into jagged necklines ("arrume o acabamento").
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dress_metahumans import ROOT, call, log, restart_editor  # noqa: E402

import dress_metahumans
dress_metahumans.LOG = Path('D:/CodexTemp/hi_garments.log')


def main(args):
    medium = []
    if '--medium' in args:
        i = args.index('--medium')
        medium = args[i + 1].split(',')
        args = args[:i] + args[i + 2:]
    people = json.loads((ROOT / 'unreal/MareAlta/Content/Data/outfits_fab.json').read_text(encoding='utf-8'))['people']
    names = args or list(people) + ['Asha_Swim_Aeron', 'Celeste_Swim_Aeron', 'Jelena_Swim_Aeron']
    for i, name in enumerate(names):
        if i and i % 5 == 0:
            log('restart editor:', restart_editor())
        log(name, 'high garments', call('mh_higarment', name, 300)[:300])
    if medium:
        log('restart editor:', restart_editor())
        for name in medium:
            log(name, 'medium rebuild', call('mh_build', name, 200)[:200])
            log(name, 'save', call('mh_save', name, 80)[:80])
    log('DONE')


if __name__ == '__main__':
    main(sys.argv[1:])
