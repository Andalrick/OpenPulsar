from enum import Enum


class SpecialAction(Enum):
    DPI_PLUS_50 = "dpi_plus_50"
    DPI_MINUS_50 = "dpi_minus_50"

    DPI_PLUS_100 = "dpi_plus_100"
    DPI_MINUS_100 = "dpi_minus_100"

    NEXT_PROFILE = "next_profile"
    PREVIOUS_PROFILE = "previous_profile"
