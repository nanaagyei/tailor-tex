from __future__ import annotations

import tempfile
import unittest
from pathlib import Path, PurePosixPath

from scripts.check_md_links import check_markdown_links


class CheckMarkdownLinksTests(unittest.TestCase):
    def test_valid_relative_and_external_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "docs").mkdir()
            (root / "README.md").write_text(
                "[guide](docs/guide.md) [site](https://example.com) "
                "[email](mailto:team@example.com)\n",
                encoding="utf-8",
            )
            (root / "docs/guide.md").write_text("Guide\n", encoding="utf-8")
            tracked = {PurePosixPath("README.md"), PurePosixPath("docs/guide.md")}

            errors = check_markdown_links(root, tracked, tracked)

        self.assertEqual(errors, [])

    def test_missing_relative_target_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            tracked = {PurePosixPath("README.md")}

            errors = check_markdown_links(root, tracked, tracked)

        self.assertEqual(len(errors), 1)
        self.assertIn("README.md:1", errors[0])
        self.assertIn("missing.md", errors[0])

    def test_ignores_code_examples(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text(
                "`[inline](missing.md)`\n\n```md\n[block](missing.md)\n```\n",
                encoding="utf-8",
            )
            tracked = {PurePosixPath("README.md")}

            errors = check_markdown_links(root, tracked, tracked)

        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
