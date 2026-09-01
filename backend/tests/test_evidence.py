from app.domain.evidence import (
    canonicalize_url,
    citation_keys,
    grounding_score,
    invalid_citations,
    uncited_key_blocks,
)


def test_canonicalize_removes_tracking():
    url = "https://Example.com/story/?utm_source=newsletter&b=2&a=1#top"
    assert canonicalize_url(url) == "https://example.com/story?b=2&a=1"


def test_grounding_score_rewards_overlap():
    score = grounding_score(
        "Solar generation increased during 2025",
        "The report says solar generation increased strongly during 2025 across the region.",
    )
    assert score >= 0.6


def test_citation_validation():
    report = "One finding [S1]. Another [S4]."
    assert citation_keys(report) == ["S1", "S4"]
    assert invalid_citations(report, {"S1", "S2"}) == {"S4"}


def test_key_sections_require_citations():
    report = (
        "## Overview\n\n"
        "This is a long factual paragraph that contains enough detail "
        "to require a source citation but has none.\n\n"
        "## Caveats\n\n"
        "This caution can stand without one."
    )

    assert len(uncited_key_blocks(report)) == 1

    cited = (
        "## Overview\n\n"
        "This is a long factual paragraph that contains enough detail "
        "to require a source citation and has one [S1]."
    )

    assert uncited_key_blocks(cited) == []
