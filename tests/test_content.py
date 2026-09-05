"""Protect authored content from silent loss or accidental publication."""

import copy
from datetime import date
from pathlib import Path
import tempfile
import unittest

import yaml

from tools.site_builder.content import ContentError, load_wishlists, load_articles


class ContentFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'content/wishlists'
        self.folder.mkdir(parents=True)
        (self.root / 'content/articles').mkdir()
        (self.root / 'content/site.yml').write_text(
            'name: Test\ncategories:\n  - id: development\n    title: Разработка\n',
            encoding='utf-8',
        )
        (self.root / 'content/series.yml').write_text(
            'series:\n  - id: build\n    title: Создание\n    description: Шаги\n',
            encoding='utf-8',
        )
        self.wishlist = {
            'id': 'mine', 'title': 'Мой список', 'description': '',
            'categories': [{'id': 'books', 'title': 'Книги'}],
            'items': [{'id': 'book', 'title': 'Книга', 'description': 'Комментарий',
                       'category': 'books', 'kind': 'product', 'status': 'wanted',
                       'price': 1000, 'currency': 'RUB',
                       'links': [{'label': 'Магазин', 'url': 'https://example.com/book'},
                                 {'label': 'Другой', 'url': 'https://example.org/book'}]}],
            'footer_links': [],
        }

    def write_list(self):
        (self.folder / 'mine.yml').write_text(yaml.safe_dump(self.wishlist, allow_unicode=True), encoding='utf-8')

    def lists(self):
        return load_wishlists(self.root)

    def articles(self, preview=False):
        return load_articles(self.root, today=date(2026, 9, 5), preview=preview)

    def write_article(self, filename, **updates):
        meta = dict(title=filename, date=date(2026, 9, 1), description='Описание',
                    category='development', tags=['Python'], slug=filename, draft=False)
        meta.update(updates)
        (self.root / f'content/articles/{filename}.md').write_text(
            '---\n' + yaml.safe_dump(meta, allow_unicode=True) + '---\n\n# Текст\n', encoding='utf-8')


class ContentTests(ContentFixture, unittest.TestCase):

    def test_index_wishlist_id_is_rejected_but_item_anchor_is_allowed(self):
        self.wishlist['items'][0]['id'] = 'index'
        self.write_list()
        self.assertEqual(self.lists()[0]['items'][0]['id'], 'index')
        self.wishlist['id'] = 'index'
        self.write_list()
        with self.assertRaisesRegex(ContentError, 'mine.yml.*index'):
            self.lists()

    def test_index_category_id_cannot_create_wrong_public_url(self):
        (self.root / 'content/site.yml').write_text(
            'name: Test\ncategories:\n  - id: index\n    title: Category\n', encoding='utf-8')
        with self.assertRaisesRegex(ContentError, 'site.yml.*index'):
            self.articles()

    def test_multiple_purchase_links_survive_loading(self):
        self.write_list()
        links = self.lists()[0]['items'][0]['links']
        self.assertEqual([link['url'] for link in links], ['https://example.com/book', 'https://example.org/book'])

    def test_goal_without_price_is_valid(self):
        self.wishlist['items'].append(dict(id='learn', title='Учиться', description='',
                                            category='books', kind='goal', status='wanted', links=[]))
        self.write_list()
        self.assertNotIn('price', self.lists()[0]['items'][1])

    def test_duplicate_item_id_is_rejected_with_filename(self):
        self.wishlist['items'].append(copy.deepcopy(self.wishlist['items'][0]))
        self.write_list()
        self.assertTrue(callable(load_wishlists), 'Wishlist loader is not implemented')
        with self.assertRaisesRegex(ContentError, 'mine.yml.*book'):
            load_wishlists(self.root)

    def test_invalid_yaml_is_reported(self):
        (self.folder / 'mine.yml').write_text('items: [\n', encoding='utf-8')
        self.assertTrue(callable(load_wishlists), 'Wishlist loader is not implemented')
        with self.assertRaisesRegex(ContentError, 'mine.yml'):
            load_wishlists(self.root)

    def test_script_url_is_rejected(self):
        self.wishlist['items'][0]['links'][0]['url'] = 'javascript:alert(1)'
        self.write_list()
        self.assertTrue(callable(load_wishlists), 'Wishlist loader is not implemented')
        with self.assertRaisesRegex(ContentError, 'mine.yml'):
            load_wishlists(self.root)

    def test_drafts_and_future_posts_are_not_published(self):
        self.write_article('published')
        self.write_article('draft', draft=True)
        self.write_article('future', date=date(2026, 9, 6))
        self.assertEqual([p['slug'] for p in self.articles()], ['published'])
        self.assertEqual(len(self.articles(preview=True)), 3)

    def test_posts_are_sorted_newest_first(self):
        self.write_article('earlier', date=date(2026, 8, 1))
        self.write_article('later', date=date(2026, 9, 3))
        self.assertEqual([p['slug'] for p in self.articles()], ['later', 'earlier'])

    def test_duplicate_slug_is_rejected(self):
        self.write_article('one', slug='same')
        self.write_article('two', slug='same')
        self.assertTrue(callable(load_articles), 'Article catalog is not implemented')
        with self.assertRaisesRegex(ContentError, 'same'):
            load_articles(self.root, today=date(2026, 9, 5))

    def test_duplicate_series_position_is_rejected(self):
        self.write_article('one', series='build', series_order=1)
        self.write_article('two', series='build', series_order=1)
        self.assertTrue(callable(load_articles), 'Article catalog is not implemented')
        with self.assertRaisesRegex(ContentError, 'series_order'):
            load_articles(self.root, today=date(2026, 9, 5))

    def test_impossible_date_is_rejected(self):
        self.write_article('bad-date', date='2026-02-30')
        self.assertTrue(callable(load_articles), 'Article catalog is not implemented')
        with self.assertRaisesRegex(ContentError, 'bad-date.md'):
            load_articles(self.root, today=date(2026, 9, 5))

    def test_path_traversal_slug_is_rejected(self):
        self.write_article('escape', slug='../../escape')
        self.assertTrue(callable(load_articles), 'Article catalog is not implemented')
        with self.assertRaisesRegex(ContentError, 'escape.md'):
            load_articles(self.root, today=date(2026, 9, 5))


if __name__ == '__main__':
    unittest.main()
