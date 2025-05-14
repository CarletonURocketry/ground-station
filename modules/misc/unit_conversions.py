# Unit conversion functions
# Thomas Selwyn (Devil)
# Matteo Golin (linguini1)


def milli_degrees_to_celsius(milli_degrees: int) -> float:
    """Returns the passed milli degrees Celsius value into Celsius.
    Args:
        milli_degrees (int): The temperature in milli degrees Celsius

    Returns:
        float: The temperature in Celsius"""

    return round(milli_degrees / 1000, 2)


def celsius_to_fahrenheit(celsius: float) -> float:
    """Returns the passed Celsius value in Fahrenheit.
    Args:
        celsius (float): The temperature into Celsius

    Returns:
        float: The temperature in Fahrenheit"""

    return round((celsius * 1.8) + 32, 1)


def metres_to_feet(metres: float) -> float:
    """Returns the passed metres value into feet.
    Args:
        metres (float): The distance in metres

    Returns:
        float: The distance in feet"""

    return round(metres * 3.28, 1)


def pascals_to_psi(pascals: int) -> float:
    """Returns the passed pascals value into psi.
    Args:
        pascals (int): The pressure in pascals

    Returns:
        float: The pressure in psi"""

    return round(pascals / 6895, 2)


def millimeters_to_meters(millimeters: int) -> float:
    """Returns the passed millimeters value into meters.
    Args:
        millimeters (int): The distance in millimeters

    Returns:
        float: The distance in meters
    """

    return round(millimeters / 1000, 2)


def centimeters_to_meters(centimeters: int) -> float:
    """Returns the passed centimeters value into meters.
    Args:
        centimeters (int): The distance in centimeters

    Returns:
        float: The distance in meters
    """

    return round(centimeters / 100, 2)


def milliseconds_to_seconds(milliseconds: int) -> float:
    """Returns the passed milliseconds value into seconds.
    Args:
        milliseconds (int): The time in milliseconds

    Returns:
        float: The time in seconds
    """

    return round(milliseconds / 1000, 2)


def tenthdegrees_to_degrees(tenthdegrees: int) -> float:
    """Returns the passed tenth degree per second value into degrees per second.
    Args:
        tenthdegrees (int): The angular velocity in tenths of degrees per second

    Returns:
        float: The angular velocity in degrees per second
    """

    return round(tenthdegrees / 10, 2)


def microdegrees_to_degrees(microdegrees: int) -> float:
    """Returns the passed microdegree value into degrees.
    Args:
        microdegrees (int): The angle microdegrees

    Returns:
        float: The angle in degrees
    """

    return round(microdegrees / pow(10, 7), 2)


def magnitude(x: float, y: float, z: float) -> float:
    """Returns the magnitude of the 3D vector specified by the input values
    Args:
        x (float): x component of the vector
        y (float): y component of the vector
        z (float): z component of the vector

    Returns:
        float: Magnitude of vector
    """

    return round(((x**2) + (y**2) + (z**2)) ** 0.5, 2)
