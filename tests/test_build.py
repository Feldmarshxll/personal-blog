"""Exercise the real template engine with published and private content."""

from datetime import date
from html import unescape
from pathlib import Path
import shutil
import unittest

import yaml

import test_generate
from tools.site_builder.__main__ import build
from tools.site_builder.check import check_links


def populate_preview(root):
    """Create isolated, explicitly synthetic content for integration and visual QA."""
    (root / 'content/site.yml').write_text(yaml.safe_dump({
        'name': 'Проверка & шаблоны', 'tagline': 'Единая подпись из YAML',
        'intro': 'Тестовый материал для проверки вёрстки.',
        'categories': [{'id': 'development', 'title': 'Разработка'}],
    }, allow_unicode=True), encoding='utf-8')
    (root / 'content/series.yml').write_text(yaml.safe_dump({'series': [{
        'id': 'build', 'title': 'Серия для проверки', 'description': 'Две части по порядку.',
    }]}, allow_unicode=True), encoding='utf-8')
    posts = [('first', 1, date(2020, 9, 1)), ('second', 2, date(2020, 9, 4)),
             ('private-draft', 3, date(2020, 9, 5)), ('future-post', 4, date(2099, 1, 1))]
    for slug, order, published in posts:
        metadata = dict(title=f'Проверка статьи: часть {order}', date=published,
                        description='Проверяем текст, код, таблицу и связи между публикациями.',
                        category='development', tags=['Python', 'тест & шаблоны'],
                        slug=slug, series='build', series_order=order,
                        authors=['Тестовый автор'], draft=slug == 'private-draft')
        body = ('Вводный абзац с **выделением** и [ссылкой на каталог](../index.md).\n\n'
                '## Подход\n\nКороткий абзац для проверки читаемости.\n\n'
                '```python\nprint("Hello, universe")\n```\n\n'
                '## Результат\n\n| Параметр | Значение |\n| --- | --- |\n| Части | 2 |\n')
        (root / f'content/articles/{slug}.md').write_text(
            '---\n' + yaml.safe_dump(metadata, allow_unicode=True) + '---\n\n' + body,
            encoding='utf-8')
    (root / 'content/projects').mkdir(exist_ok=True)
    for slug, draft in [('example-project', False), ('private-project', True)]:
        metadata = dict(title='Тестовый проект', summary='Проверка карточки проекта.',
                        slug=slug, draft=draft, status='Готов', technologies=['Python'],
                        featured=True, links=[dict(label='Исходники', url='https://example.com/')])
        (root / f'content/projects/{slug}.md').write_text(
            '---\n' + yaml.safe_dump(metadata, allow_unicode=True)
            + '---\n\n## Задача\n\nПроверить отображение проекта.\n', encoding='utf-8')


class RealBuildTests(unittest.TestCase):
    def test_templates_routes_metadata_and_publication_boundary(self):
        fixture = test_generate.GenerationTests('test_legacy_url_has_new_target')
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        root = fixture.root
        repository = Path(__file__).resolve().parents[1]
        shutil.copytree(repository / 'theme', root / 'theme')
        shutil.copyfile(repository / 'zensical.toml', root / 'zensical.toml')
        populate_preview(root)

        build(root)
        output = root / '.build/site'
        read = lambda path: (output / path).read_text(encoding='utf-8')
        self.assertEqual(check_links(output, '/personal-blog/',
                                     'https://feldmarshxll.github.io/personal-blog/'), [])
        for path in ('index.html', 'blog/articles/first/index.html',
                     'blog/projects/example-project/index.html', '404.html'):
            html = read(path)
            self.assertIn('Проверка &amp; шаблоны', html)
            self.assertIn('Единая подпись из YAML', html)
            self.assertNotIn('Feldmarshxll', html)
        first = unescape(read('blog/articles/first/index.html'))
        second = unescape(read('blog/articles/second/index.html'))
        self.assertIn('Следующая часть', first)
        self.assertIn('/personal-blog/blog/articles/second/', first)
        self.assertNotIn('Предыдущая часть', first)
        self.assertIn('Предыдущая часть', second)
        self.assertNotIn('Следующая часть', second)
        self.assertIn('<table>', first)
        self.assertIn('Hello, universe', first)
        self.assertIn('1 сентября 2020', first)
        self.assertIn('Тестовый автор', first)
        series = unescape(read('blog/series/build/index.html'))
        self.assertLess(series.index('articles/first/'), series.index('articles/second/'))
        homepage = unescape(read('index.html'))
        self.assertLess(homepage.index('articles/second/'), homepage.index('articles/first/'))
        self.assertIn('/personal-blog/blog/projects/example-project/', homepage)
        all_html = '\n'.join(p.read_text(encoding='utf-8') for p in output.rglob('*.html'))
        for slug in ('private-draft', 'future-post', 'private-project'):
            self.assertNotIn(slug, all_html)
        for folder in ('articles/private-draft', 'articles/future-post', 'projects/private-project'):
            self.assertFalse((output / 'blog' / folder).exists())


if __name__ == '__main__':
    unittest.main()
