import math

from src.rng import RNG


def exponential(rng: RNG, lam: float) -> float:
    """Tiempo entre llegadas de clientes — distribucion Exponencial(lambda).

    Args:
        rng: generador de numeros uniformes en (0, 1)
        lam: tasa de llegadas en clientes por minuto

    Returns:
        Minutos hasta el proximo cliente.
    """
    U = rng.next_float()
    return -math.log(U) / lam


def uniform(rng: RNG, a: float, b: float) -> float:
    """Tiempo de preparacion de un pedido — distribucion Uniforme[a, b].

    Args:
        rng: generador de numeros uniformes en (0, 1)
        a  : tiempo minimo en minutos
        b  : tiempo maximo en minutos

    Returns:
        Tiempo de preparacion en minutos.
    """
    U = rng.next_float()
    return a + (b - a) * U


def bernoulli(rng: RNG, p: float) -> bool:
    """Tipo de cliente — True: sandwich, False: sushi.

    Args:
        rng: generador de numeros uniformes en (0, 1)
        p  : probabilidad de que el cliente quiera sandwich

    Returns:
        True si el cliente quiere sandwich, False si quiere sushi.
    """
    U = rng.next_float()
    return U < p
