class LCG:
    """Generador Congruencial Lineal — produce números uniformes en (0, 1).

    Referencia de parámetros: Knuth, "The Art of Computer Programming" Vol.2
    Mismos parámetros usados por glibc (biblioteca estándar de C en Linux).
    """

    # Parámetros de Knuth — período máximo = 2^32 = 4,294,967,296 números
    A = 1664525
    C = 1013904223
    M = 2 ** 32

    def __init__(self, seed: int):
        # seed % M garantiza que _x siempre esté dentro del rango [0, M-1]
        self._x = seed % self.M

    def next_float(self) -> float:
        """Devuelve el siguiente número uniforme en (0, 1)."""
        self._x = (self.A * self._x + self.C) % self.M
        return self._x / self.M

    def next_int(self, low: int, high: int) -> int:
        """Devuelve un entero aleatorio en [low, high] inclusive."""
        return low + int(self.next_float() * (high - low + 1))
