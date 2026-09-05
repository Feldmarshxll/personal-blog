"""One entry point for generation, strict builds and local preview."""

import argparse
from pathlib import Path
import subprocess
import sys

from .check import check_links
from .generate import generate, settings
from .preview import serve
from .validation import ContentError


def build(root, preview=False):
    generate(root, preview=preview)
    subprocess.run([sys.executable, '-m', 'zensical', 'build', '--strict', '--clean',
                    '-f', str(root / '.build/zensical.yml')], cwd=root, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Сборка личного сайта')
    parser.add_argument('command', choices=('generate', 'build', 'serve', 'check'))
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--drafts', action='store_true', help='Включить черновики и будущие статьи только в локальном предпросмотре')
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        config, base = settings(root)
        if args.drafts and args.command != 'serve':
            parser.error('--drafts разрешён только с serve; публичная сборка всегда исключает черновики')
        if args.command == 'generate':
            print(f'Страницы подготовлены: {generate(root)}')
        elif args.command == 'build':
            build(root)
        elif args.command == 'check':
            problems = check_links(root / '.build/site', base, config['site_url'])
            if problems:
                print('\n'.join(problems), file=sys.stderr)
                return 1
            print('Внутренние ссылки и якоря проверены.')
        else:
            build(root, args.drafts)
            serve(root, root / '.build/site', base, args.port, lambda: build(root, args.drafts))
    except (ContentError, OSError, subprocess.CalledProcessError) as exc:
        print(f'Ошибка: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
