from pydantic import BaseModel, ConfigDict


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_id: int
    entity_type: str
    value: str
    source_evidence_id: int | None = None
