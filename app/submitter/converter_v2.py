from datetime import datetime
from typing import Any, Mapping, OrderedDict, Union

from structlog import get_logger

from app.data_models import AnswerStore, ListStore, QuestionnaireStore
from app.data_models.metadata_proxy import MetadataProxy
from app.questionnaire.questionnaire_schema import (
    DEFAULT_LANGUAGE_CODE,
    QuestionnaireSchema,
)
from app.questionnaire.routing_path import RoutingPath
from app.submitter.convert_payload_0_0_1 import convert_answers_to_payload_0_0_1
from app.submitter.convert_payload_0_0_3 import convert_answers_to_payload_0_0_3

logger = get_logger()

MetadataType = Mapping[str, Union[str, int, list, dict]]


class DataVersionError(Exception):
    def __init__(self, version: str):
        super().__init__()
        self.version = version

    def __str__(self) -> str:
        return f"Data version {self.version} not supported"


def convert_answers_v2(
    schema: QuestionnaireSchema,
    questionnaire_store: QuestionnaireStore,
    routing_path: RoutingPath,
    submitted_at: datetime,
    flushed: bool = False,
) -> dict[str, Any]:
    """
    Create the JSON answer format for down stream processing, the format can be found here:
    https://github.com/ONSdigital/ons-schema-definitions/docs/eq_runner_to_downstream_payload_v2.m

    Args:
        schema: QuestionnaireSchema instance with populated schema json
        questionnaire_store: EncryptedQuestionnaireStorage instance for accessing current questionnaire data
        routing_path: The full routing path followed by the user when answering the questionnaire
        submitted_at: The date and time of submission
        flushed: True when system submits the users answers, False when submitted by user.
    Returns:
        Data payload
    """
    if metadata := questionnaire_store.metadata:
        response_metadata = questionnaire_store.response_metadata
        answer_store = questionnaire_store.answer_store
        list_store = questionnaire_store.list_store

        survey_id = schema.json["survey_id"]

        payload = {
            "case_id": metadata["case_id"],
            "tx_id": metadata["tx_id"],
            "type": "uk.gov.ons.edc.eq:surveyresponse",
            "version": metadata["version"],
            "data_version": schema.json["data_version"],
            "origin": "uk.gov.ons.edc.eq",
            "collection_exercise_sid": metadata["collection_exercise_sid"],
            "schema_name": metadata["schema_name"],
            "survey_id": survey_id,
            "flushed": flushed,
            "submitted_at": submitted_at.isoformat(),
            "launch_language_code": metadata["language_code"] or DEFAULT_LANGUAGE_CODE,
        }

        optional_survey_metadata_properties = get_optional_survey_metadata_properties(
            metadata
        )
        optional_properties = get_optional_payload_properties(
            metadata, response_metadata
        )

        if metadata["survey_metadata"] and metadata["survey_metadata"].data:
            payload["survey_metadata"] = dict(metadata["survey_metadata"].data)
            payload["survey_metadata"].update(optional_survey_metadata_properties)  # type: ignore

        payload["data"] = get_payload_data(
            data_version=schema.json["data_version"],
            answer_store=answer_store,
            list_store=list_store,
            schema=schema,
            routing_path=routing_path,
            metadata=metadata,
            response_metadata=response_metadata,
        )

        logger.info("converted answer ready for submission")

        return payload | optional_properties


def get_optional_payload_properties(
    metadata: MetadataProxy, response_metadata: Mapping
) -> MetadataType:
    payload = {}

    for key in ["channel", "region_code"]:
        if value := metadata[key]:
            payload[key] = value
    if started_at := response_metadata.get("started_at"):
        payload["started_at"] = started_at

    return payload


def get_optional_survey_metadata_properties(metadata: MetadataProxy) -> MetadataType:
    survey_metadata = {}

    for key in ["form_type", "case_ref", "case_type"]:
        if value := metadata[key]:
            survey_metadata[key] = value

    return survey_metadata


def get_payload_data(
    data_version: str,
    answer_store: AnswerStore,
    list_store: ListStore,
    schema: QuestionnaireSchema,
    routing_path: RoutingPath,
    metadata: MetadataProxy,
    response_metadata: Mapping,
) -> Union[OrderedDict[str, Any], dict[str, Union[list[Any]]]]:
    if data_version == "0.0.1":
        return convert_answers_to_payload_0_0_1(
            metadata, response_metadata, answer_store, list_store, schema, routing_path
        )
    if data_version == "0.0.3":
        return {
            "answers": convert_answers_to_payload_0_0_3(
                answer_store, list_store, schema, routing_path
            ),
            "lists": list_store.serialize(),
        }

    raise DataVersionError(schema.json["data_version"])