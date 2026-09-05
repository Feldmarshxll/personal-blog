"""Check publication boundaries, page relationships and rebuild behavior."""

from datetime import date
import copy
import unittest

import yaml

from test_content import ContentFixture

from tools.site_builder.generate import generate


class GenerationTests(ContentFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        (self.root / 'zensical.toml').write_text(
            '[project]\nsite_url = "https://example.com/personal-blog/"\n'
            'docs_dir = ".build/docs"\nsite_dir = ".build/site"\n'
            '[project.extra]\nbase_path = "/personal-blog/"\n', encoding='utf-8')
        (self.root / 'content/pages').mkdir()
        (self.root / 'content/pages/resume.md').write_text(
            '---\ntitle: Резюме\n---\n\n## Опыт\n\nПозже.\n', encoding='utf-8')
        self.wishlist['legacy_path'] = 'Старый wishlist'
        self.write_list()

    def build_content(self):
        return generate(self.root, today=date(2026, 9, 5))

    def page(self, relative):
        return (self.root / '.build/docs' / relative).read_text(encoding='utf-8')

    def test_generation_preserves_authored_files_and_escapes_yaml_text(self):
        self.wishlist['items'][0]['title'] = '<script>alert(1)</script>'
        self.write_list()
        source = (self.root / 'content/wishlists/mine.yml').read_bytes()
        self.build_content()
        self.assertEqual((self.root / 'content/wishlists/mine.yml').read_bytes(), source)
        page = self.page('personal/wishlists/mine.md')
        self.assertIn('&lt;script&gt;', page)
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('https://example.org/book', page)

    def test_legacy_url_has_new_target(self):
        self.build_content()
        self.assertIn('/personal-blog/personal/wishlists/mine/', self.page('Старый wishlist.md'))

    def test_removed_article_disappears_on_rebuild(self):
        self.write_article('one')
        self.build_content()
        (self.root / 'content/articles/one.md').unlink()
        self.build_content()
        self.assertFalse((self.root / '.build/docs/blog/articles/one.md').exists())

    def test_draft_does_not_enter_staged_docs_or_homepage(self):
        self.write_article('secret-draft', draft=True)
        self.write_article('public')
        self.build_content()
        self.assertFalse((self.root / '.build/docs/blog/articles/secret-draft.md').exists())
        self.assertNotIn('secret-draft', self.page('index.md'))
        self.assertIn('/personal-blog/blog/articles/public/', self.page('index.md'))

    def test_series_navigation_follows_part_number_not_post_date(self):
        self.write_article('first', series='build', series_order=1, date=date(2026, 9, 1))
        self.write_article('second', series='build', series_order=2, date=date(2026, 9, 4))
        self.build_content()
        raw = self.page('blog/articles/first.md')
        meta = yaml.safe_load(raw.split('---', 2)[1])
        self.assertEqual(meta['article']['series']['next']['url'], '/personal-blog/blog/articles/second/')
        self.assertIsNone(meta['article']['series']['previous'])
        series = self.page('blog/series/build.md')
        self.assertLess(series.index('first/'), series.index('second/'))

    def test_failed_validation_keeps_last_valid_staging(self):
        self.build_content()
        previous = self.page('index.md')
        (self.folder / 'mine.yml').write_text('items: [', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.build_content()
        self.assertEqual(self.page('index.md'), previous)

    def test_unrelated_output_configuration_is_rejected_before_writing(self):
        path = self.root / 'zensical.toml'
        path.write_text(path.read_text().replace('.build/docs', 'content'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'docs_dir'):
            generate(self.root)
        self.assertTrue((self.root / 'content/pages/resume.md').exists())

    def test_reserved_article_slug_keeps_previous_catalog(self):
        self.build_content()
        previous = self.page('blog/articles/index.md')
        self.write_article('collision', slug='index')
        with self.assertRaisesRegex(ValueError, 'collision.md.*index'):
            self.build_content()
        self.assertEqual(self.page('blog/articles/index.md'), previous)

    def test_reserved_project_slug_is_rejected(self):
        folder = self.root / 'content/projects'
        folder.mkdir()
        (folder / 'collision.md').write_text(
            '---\ntitle: Project\nslug: index\nsummary: Description\nstatus: Active\n---\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'collision.md.*index'):
            self.build_content()

    def test_reserved_series_id_is_rejected(self):
        (self.root / 'content/series.yml').write_text(
            'series:\n  - id: index\n    title: Series\n', encoding='utf-8')
        self.write_article('part', series='index', series_order=1)
        with self.assertRaisesRegex(ValueError, 'series.yml.*index'):
            self.build_content()

    def test_legacy_routes_cannot_replace_home_or_section(self):
        self.build_content()
        previous = self.page('index.md')
        for legacy in ('index', 'blog', 'personal', '404'):
            with self.subTest(legacy=legacy):
                self.wishlist['legacy_path'] = legacy
                self.write_list()
                with self.assertRaisesRegex(ValueError, f'mine.yml.*{legacy}'):
                    self.build_content()
                self.assertEqual(self.page('index.md'), previous)

    def test_duplicate_legacy_routes_report_source(self):
        self.build_content()
        other = copy.deepcopy(self.wishlist)
        other['id'] = 'other'
        (self.folder / 'other.yml').write_text(yaml.safe_dump(other, allow_unicode=True), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'other.yml.*Старый wishlist'):
            self.build_content()

    def test_site_metadata_is_shared_with_pages_and_runtime_config(self):
        source = self.root / 'content/site.yml'
        site = yaml.safe_load(source.read_text(encoding='utf-8'))
        site.update(name='New <name> & brand', tagline='New <tagline>')
        source.write_text(yaml.safe_dump(site, allow_unicode=True), encoding='utf-8')
        self.build_content()
        for path in ('index.md', 'blog/resume.md', 'Старый wishlist.md'):
            meta = yaml.safe_load(self.page(path).split('---', 2)[1])
            self.assertEqual(meta['site']['name'], site['name'])
            self.assertEqual(meta['site']['tagline'], site['tagline'])
        config = yaml.safe_load((self.root / '.build/zensical.yml').read_text(encoding='utf-8'))
        self.assertEqual(config['site_name'], site['name'])
        self.assertEqual(config['site_description'], site['tagline'])
        self.assertEqual(config['extra']['site']['name'], site['name'])

    def test_author_assets_cannot_silently_replace_theme_assets(self):
        self.build_content()
        previous = self.page('index.md')
        for base in ('theme/assets', 'content/assets'):
            folder = self.root / base / 'styles'
            folder.mkdir(parents=True)
            (folder / 'site.css').write_text(base, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'content.*site.css'):
            self.build_content()
        self.assertEqual(self.page('index.md'), previous)


if __name__ == '__main__':
    unittest.main()
