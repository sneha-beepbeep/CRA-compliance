"""Playwright + axe-core at 320 px and desktop (technical plan, "Accessibility").

Planned for the phase 1a accessibility pass. Skips cleanly when Playwright or
its browsers aren't installed (they aren't in the build environment).
"""
import pytest

playwright = pytest.importorskip("playwright", reason="Playwright not installed; run the axe-core pass in CI")


def test_axe_placeholder():
    pytest.skip("axe-core scenarios (S-7, S-8, S-8a, S-9 at 320 px and desktop) not written yet")
