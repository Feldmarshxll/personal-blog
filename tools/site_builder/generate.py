"""Stage deterministic public Markdown without editing authored sources."""

from datetime import date
from copy import deepcopy
import os
from pathlib import Path, PurePosixPath
import shutil
import tomllib
from urllib.parse import urlsplit

import yaml

from .catalog import decorate, summary
from .content import load_articles, load_projects, load_series, load_site, load_wishlists, read_markdown
from .markup import anchor, cards, empty, h, intro, taxonomy_links, wishlist_html
from .validation import fail, inside


def settings(root):
    source = root / 'zensical.toml'
    try:
        project = tomllib.loads(source.read_text(encoding='utf-8'))['project']
    except (OSError, ValueError, KeyError) as exc:
        fail(source, str(exc))
    for field, expected in (('docs_dir', '.build/docs'), ('site_dir', '.build/site')):
        if project.get(field) != expected:
            fail(source, f'{field} должен быть {expected}')
    base = urlsplit(project.get('site_url', '')).path.rstrip('/') + '/'
    if not base.startswith('/') or '..' in base.split('/'):
        fail(source, 'некорректный site_url')
    if project.get('extra', {}).get('base_path') != base:
        fail(source, f'extra.base_path должен совпадать с путём site_url: {base}')
    inside(root / '.build', root)
    inside(root / '.build/docs', root / '.build')
    inside(root / '.build/site', root / '.build')
    return project, base


def _page(pages, path, title, body, *, source='генерируемый каталог', **metadata):
    # foo.md and foo/index.md are distinct files but produce the same URL.
    route = PurePosixPath(path).with_suffix('')
    if route.name.casefold() == 'index':
        route = route.parent
    key = str(route).casefold()
    if key in pages:
        previous = pages[key]
        fail(source, f'конфликт адреса {path} с {previous["path"]} ({previous["source"]})')
    meta = dict(title=title, template='main.html')
    meta.update(metadata)
    pages[key] = dict(path=path, meta=meta, body=body, source=source)


def _assets(root):
    files = {}
    for folder in ('theme/assets', 'content/assets'):
        source = root / folder
        if source.is_dir():
            for path in sorted(source.rglob('*')):
                if path.is_file():
                    inside(path, source)
                    relative = path.relative_to(source)
                    key = relative.as_posix().casefold()
                    if key in files:
                        fail(path, f'конфликт файла assets/{relative} с {files[key][0]}')
                    files[key] = (path, relative)
    return files.values()


def _runtime_config(root, project, site):
    config = deepcopy(project)
    config.update(site_name=site['name'], site_description=site['tagline'])
    config.update(docs_dir='docs', site_dir='site')
    theme = config.get('theme', {})
    if theme.get('custom_dir'):
        theme['custom_dir'] = os.path.relpath(root / theme['custom_dir'], root / '.build').replace('\\', '/')
    config.setdefault('extra', {})['site'] = site
    return yaml.safe_dump(config, allow_unicode=True, sort_keys=False)


