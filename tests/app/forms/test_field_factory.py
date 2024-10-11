import pytest

from app.data_models.data_stores import DataStores
from app.forms import error_messages
from app.forms.field_handlers import get_field_handler
from app.questionnaire import QuestionnaireSchema
from app.questionnaire.rules.rule_evaluator import RuleEvaluator
from app.questionnaire.value_source_resolver import ValueSourceResolver


def test_invalid_field_type_raises_on_invalid():
    schema = QuestionnaireSchema(
        {
            "questionnaire_flow": {
                "type": "Linear",
                "options": {"summary": {"collapsible": False}},
            }
        }
    )

    metadata = {
        "user_id": "789473423",
        "schema_name": "0000",
        "collection_exercise_sid": "test-sid",
        "period_id": "2016-02-01",
        "period_str": "2016-01-01",
        "ref_p_start_date": "2016-02-02",
        "ref_p_end_date": "2016-03-03",
        "ru_ref": "12345678901A",
        "ru_name": "Apple",
        "return_by": "2016-07-07",
        "case_id": "1234567890",
        "case_ref": "1000000000000001",
    }

    rule_evaluator = RuleEvaluator(
        data_stores=DataStores(),
        schema=schema,
        location=None,
    )

    value_source_resolver = ValueSourceResolver(
        evaluator=rule_evaluator,
        data_stores=DataStores(metadata=metadata, response_metadata={}),
        schema=schema,
        location=None,
        list_item_id=None,
        escape_answer_values=False,
    )

    # Given
    invalid_field_type = "Football"
    # When / Then
    with pytest.raises(KeyError):
        get_field_handler(
            answer_schema={"type": invalid_field_type},
            value_source_resolver=value_source_resolver,
            rule_evaluator=rule_evaluator,
            error_messages=error_messages,
        )
