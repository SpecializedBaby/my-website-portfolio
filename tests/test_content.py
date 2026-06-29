from datetime import date
from pathlib import Path

import pytest

from app import content as content_mod
from app.content import ContentError, load_all, load_data, load_posts

PROJECT_DIR = Path(__file__).resolve().parent.parent
CONTENT_DIR = PROJECT_DIR / "content"


def _write_post(dirpath: Path, name: str, front: str, body: str = "Body text here.") -> None:
    (dirpath / name).write_text(f"---\n{front}\n---\n\n{body}\n", encoding="utf-8")


def test_loads_real_site_data():
    site = load_data(CONTENT_DIR / "data.yaml")
    assert site.profile.name == "Dmytro Kostevskyi"
    assert site.profile.initials == "DK"
    assert site.socials and site.products and site.experience
    assert site.experience[0].roles  # nested dataclasses parsed


def test_real_posts_load_and_sort_newest_first():
    posts = load_posts(CONTENT_DIR / "posts")
    assert len(posts) == 6
    dates = [p.date for p in posts]
    assert dates == sorted(dates, reverse=True)
    assert all(p.body_html for p in posts)


def test_slug_comes_from_filename(tmp_path):
    _write_post(tmp_path, "my-first-post.md", "title: Hi\ndate: 2026-01-01\ntag: X\nexcerpt: e")
    posts = load_posts(tmp_path)
    assert posts[0].slug == "my-first-post"


def test_read_time_for_known_word_count(tmp_path):
    body = " ".join(["word"] * 400)  # 400 words / 200 wpm -> 2 min
    _write_post(tmp_path, "p.md", "title: T\ndate: 2026-01-01\ntag: X\nexcerpt: e", body=body)
    assert load_posts(tmp_path)[0].read == "2 min read"


def test_read_time_minimum_is_one_minute(tmp_path):
    _write_post(tmp_path, "p.md", "title: T\ndate: 2026-01-01\ntag: X\nexcerpt: e", body="short")
    assert load_posts(tmp_path)[0].read == "1 min read"


def test_date_parsed_to_date_object(tmp_path):
    _write_post(tmp_path, "p.md", "title: T\ndate: 2026-03-09\ntag: X\nexcerpt: e")
    assert load_posts(tmp_path)[0].date == date(2026, 3, 9)


def test_missing_required_frontmatter_raises(tmp_path):
    _write_post(tmp_path, "bad.md", "title: T\ndate: 2026-01-01\ntag: X")  # no excerpt
    with pytest.raises(ContentError):
        load_posts(tmp_path)


def test_bad_date_raises(tmp_path):
    _write_post(tmp_path, "bad.md", "title: T\ndate: not-a-date\ntag: X\nexcerpt: e")
    with pytest.raises(ContentError):
        load_posts(tmp_path)


def test_empty_body_raises(tmp_path):
    _write_post(tmp_path, "bad.md", "title: T\ndate: 2026-01-01\ntag: X\nexcerpt: e", body="")
    with pytest.raises(ContentError):
        load_posts(tmp_path)


def test_missing_profile_raises(tmp_path):
    (tmp_path / "data.yaml").write_text("socials: []\n", encoding="utf-8")
    with pytest.raises(ContentError):
        load_data(tmp_path / "data.yaml")


def test_load_all_and_lookup():
    bundle = load_all(CONTENT_DIR)
    assert bundle.site.profile.name == "Dmytro Kostevskyi"
    a_slug = bundle.posts[0].slug
    assert bundle.post_by_slug(a_slug) is bundle.posts[0]
    assert bundle.post_by_slug("does-not-exist") is None
