"""Transport adapter; executed only by the frozen container Python."""
# SPDX-License-Identifier: MIT
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import shlex
import shutil
import sys

PREFIX = Path('/opt/dgdtl/env')
PYTHON = str(PREFIX / 'bin/python')
RELEASE = Path(__file__).resolve().parents[2]
FONTS = (
    ('normal', 'normal', 'Arial.ttf', '35c0f3559d8db569e36c31095b8a60d441643d95f59139de40e23fada819b833'),
    ('normal', 'bold', 'Arial_Bold.ttf', '4044aa6b5bebbc36980206b45b0aaaaa5681552a48bcadb41746d5d1d71fd7b4'),
    ('italic', 'normal', 'Arial_Italic.ttf', '70ade233175a6a6675e4501461af9326e6f78b1ffdf787ca0da5ab0fc8c9cfd6'),
    ('italic', 'bold', 'Arial_Bold_Italic.ttf', '2f371cd9d96b3ac544519d85c16dc43ceacdfcea35090ee8ddf3ec5857c50328'),
)


def verify_environment():
    if (sys.executable != PYTHON or Path(sys.prefix) != PREFIX
            or shutil.which('python') != PYTHON):
        raise RuntimeError(f'Frozen Python required: {PYTHON}; observed {sys.executable}, {sys.prefix}')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise RuntimeError('The certified runtime requires linux/amd64.')
    if 'microsoft-standard-wsl2' not in platform.release().lower():
        raise RuntimeError('The Docker kernel is not the required WSL2 backend.')
    import dgdtl_lts
    import u_maxp
    for module in (dgdtl_lts, u_maxp):
        if not Path(module.__file__).resolve().is_relative_to(PREFIX / 'lib/python3.12/site-packages'):
            raise RuntimeError(f'Unexpected public import: {module.__file__}')
    from matplotlib import font_manager as fm
    for style, weight, filename, expected in FONTS:
        font = Path(fm.findfont(fm.FontProperties(family='Arial', style=style, weight=weight),
                               fallback_to_default=False))
        if font.name != filename or hashlib.sha256(font.read_bytes()).hexdigest() != expected:
            raise RuntimeError(f'Controlled Arial identity/resolution mismatch: {font}')


def hunter_request(config):
    """Use the Linux builder verbatim; translate only the three host paths later."""
    paths = dict(train=config.train_file, valid=config.valid_file, output=config.out_dir)
    # Placeholders avoid interpreting Windows path backslashes as shell syntax.
    saved = config.train_file, config.valid_file, config.out_dir
    try:
        config.train_file, config.valid_file, config.out_dir = '/input/train', '/input/valid', '/output'
        argv = shlex.split(config.build_command().replace('\\\n', ''))[2:]
    finally:
        config.train_file, config.valid_file, config.out_dir = saved
    return dict(paths=paths, argv=argv)


def main():
    verify_environment()
    action = sys.argv[1]
    if action == 'check':
        print(f'Frozen environment and controlled Arial: PASS ({PYTHON})')
    elif action == 'configure':
        config_type = runpy.run_path(str(RELEASE / 'launchers/linux/create_local_sh_dgdtl_lts.py'))['HunterConfig']
        config = config_type()
        config.configure_interactively()
        Path('/transport/hunter.json').write_text(json.dumps(hunter_request(config)), encoding='utf-8')
    elif action == 'hunter':
        request = json.loads(Path('/transport/hunter.json').read_text(encoding='utf-8'))
        os.execv(PYTHON, [PYTHON, '-s', str(RELEASE / 'orchestrators/dgdtl_hunter_umaxp_cluster.py'), *request['argv']])
    elif action == 'unified':
        os.execv(PYTHON, [PYTHON, '-s', str(RELEASE / 'orchestrators/dgdtl_unified_umaxp.py')])
    else:
        raise RuntimeError(f'Unknown internal action: {action}')


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt) as exc:
        print(f'DGDTL launcher: {exc}', file=sys.stderr)
        sys.exit(1)
