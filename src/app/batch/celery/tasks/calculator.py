import logging
from container import inject
from datetime import datetime

@inject
def add(
    log: logging.Logger
    , x: int
    , y: int
) -> int:
    """_summary_

    Args:
        x (int): _description_
        y (int): _description_
        log (logging.Logger): _description_

    Returns:
        int: _description_
    """
    result = x + y
    log.debug(result)
    return result

@inject
def sub(
    log: logging.Logger
    , x: int
    , y: int
) -> int:
    """뺄셈 함수

    Args
    ----
    x: int
    y: int

    Returns
    -------
    : int
         x - y 차
    """
    return x - y

@inject
def mul(
    log: logging.Logger
    , x: int
    , y: int
) -> int:
    """곱셈 함수

    Args
    ----
    x: int
    y: int

    Returns
    -------
    : int
         x * y 곱
    """
    result = x * y
    log.debug(result)
    return result

def div(
    x: int = 2
    , y: int = 1
) -> int:
    """나눗셈 함수

    Args
    ----
    x: int
    y: int

    Returns
    -------
    : int
         x + y 나눗셈
    """
    return x / y