import re

CITATION_PATTERN = re.compile(r"\[([A-Za-z0-9_-]+)\]")


def extract_citations(answer: str) -> list[str]:
    return list(dict.fromkeys(CITATION_PATTERN.findall(answer)))


def validate_citations(
    answer: str,
    allowed_document_ids: set[str],
) -> list[str]:
    citations = extract_citations(answer)

    return [
        citation
        for citation in citations
        if citation not in allowed_document_ids
    ]
