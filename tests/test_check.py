"""Check actual rendered references rather than configuration strings."""

from pathlib import Path
import tempfile
import unittest

from tools.site_builder.check import check_links


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')

    def check(self):
        return check_links(self.root, '/personal-blog/', 'https://example.com')

    def test_prefix_relative_links_assets_and_unicode_anchors_resolve(self):
        self.write('index.html', '<a href="/personal-blog/article/#%D1%86%D0%B5%D0%BB%D1%8C">Read</a><script src="assets/test.js"></script>')
        self.write('article/index.html', '<h2 id="цель">Goal</h2><a href="../">Home</a>')
        self.write('assets/test.js', '// fine')
        self.assertEqual(self.check(), [])

    def test_missing_file_and_missing_anchor_are_reported(self):
        self.write('index.html', '<a href="/personal-blog/missing/">Bad</a><a href="#missing">Bad anchor</a>')
        failures = self.check()
        self.assertEqual(len(failures), 2)
        self.assertTrue(any('missing/' in failure for failure in failures))

    def test_external_links_are_not_fetched(self):
        self.write('index.html', '<a href="https://no-such-host.invalid/path">External</a>')
        self.assertEqual(self.check(), [])

    def test_same_origin_absolute_link_is_checked(self):
        self.write('index.html', '<a href="https://example.com/personal-blog/no-page/">Missing</a>')
        self.assertEqual(len(self.check()), 1)

    def test_escape_from_site_root_is_reported(self):
        self.write('index.html', '<a href="../../../outside.html">Escape</a>')
        self.assertEqual(len(self.check()), 1)


if __name__ == '__main__':
    unittest.main()
