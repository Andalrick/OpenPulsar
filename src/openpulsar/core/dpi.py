from dataclasses import dataclass


@dataclass
class Color:
    r: int
    g: int
    b: int


@dataclass
class DpiStage:
    dpi: int
    color: Color