def _write_catalog(output, site, articles, projects, wishlists, series, base, resume):
    categories, groups, tags = decorate(articles, projects, site['categories'], series, base)
    featured = [summary(p) for p in projects if p['featured']]
    _page(output, 'index.md', site['name'], '', template='home.html', site=site,
          latest_articles=[summary(a) for a in articles[:3]], featured_projects=featured[:3],
          description=site['tagline'])
    overview = [dict(title=title, description=description, url=base + url, label=number) for number, title, description, url in (
        ('01 / Тексты', 'Статьи', 'Разработка, Data Science и исследования. Идеи, эксперименты и выводы.', 'blog/articles/'),
        ('02 / Последовательно', 'Серии', 'Связанные публикации, которые удобно читать по порядку.', 'blog/series/'),
        ('03 / Практика', 'Проекты', 'От постановки задачи до результата: работа, решения и ограничения.', 'blog/projects/'),
        ('04 / О нас', 'Резюме', 'Опыт, навыки, образование и контакты.', 'blog/resume/'))]
    _page(output, 'blog/index.md', 'Блог и портфолио',
          intro('Публичное', 'Блог и портфолио', 'Место для мыслей, исследований и законченных работ.') + cards(overview, ''))
    _page(output, 'blog/articles/index.md', 'Статьи',
          intro('Блог и портфолио / 01', 'Статьи', 'Наблюдения, эксперименты и подробные разборы.')
          + taxonomy_links(categories) + cards(articles, 'Первые статьи появятся здесь.'))
    for category in categories:
        related = [a for a in articles if a['category'] == category['id']]
        _page(output, f'blog/categories/{category["id"]}.md', category['title'],
              intro('Рубрика', category['title'], 'Статьи по теме.') + cards(related, 'В этой рубрике пока нет статей.'))
    _page(output, 'blog/tags/index.md', 'Теги', intro('Блог и портфолио', 'Теги', 'Публикации по ключевым темам.')
          + (taxonomy_links(tags) if tags else empty('Теги появятся вместе с первыми статьями.')))
    for tag in tags:
        _page(output, f'blog/tags/{tag["id"]}.md', tag['title'],
              intro('Тег', tag['title'], 'Все публикации с этой меткой.') + cards(tag['articles'], ''))
    public_groups = [g for g in groups if g['articles']]
    _page(output, 'blog/series/index.md', 'Серии',
          intro('Блог и портфолио / 02', 'Серии', 'Одна тема. Несколько шагов. Последовательное чтение.')
          + cards(public_groups, 'Здесь будут собраны серии публикаций.'))
    for group in public_groups:
        _page(output, f'blog/series/{group["id"]}.md', group['title'],
              intro('Серия', group['title'], group['description']) + '<div class="series-list">\n'
              + cards(group['articles'], '') + '\n</div>')
    for article in articles:
        metadata = dict(date_label=article['date_label'], category=article['category_info'],
                        tags=article['tag_info'], authors=article['authors'], series=article.get('series_info'))
        _page(output, f'blog/articles/{article["slug"]}.md', article['title'], article['body'],
              template='article.html', article=metadata, description=article['description'],
              draft=article['draft'], source=article['source'])
    _page(output, 'blog/projects/index.md', 'Проекты',
          intro('Блог и портфолио / 03', 'Проекты', 'Задачи, решения и результаты — с деталями, которые имеют значение.')
          + cards(projects, 'Кейсы проектов скоро появятся здесь.'))
    for project in projects:
        body = intro('Проект', project['title'], project['summary'])
        body += '<p class="card-meta">' + h(project['status']) + '</p>\n\n'
        body += '<div class="tag-list">' + ' '.join(f'<span class="tag">{h(t)}</span>' for t in project['technologies']) + '</div>\n\n'
        body += '<div class="wish-links">' + ' '.join(anchor(l['label'], l['url']) for l in project['links']) + '</div>\n\n'
        body += project['body']
        _page(output, f'blog/projects/{project["slug"]}.md', project['title'], body,
              description=project['summary'], source=project['source'])
    meta, body = resume
    _page(output, 'blog/resume.md', meta.get('title', 'Резюме'),
          intro('Блог и портфолио / 04', 'Резюме', 'Опыт, навыки и то, над чем мы работаем.') + body,
          description=meta.get('description', ''), page_class='resume-page')
    personal_cards = [dict(title=w['title'], description=w['description'],
                           url=f'{base}personal/wishlists/{w["id"]}/', label=f'{len(w["items"])} желаний и целей') for w in wishlists]
    _page(output, 'personal/index.md', 'Личное',
          intro('Немного личного', 'За пределами работы.', 'Вещи, маленькие радости и большие планы.')
          + cards(personal_cards, 'Личные списки пока не добавлены.'))
    for wishlist in wishlists:
        target = f'{base}personal/wishlists/{wishlist["id"]}/'
        _page(output, f'personal/wishlists/{wishlist["id"]}.md', wishlist['title'], wishlist_html(wishlist, base))
        if wishlist.get('legacy_path'):
            _page(output, wishlist['legacy_path'] + '.md', wishlist['title'],
                  intro('Новый адрес', wishlist['title'], 'Этот список теперь находится в разделе «Личное».')
                  + anchor('Открыть вишлист', target), template='redirect.html', redirect_url=target,
                  search={'exclude': True}, source=wishlist['source'])


def generate(root, preview=False, today=None):
    root = Path(root).resolve()
    project, base = settings(root)
    # Validate the whole input before touching the previous successful staging.
    site, wishlists = load_site(root), load_wishlists(root)
    articles = load_articles(root, today or date.today(), preview)
    projects, series = load_projects(root, preview), load_series(root)
    resume = read_markdown(root / 'content/pages/resume.md')
    pages = {}
    _write_catalog(pages, site, articles, projects, wishlists, series, base, resume)
    assets = _assets(root)
    runtime_config = _runtime_config(root, project, site)
    build_root = inside(root / '.build', root)
    build_root.mkdir(exist_ok=True)
    output = inside(build_root / 'docs', build_root)
    pending = inside(build_root / 'docs-next', build_root)
    config_path = inside(build_root / 'zensical.yml', build_root)
    if pending.exists():
        shutil.rmtree(pending)
    pending.mkdir()
    for page in pages.values():
        target = inside(pending / page['path'], pending)
        target.parent.mkdir(parents=True, exist_ok=True)
        page['meta']['site'] = site
        target.write_text('---\n' + yaml.safe_dump(page['meta'], allow_unicode=True, sort_keys=False)
                          + '---\n\n' + page['body'] + '\n', encoding='utf-8', newline='\n')
    for source, relative in assets:
        target = inside(pending / 'assets' / relative, pending / 'assets')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if output.exists():
        shutil.rmtree(output)
    pending.rename(output)
    config_path.write_text(runtime_config, encoding='utf-8', newline='\n')
    return output
