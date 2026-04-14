"""
models.py
---------
Pydantic schema for a single extracted real estate listing.
Used by the extractor to validate and parse Gemini's structured output.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ListingExtraction(BaseModel):
    property_type: Optional[
        Literal[
            "apartment",
            "villa",
            "studio",
            "duplex",
            "penthouse",
            "chalet",
            "townhouse",
            "twin_house",
            "i_villa",
            "land",
            "office",
            "shop",
            "warehouse",
            "building",
            "loft",
            "other",
        ]
    ] = Field(
        default=None,
        description=(
            "The property type word MUST appear explicitly in the ad text. "
            "If no property type word is found, return null. "
            "If a word appears but is not in the enum, return 'other'."
        ),
    )
    transaction_type: Optional[Literal["sale", "rent"]] = Field(
        default="sale",
        description=(
            "Whether the property is for sale or rent. "
            "Keywords: بيع/sale/for sale/resale → 'sale'. "
            "إيجار/rent/for rent/monthly → 'rent'. "
            "If unclear, return null."
        ),
    )
    price: Optional[float] = Field(
        default=None,
        description=(
            "Total asking price. Compute in this priority order:\n"
            "1. Explicit total stated → use it directly.\n"
            "2. Deposit (مقدم) + remaining lump sum (متبقي) both stated → price = deposit + remaining.\n"
            "3. Deposit + installment amount + installment count both stated → price = deposit + (amount × count). "
            "Convert years to months (× 12): '10 سنوات' = 120 months, '5 سنين' = 60 months.\n"
            "4. Installment amount + installment count stated (no deposit) → price = amount × count.\n"
            "5. Deposit only, or installment amount with NO count/period → null.\n"
            "Normalize: '4.5M' / '4.5 مليون' → 4500000. '800k' → 800000. "
            "'35.000' in rent context → 35000 (period = thousands separator)."
        ),
    )
    down_payment: Optional[float] = Field(
        default=None,
        description=(
            "The initial deposit / down payment only, as a plain number. "
            "Keywords: مقدم / down payment / DP / advance. "
            "Normalize the same way as price. "
            "Return null if no deposit is mentioned separately from the total price."
        ),
    )
    currency: Literal["EGP", "USD", "EUR", "other"] = Field(
        default="EGP",
        description=(
            "Currency of the price. "
            "جنيه/EGP/ج.م → 'EGP'. دولار/USD/$ → 'USD'. يورو/EUR/€ → 'EUR'. "
            "ALWAYS output 'EGP' when no currency symbol is mentioned. Never output null."
        ),
    )

    @field_validator("currency", mode="before")
    @classmethod
    def _coerce_currency(cls, v):
        return v if v is not None else "EGP"

    bedrooms: Optional[int] = Field(
        default=None,
        description=(
            "Number of bedrooms. Use 0 for studios. "
            "Extract from patterns like '3 غرف', '2BR', '3 bedrooms', '3 نوم'. "
            "If not stated, return null."
        ),
    )
    compound_name: Optional[str] = Field(
        default=None,
        description=(
            "Name of the compound, gated community, or development project in English. "
            "Common formats: 'Madinaty', 'Palm Hills', 'Mountain View', 'Hyde Park', etc.. "
            "Translate arabic compound names to English (e.g. 'مدينتي' → 'Madinaty', 'هايد بارك' → 'Hyde Park'). "
            "If the property is not in a compound, return null."
        ),
    )
    city: Optional[str] = Field(
        default=None,
        description=(
            "The city where the property is located, always in English. "
            "If its explicitly mentioned, extract directly and translate it in English"
            "If not explicitly mentioned, predict from context when possible "
            "Examples: Cairo, Alexandria, New Cairo, 6th of October City, North Coast, etc. "
            "Return null only if truly uninferable."
        ),
    )
    district: Optional[str] = Field(
        default=None,
        description=(
            "The district, neighborhood, or sub-area within the city, always in English. "
            "Extract directly if explicitly mentioned"
            "If not stated, infer from compound/context"
            "Examples: 5th Settlement, Maadi, Zamalek, Nasr City, Misr El-Gedida, etc. "
            "Return null if uninferable."
        ),
    )
    ad_snippet: Optional[str] = Field(
        default=None,
        description=(
            "A clean, standalone excerpt of THIS specific listing only. "
            "Include: property details, location, price, size. "
            "Exclude: phone numbers, repeated contact lines, other listings "
            "from the same message, emojis, decorative characters."
        ),
    )
    ad_index: int = Field(
        description=(
            "The integer N from the '--- AD N ---' header this listing was "
            "extracted from. If one AD contains multiple listings, all share "
            "the same ad_index."
        ),
    )
