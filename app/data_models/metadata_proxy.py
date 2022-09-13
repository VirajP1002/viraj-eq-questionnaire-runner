from __future__ import annotations

from collections import abc
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Optional

from werkzeug.datastructures import ImmutableDict


@dataclass(frozen=True)
class SurveyMetadata:
    data: ImmutableDict = field(default_factory=dict)  # type: ignore
    receipting_keys: Optional[tuple] = None

    def __getitem__(self, key: str) -> Optional[Any]:
        return self.data.get(key)


# pylint: disable=too-many-locals
@dataclass(frozen=True)
class MetadataProxy:
    tx_id: str
    account_service_url: str
    case_id: str
    collection_exercise_sid: str
    response_id: str
    survey_metadata: Optional[SurveyMetadata] = None
    schema_url: Optional[str] = None
    schema_name: Optional[str] = None
    language_code: Optional[str] = None
    response_expires_at: Optional[datetime] = None
    channel: Optional[str] = None
    region_code: Optional[str] = None
    version: Optional[str] = None
    roles: Optional[list] = None

    def __getitem__(self, key: str) -> Optional[Any]:
        if self.survey_metadata and key in self.survey_metadata.data:
            return self.survey_metadata.data[key]
        if key:
            return getattr(self, key, None)

    @classmethod
    def from_dict(cls, metadata: Mapping) -> MetadataProxy:
        _metadata = deepcopy(dict(metadata))

        tx_id = _metadata.pop("tx_id", None)
        account_service_url = _metadata.pop("account_service_url", None)
        case_id = _metadata.pop("case_id", None)
        collection_exercise_sid = _metadata.pop("collection_exercise_sid", None)
        response_id = _metadata.pop("response_id", None)
        response_expires_at = _metadata.pop("response_expires_at", None)
        language_code = _metadata.pop("language_code", None)
        schema_name = _metadata.pop("schema_name", None)
        schema_url = _metadata.pop("schema_url", None)
        channel = _metadata.pop("channel", None)
        region_code = _metadata.pop("region_code", None)
        version = _metadata.pop("version", None)
        roles = _metadata.pop("roles", None)

        if version == "v2":
            serialized_metadata = cls.serialize(_metadata.pop("survey_metadata", {}))
            survey_metadata = SurveyMetadata(**serialized_metadata)
        else:
            serialized_metadata = cls.serialize(_metadata)
            survey_metadata = SurveyMetadata(data=serialized_metadata)

        return cls(
            tx_id=tx_id,
            account_service_url=account_service_url,
            case_id=case_id,
            collection_exercise_sid=collection_exercise_sid,
            response_id=response_id,
            response_expires_at=response_expires_at,
            language_code=language_code,
            schema_name=schema_name,
            schema_url=schema_url,
            channel=channel,
            region_code=region_code,
            version=version,
            survey_metadata=survey_metadata,
            roles=roles,
        )

    @classmethod
    def serialize(cls, data: Any) -> Any:
        if isinstance(data, abc.Hashable):
            return data
        if isinstance(data, list):
            return tuple((cls.serialize(item) for item in data))
        if isinstance(data, dict):
            key_value_tuples = {k: cls.serialize(v) for k, v in data.items()}
            return ImmutableDict(key_value_tuples)