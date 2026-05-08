from typing import Protocol


class RNG(Protocol):
    """Interfaz que debe cumplir cualquier generador de números aleatorios.

    Cualquier clase que tenga next_float() cumple este contrato
    automáticamente — sin necesidad de heredar de RNG.
    """

    def next_float(self) -> float:
        """Devuelve un número uniforme en (0, 1)."""
        ...
