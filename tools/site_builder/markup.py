"""HTML fragments for generated catalogs; all YAML strings are escaped."""

from html import escape


def h(value):
    return escape(str(value), quote=True)


def anchor(title, url, css=''):
    return f'<a class="{h(css)}" href="{h(url)}">{h(title)}</a>'


def intro(label, title, description):
    return (f'<header class="page-intro"><p class="eyebrow">{h(label)}</p>'
            f'<h1>{h(title)}</h1><p>{h(description)}</p></header>\n\n')


def empty(message):
    return f'<div class="empty-state"><p>{h(message)}</p></div>\n'


def cards(entries, empty_message):
    if not entries:
        return empty(empty_message)
    result = ['<div class="card-grid">']
    for entry in entries:
        meta = entry.get('date_label', entry.get('label', ''))
        result.append(
            '<article class="content-card">'
            f'<p class="card-meta">{h(meta)}</p>'
            f'<h2>{anchor(entry["title"], entry["url"])}</h2>'
            f'<p>{h(entry.get("description", ""))}</p></article>')
    return '\n'.join(result) + '\n</div>\n'


def taxonomy_links(entries):
    return '<div class="tag-list">' + ' '.join(anchor(e['title'], e['url'], 'tag') for e in entries) + '</div>\n\n'


def money(item):
    if 'price' not in item:
        return 'Цель' if item['kind'] == 'goal' else 'Цена не указана'
    amount = f'{item["price"]:,.2f}'.rstrip('0').rstrip('.').replace(',', '\u202f').replace('.', ',')
    return f'≈ {amount} {"₽" if item["currency"] == "RUB" else "$"}'


def wishlist_html(data, base_path):
    categories = {c['id']: c['title'] for c in data['categories']}
    options = ''.join(f'<option value="{h(c["id"])}">{h(c["title"])}</option>' for c in data['categories'])
    currencies = sorted({i['currency'] for i in data['items'] if 'currency' in i})
    currency_options = ''.join(f'<option value="{c}">{c}</option>' for c in currencies)
    result = [intro('Личное / Вишлисты', data['title'], data['description']),
              '<section class="wishlist" data-wishlist>',
              '<div class="wishlist-toolbar" data-wishlist-toolbar hidden>',
              f'<label>Категория<select data-filter-category><option value="">Все категории</option>{options}</select></label>',
              '<label>Статус<select data-filter-status><option value="">Все</option><option value="wanted">Хочу</option><option value="received">Подарено</option></select></label>',
              f'<label>Валюта<select data-filter-currency><option value="">Все валюты</option>{currency_options}</select></label>',
              '<label>Бюджет до<input data-filter-budget type="number" min="0" step="any" inputmode="decimal" placeholder="Любой" aria-describedby="budget-note"></label>',
              '<button type="button" data-filter-reset>Сбросить</button>',
              '<p id="budget-note" class="filter-note">Для бюджета выберите валюту. Цели без цены остаются в списке.</p>',
              '</div>',
              f'<p class="wishlist-count" data-filter-count aria-live="polite">Всего: {len(data["items"])}</p>',
              '<div class="card-grid wishlist-grid">']
    for item in data['items']:
        status = 'Хочу' if item['status'] == 'wanted' else 'Подарено'
        result.append(
            f'<article class="wish-card" id="{h(item["id"])}" data-wish '
            f'data-category="{h(item["category"])}" data-status="{h(item["status"])}" '
            f'data-currency="{h(item.get("currency", ""))}" data-price="{h(item.get("price", ""))}">')
        if item.get('image'):
            result.append(f'<img class="wish-image" src="{h(base_path + item["image"])}" alt="" loading="lazy" width="480" height="320">')
        result.append(f'<div class="card-meta"><span class="wish-category">{h(categories[item["category"]])}</span><span>{status}</span></div>')
        result.append(f'<h2>{anchor(item["title"], "#" + item["id"])}</h2>')
        result.append(f'<p class="wish-description">{h(item["description"])}</p>')
        result.append(f'<p class="wish-price">{h(money(item))}</p>')
        if item.get('priority'):
            priority = {'low': 'Низкий', 'normal': 'Обычный', 'high': 'Высокий'}[item['priority']]
            result.append(f'<p class="card-meta">Приоритет: {priority}</p>')
        if item.get('checked_at'):
            result.append(f'<p class="card-meta">Цена проверена: {h(item["checked_at"])}</p>')
        result.append('<div class="wish-links">' + ' '.join(anchor(link['label'], link['url']) for link in item['links']) + '</div>')
        result.append('</article>')
    result.extend(['</div>', '<div class="empty-state" data-filter-empty hidden><p>По этим условиям ничего не найдено.</p></div>', '</section>'])
    if data['footer_links']:
        result.append('<footer class="wishlist-footer">' + ' '.join(anchor(link['label'], link['url']) for link in data['footer_links']) + '</footer>')
    return '\n'.join(result)
