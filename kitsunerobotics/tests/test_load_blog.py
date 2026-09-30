import os
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings

from kitsunerobotics.blog_loader import load_posts, pull_blog
from kitsunerobotics.models import SiteSetting
from kitsunerobotics.templatetags.markdown_tags import render_markdown
from siteblog.models import Article


class MarkdownRenderTests(TestCase):
    def test_images_shrink_and_media_files_become_downloads(self):
        html = render_markdown(
            "![rack](/media/rack.png)\n\n"
            "[notes.pdf](/media/notes.pdf)\n\n"
            "[home](https://kitsunehosting.net)\n"
        )
        self.assertIn('class="post-image" href="/media/rack.png"', html)
        self.assertIn('class="download-box" href="/media/notes.pdf"', html)
        self.assertIn("Download", html)
        self.assertIn('<a href="https://kitsunehosting.net">home</a>', html)


class LoadBlogTests(TestCase):
    def test_markdown_file_becomes_an_article_with_a_media_image_url(self):
        repo = Path(self._tmp())
        post_dir = repo / "rackcontroller4u"
        post_dir.mkdir(parents=True)
        (post_dir / "photo.png").write_bytes(b"png")
        (post_dir / "preview.png").write_bytes(b"png")
        (repo / "rackcontroller4u.md").write_text(
            "---\n"
            "title: Watercooling Rack Controller\n"
            "published: 2026-10-01\n"
            "status: draft\n"
            "tags: pcb kicad pc_building 3d_printing\n"
            "preview: rackcontroller4u/preview.png\n"
            "---\n"
            "Hello\n\n"
            "![the rack](rackcontroller4u/photo.png)\n",
            encoding="utf-8",
        )
        Article.objects.create(
            title="Old",
            slug="old-post",
            article_body="gone",
            status="published",
        )

        with override_settings(MEDIA_URL="/media/"):
            slugs, removed = load_posts(repo)

        self.assertEqual(slugs, ["rackcontroller4u"])
        self.assertGreaterEqual(removed, 1)
        article = Article.objects.get(slug="rackcontroller4u")
        self.assertEqual(article.title, "Watercooling Rack Controller")
        self.assertEqual(article.status, "draft")
        self.assertEqual(article.published_on.date(), date(2026, 10, 1))
        self.assertIn("/media/blog/rackcontroller4u/photo.png", article.article_body.content)
        self.assertEqual(
            article.article_tags.names,
            ["pcb", "kicad", "pc_building", "3d_printing"],
        )
        self.assertEqual(
            article.article_tags.preview,
            "/media/blog/rackcontroller4u/preview.png",
        )
        self.assertTrue((repo / "rackcontroller4u" / "photo.png").is_file())
        self.assertFalse(Article.objects.filter(slug="old-post").exists())

    def test_post_changes_notify_discord_and_keep_tags(self):
        SiteSetting.objects.create(
            key="blogpost_webhook", value="https://example.test/hook"
        )
        repo = Path(self._tmp())
        path = repo / "hello.md"
        path.write_text(
            "---\ntitle: Hello\nstatus: published\ntags: pcb, kicad\n---\nHi\n",
            encoding="utf-8",
        )

        with patch("kitsunerobotics.webhooks.requests.post") as post:
            load_posts(repo)
            self.assertEqual(post.call_count, 1)
            content = post.call_args.kwargs["json"]["content"]
            self.assertIn("New blog post: Hello", content)
            self.assertIn("tags: pcb, kicad", content)
            self.assertEqual(post.call_args.args[0], "https://example.test/hook")

            post.reset_mock()
            load_posts(repo)
            post.assert_not_called()

            path.write_text(
                "---\ntitle: Hello\nstatus: published\ntags: pcb water\n---\nHi\n",
                encoding="utf-8",
            )
            load_posts(repo)

        article = Article.objects.get(slug="hello")
        self.assertEqual(article.article_tags.names, ["pcb", "water"])
        content = post.call_args.kwargs["json"]["content"]
        self.assertIn("Updated blog post: Hello", content)
        self.assertIn("tags: pcb, water", content)

    def test_unchanged_repo_is_not_loaded_again(self):
        origin = Path(self._tmp())
        (origin / "hello.md").write_text(
            "---\ntitle: Hello\nstatus: published\n---\nHi\n",
            encoding="utf-8",
        )
        self._commit(origin, "first")
        checkout = Path(self._tmp())
        media = Path(self._tmp())

        with override_settings(MEDIA_ROOT=media, MEDIA_URL="/media/"):
            first = pull_blog(url=str(origin), checkout=checkout)
            second = pull_blog(url=str(origin), checkout=checkout)

        self.assertEqual(first[0], ["hello"])
        self.assertIsNone(second)

    def _commit(self, repo, message):
        env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "t@example.com",
        }
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, env=env)
        subprocess.run(["git", "add", "."], cwd=repo, check=True, env=env)
        subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, env=env)

    def _tmp(self):
        import tempfile

        path = tempfile.mkdtemp()
        self.addCleanup(lambda: __import__("shutil").rmtree(path, ignore_errors=True))
        return path
