# Unit conversion functions
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)

def celsius_to_fahrenheit(celsius: float) -> float:

    """Returns the passed celsius value in fahrenheit as a float."""

    return round((celsius * 1.8) + 32, 1)


def metres_to_feet(metres: float) -> float:

    """Returns the passed metres value in feet as a float."""

    return round(metres * 3.28, 1)
