from policy_pilot.chunking import DOCUMENT_INFO, split_markdown

SAMPLE = """# Title

Version 1 · valid from 2026-01-01

## 1. First
Text one.

## 2. Second
Text two.
"""


def test_one_chunk_per_section_plus_document_info():
    chunks = split_markdown(SAMPLE)
    assert [c.section for c in chunks] == [DOCUMENT_INFO, "1. First", "2. Second"]


def test_last_section_is_not_lost():
    chunks = split_markdown(SAMPLE)
    assert chunks[-1].text == "Text two."


def test_title_is_not_part_of_any_chunk():
    chunks = split_markdown(SAMPLE)
    assert all("# Title" not in c.text for c in chunks)


def test_long_section_is_split_at_paragraphs():
    paragraphs = ["A" * 700, "B" * 700, "C" * 700]
    markdown = "## Long\n" + "\n\n".join(paragraphs)
    chunks = split_markdown(markdown)
    assert len(chunks) == 3
    assert all(len(c.text) <= 1200 for c in chunks)