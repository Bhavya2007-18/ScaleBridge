"""Integration test for the end-to-end assessment workflow."""

from __future__ import annotations

import pytest


def test_end_to_end_assessment_workflow() -> None:
    """AssessmentService orchestration is pending refactor to the science engine.

    The full workflow is already covered by ``tests/test_api_workflow.py``.
    """
    pytest.skip("AssessmentService pending refactor to science engine pipeline")
