from decimal import Decimal

import pytest

from apps.assessments.models import AttemptType
from apps.assessments.services import calculate_osce_result


@pytest.mark.django_db
def test_retake_pass_final_mark_is_capped_at_60(osce_attempt_factory, osce_score_factory):
    attempt = osce_attempt_factory(
        attempt_type=AttemptType.RETAKE,
    )

    station = attempt.osce_exam.stations.first()
    rubric_item = station.rubric_items.first()

    osce_score_factory(
        attempt=attempt,
        station=station,
        rubric_item=rubric_item,
        score=rubric_item.max_score,
    )

    result = calculate_osce_result(attempt=attempt)

    assert result.is_passed is True
    assert result.percentage >= Decimal("60.00")
    assert result.final_mark == Decimal("60.00")