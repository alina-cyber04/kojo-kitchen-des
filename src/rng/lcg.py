class LCG:
    """Generador Congruencial Lineal — produce números uniformes en (0, 1).

    Implementa la recurrencia x_{n+1} = (A·x_n + C) mod M con parámetros
    de período máximo 2^32. El estado interno _x avanza en cada llamada.

    Attributes:
        A: Multiplicador del generador.
        C: Incremento del generador.
        M: Módulo; define el espacio de estados y el período máximo.
    """

    # Período máximo = 2^32 = 4 294 967 296 números
    A = 1664525
    C = 1013904223
    M = 2 ** 32

    def __init__(self, seed: int) -> None:
        self._x = seed % self.M

    def next_float(self) -> float:
        """Devuelve el siguiente número uniforme en (0, 1).

        Returns:
            Valor en el intervalo abierto (0, 1).
        """
        self._x = (self.A * self._x + self.C) % self.M
        return self._x / self.M

    def next_int(self, low: int, high: int) -> int:
        """Devuelve un entero aleatorio en [low, high] inclusive.

        Args:
            low: Límite inferior del rango (incluido).
            high: Límite superior del rango (incluido).

        Returns:
            Entero uniformemente distribuido en [low, high].
        """
        return low + int(self.next_float() * (high - low + 1))
