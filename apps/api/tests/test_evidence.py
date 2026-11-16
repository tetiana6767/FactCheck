"""Тести пошукового адаптера й реєстру доказів."""

from app.schemas.check import Claim, Evidence
from app.services.evidence_ledger import EvidenceLedger
from app.services.search_gateway import InMemorySearchGateway


def test_test_corpus_links_evidence_to_claim() -> None:
    claim = Claim(
        id="claim-7",
        text="Київ — столиця України.",
        start=0,
        end=25,
    )

    evidence = InMemorySearchGateway().search(claim)

    assert len(evidence) == 1
    assert evidence[0].claim_id == "claim-7"
    assert evidence[0].source_type == "test_corpus"


def test_test_corpus_returns_empty_tuple_for_unknown_claim() -> None:
    claim = Claim(id="claim-1", text="Невідома теза.", start=0, end=14)

    assert InMemorySearchGateway().search(claim) == ()


def test_ledger_deduplicates_same_claim_and_evidence() -> None:
    evidence = Evidence(
        id="evidence-1",
        claim_id="claim-1",
        title="Тест",
        url="urn:factcheck:test:evidence-1",
        quote="Тестова цитата.",
        source_type="test_corpus",
    )
    ledger = EvidenceLedger()

    ledger.add(evidence)
    ledger.add(evidence)

    assert ledger.snapshot().items == (evidence,)
