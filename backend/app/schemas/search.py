from pydantic import BaseModel

from app.schemas.financial_records import FinancialRecordResponse
from app.schemas.uploads import UploadMetadataResponse


class SearchResultResponse(BaseModel):
    upload: UploadMetadataResponse
    financial_record: FinancialRecordResponse | None
    snippet: str | None
    rank: float | None
