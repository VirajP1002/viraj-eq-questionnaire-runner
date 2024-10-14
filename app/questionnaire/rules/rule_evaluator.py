from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Generator, Iterable, Sequence, TypeAlias

from app.data_models.data_stores import DataStores
from app.questionnaire import QuestionnaireSchema
from app.questionnaire.placeholder_renderer import PlaceholderRenderer
from app.questionnaire.questionnaire_schema import DEFAULT_LANGUAGE_CODE
from app.questionnaire.resolver import Resolver, ResolverTypes
from app.questionnaire.rules.operations import Operations
from app.questionnaire.rules.operator import Operator
from app.utilities.types import LocationType

RuleEvaluatorTypes: TypeAlias = (
    bool | date | list[str] | list[date] | int | float | Decimal | None
)
ResolvedOperand: TypeAlias = bool | date | ResolverTypes | None


@dataclass
class RuleEvaluator:
    schema: QuestionnaireSchema
    data_stores: DataStores
    location: LocationType | None
    value_source_resolver: Resolver
    routing_path_block_ids: Iterable[str] | None = None
    language: str = DEFAULT_LANGUAGE_CODE

    # pylint: disable=attribute-defined-outside-init
    def __post_init__(self) -> None:
        renderer: PlaceholderRenderer = PlaceholderRenderer(
            language=self.language,
            data_stores=self.data_stores,
            schema=self.schema,
            location=self.location,
        )
        self.operations = Operations(
            language=self.language, schema=self.schema, renderer=renderer
        )

    def _evaluate(self, rule: dict[str, Sequence]) -> bool | date | None:
        operator_name = next(iter(rule))
        operator = Operator(operator_name, self.operations)
        operands = rule[operator_name]

        if not isinstance(operands, Sequence):
            raise TypeError(
                f"The rule is invalid, operands should be of type Sequence and not {type(operands)}"
            )

        resolved_operands: Iterable[ResolvedOperand]

        if operator_name == Operator.MAP:
            resolved_iterables = self._resolve_operand(operands[1])
            resolved_operands = [operands[0], resolved_iterables]
        else:
            resolved_operands = self.get_resolved_operands(operands)

        return operator.evaluate(resolved_operands)

    def _resolve_operand(self, operand: ResolverTypes) -> ResolvedOperand:
        if isinstance(operand, dict) and "source" in operand:
            return self.value_source_resolver.resolve(operand)

        if QuestionnaireSchema.has_operator(operand) and isinstance(operand, dict):
            return self._evaluate(operand)

        return operand

    def get_resolved_operands(
        self, operands: Sequence[ResolverTypes]
    ) -> Generator[ResolvedOperand, None, None]:
        for operand in operands:
            yield self._resolve_operand(operand)

    def evaluate(self, rule: dict[str, Sequence]) -> RuleEvaluatorTypes:
        return self._evaluate(rule)
