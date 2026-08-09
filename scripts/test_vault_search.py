"""Tests for vault_search's TIER layer.

The retriever itself is covered by scripts/eval_retrieval.py against a golden
set. What is pinned here is the thing that was measured and then fixed on
2026-08-08: raw research prose outranking distilled truth on its own topic, and
a caller having no way to tell the two apart from the output.

Two properties, and the second matters more than the first:

  1. `--tier` filters, and the tier is DERIVED from the path so a file added
     tomorrow lands in the right tier with nobody registering it.
  2. The default corpus and its RANKING are unchanged. Every existing caller —
     eval_retrieval's golden set among them — keeps the behaviour it had. The
     tier is added as a LABEL, not as a silent re-ranking, because a retrieval
     change that improves one query and quietly moves twenty others is not an
     improvement anybody measured.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_search as VS  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO, "scripts", "vault_search.py")


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True,
                       text=True, encoding="utf-8", cwd=REPO)
    return p.returncode, p.stdout, p.stderr


# --- tier derivation ---------------------------------------------------------

def test_tier_is_derived_from_the_path_not_from_a_list():
    assert VS.tier_of("knowledge/rendering/render-defaults.md") == "distilled"
    assert VS.tier_of("knowledge/_inbox/nlm-bedding-mass/x.md") == "staged"
    assert VS.tier_of("knowledge/studio-vault/00-Studio-Knowledge/x.md") == "vault"
    assert VS.tier_of("docs/research/2026-08-08-upgrade-dr/TRIAGE.md") == "research"


def test_a_file_nobody_registered_still_lands_in_a_tier():
    # The point of deriving: R9b's law is that a rule naming the objects it
    # applies to will always exempt the next one.
    assert VS.tier_of("knowledge/brand_new_domain/thing-invented-tomorrow.md") \
        == "distilled"
    assert VS.tier_of("docs/whatever/new.md") == "research"


# --- the measurement this feature exists for ---------------------------------

JUNCTION_Q = "skirting shadow gap wall floor junction plinth mm"


def test_the_default_corpus_still_buries_distilled_truth_under_research():
    # This is a REGRESSION PIN ON THE PROBLEM, not on the fix. If someone later
    # changes the default ranking, this test fails and they must decide
    # deliberately — rather than discovering it through a re-researched number.
    rc, out, _ = run(JUNCTION_Q, "-k", "4")
    assert rc == 0
    assert "[RESEARCH " in out


def test_tier_distilled_surfaces_the_file_that_holds_the_numbers():
    rc, out, _ = run(JUNCTION_Q, "-k", "1", "--tier", "distilled")
    assert rc == 0
    assert "knowledge/rendering/render-defaults.md" in out
    assert "RESEARCH" not in out and "STAGED" not in out


def test_every_hit_carries_its_tier_so_an_inbox_cannot_pass_as_truth():
    rc, out, _ = run(JUNCTION_Q, "-k", "5")
    assert rc == 0
    for line in [x for x in out.splitlines() if x[:2].strip().rstrip(".").isdigit()]:
        assert any(f"[{t.upper():9s}]" in line for t in VS.TIERS), line


# --- json mode ---------------------------------------------------------------

def test_json_mode_is_parseable_and_names_the_tiers_it_searched():
    rc, out, _ = run(JUNCTION_Q, "-k", "2", "--tier", "distilled", "--json")
    assert rc == 0
    d = json.loads(out)
    assert d["tiers"] == ["distilled"]
    assert d["n_hits"] >= 1 and len(d["hits"]) <= 2
    assert all(h["tier"] == "distilled" for h in d["hits"])
    assert d["hits"][0]["rank"] == 1 and d["hits"][0]["score"] > 0


def test_json_reports_a_miss_as_data_rather_than_as_prose():
    # A caller who says "the vault has nothing on X" can be made to prove it,
    # and n_hits is the only form of that claim anyone else can re-run.
    rc, out, _ = run("qzzxwv unlikelytoken plphtx", "--tier", "distilled", "--json")
    assert rc == 0
    d = json.loads(out)
    assert d["n_hits"] == 0 and d["hits"] == []
    assert d["n_docs"] > 0  # the corpus was searched; the miss is real


def test_a_tier_with_no_documents_fails_rather_than_reporting_a_clean_miss():
    # An empty corpus and a genuine miss must not print the same thing — the
    # mute failure mode, one layer down from the gate that has it too.
    rc, out, err = run("anything", "--root", "templates", "--tier", "staged")
    assert rc == 1
    assert "no indexable documents" in (out + err)


def test_no_tier_conditional_logic_can_reach_the_SCORE():
    """The claim 'default ranking unchanged' must be checkable, or it is decoration.

    An adversarial pass on 2026-08-08 built a mutant that multiplied `staged` scores by 1.8
    in the DEFAULT corpus and every test above still passed — a silent re-ranking is exactly
    the change nobody would notice and everybody would inherit. Golden top-N files are the
    obvious pin and they rot with the corpus, so this pins the MECHANISM instead: tier is
    allowed to FILTER (before indexing) and to LABEL (after ranking), never to weight.
    """
    src = open(os.path.join(REPO, "scripts", "vault_search.py"), encoding="utf-8").read()
    body = src.split("q = tokenize(args.query)", 1)[1].split("if args.json", 1)[0]
    assert "tier" not in body.replace("tier, text", "").replace("cit, tier", ""), (
        "the BM25 scoring loop now mentions `tier` — if that is a deliberate re-ranking, "
        "measure it against scripts/eval_retrieval.py first and rewrite this pin")
    assert "s *=" not in body and "s +=" in body, "score is accumulated, never scaled"
