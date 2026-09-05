"""Load wishlists without inferring prices, ownership or gift priorities."""

from .validation import (calendar_date, fail, inside, links,
                         positive_number, read_yaml, route_identifier, text, unique_records)


def load_wishlists(root):
    result, seen = [], set()
    for path in sorted((root / 'content/wishlists').glob('*.yml')):
        data = read_yaml(path)
        list_id = route_identifier(data.get('id'), path)
        if list_id in seen:
            fail(path, f'повторный список {list_id}')
        seen.add(list_id)
        text(data.get('title'), path, 'title')
        text(data.get('description', ''), path, 'description', empty=True)
        categories = unique_records(data.get('categories'), path, 'categories')
        for category in categories:
            text(category.get('title'), path, 'categories.title')
        category_ids = {c['id'] for c in categories}
        for item in unique_records(data.get('items'), path, 'items'):
            location = f'{path} [{item["id"]}]'
            text(item.get('title'), location, 'title')
            text(item.get('description', ''), location, 'description', empty=True)
            if item.get('category') not in category_ids:
                fail(location, 'неизвестная category')
            if item.get('kind') not in ('product', 'goal'):
                fail(location, 'kind должен быть product или goal')
            if item.get('status') not in ('wanted', 'received'):
                fail(location, 'status должен быть wanted или received')
            links(item.get('links', []), location, 'links')
            if 'price' in item:
                positive_number(item['price'], location, 'price', zero=True)
                if item.get('currency') not in ('RUB', 'USD'):
                    fail(location, 'currency должна быть RUB или USD')
            elif 'currency' in item:
                fail(location, 'currency указана без price')
            if 'priority' in item and item['priority'] not in ('low', 'normal', 'high'):
                fail(location, 'priority должна быть low, normal или high')
            if 'checked_at' in item:
                item['checked_at'] = calendar_date(item['checked_at'], location, 'checked_at').isoformat()
            if 'image' in item:
                image = text(item['image'], location, 'image')
                image_path = inside(root / 'content' / image, root / 'content/assets')
                if not image_path.is_file():
                    fail(location, f'не найден image: {image}')
            item.setdefault('links', [])
            item.setdefault('description', '')
        links(data.get('footer_links', []), path, 'footer_links')
        if 'legacy_path' in data:
            legacy = text(data['legacy_path'], path, 'legacy_path')
            if any(c in legacy for c in '/\\?#') or legacy in ('.', '..'):
                fail(path, 'legacy_path должен быть одним сегментом URL')
            if legacy.casefold() == '404':
                fail(path, 'legacy_path: 404 зарезервирован для страницы ошибки')
        data.setdefault('description', '')
        data.setdefault('footer_links', [])
        data['source'] = path
        result.append(data)
    return result
