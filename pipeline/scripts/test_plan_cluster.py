"""test_plan_cluster.py — unit tests for the PURE size-screen helper (no PDF).

_screen_component decides keep/drop for a connected component and names the reason, so the
gate can surface a real piece a filter discarded instead of losing it silently.

    python test_plan_cluster.py
"""
import plan_cluster as C


def test_keeps_normal_furniture():
    assert C._screen_component(600, 600) == (True, "kept")
    assert C._screen_component(2200, 1000) == (True, "kept")


def test_drops_thin_dim_tick():
    keep, reason = C._screen_component(100, 2000)
    assert keep is False and reason == "thin", (keep, reason)
    assert C._screen_component(2000, 100)[1] == "thin"


def test_drops_merged_blob_only_when_both_axes_large():
    assert C._screen_component(4000, 4000) == (False, "merged_blob")
    # a long narrow run is NOT a merged blob (one axis <= 3600) -> kept
    assert C._screen_component(5000, 600) == (True, "kept")


def test_boundaries():
    assert C._screen_component(150, 150) == (True, "kept")     # exactly at the thin floor
    assert C._screen_component(149, 600)[1] == "thin"
    assert C._screen_component(3600, 3600) == (True, "kept")   # not both > 3600
    assert C._screen_component(3601, 3601) == (False, "merged_blob")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
        print(f"  ok  {t.__name__}")
    print(f"\n{passed}/{len(tests)} plan_cluster tests passed")
