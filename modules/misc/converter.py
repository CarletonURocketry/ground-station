# Unit conversion functions
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)


def milli_degrees_to_celsius(milli_degrees: int) -> float:
    """Returns the passed milli degrees Celsius value in Celsius.
    Args:
        milli_degrees (int): The temperature in milli degrees Celsius

    Returns:
        float: The temperature in Celsius"""

    return round(milli_degrees / 1000, 2)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Returns the passed Celsius value in Fahrenheit.
    Args:
        celsius (float): The temperature in Celsius

    Returns:
        float: The temperature in Fahrenheit"""

    return round((celsius * 1.8) + 32, 1)


def metres_to_feet(metres: float) -> float:
    """Returns the passed metres value in feet.
    Args:
        metres (float): The distance in metres

    Returns:
        float: The distance in feet"""

    return round(metres * 3.28, 1)


def pascals_to_psi(pascals: int) -> float:
    """Returns the passed pascals value in psi.
    Args:
        pascals (int): The pressure in pascals

    Returns:
        float: The pressure in psi"""

    return round(pascals / 6895, 2)
