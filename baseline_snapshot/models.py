"""The vendor desk's structured purchasing recommendation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class VendorRecommendation(BaseModel):
    model_config = ConfigDict(extra='forbid')

    vendor: str | None = Field(description='Vendor name from the document, or null if unknown.')
    sku: str | None = Field(description='Item SKU from the document, or null if unknown.')
    unit_price: float | None = Field(ge=0, description='Quoted unit price in USD, or null if unknown.')
    lead_time_days: int | None = Field(ge=0, description='Quoted lead time in days, or null if unknown.')
    min_order: int | None = Field(ge=0, description='Minimum order in units, or null if unknown.')
    decision: Literal['recommend', 'do_not_recommend'] = Field(description='Whether all handbook purchasing checks pass.')
    explanation: str = Field(min_length=1, description='One sentence explaining the decision using the handbook.')
