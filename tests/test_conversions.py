# Test cases for conversion functions
__author__ = "Matteo Golin"

# Imports
import pytest
from ground_station.misc.unit_conversions import celsius_to_fahrenheit, metres_to_feet, pascals_to_psi


# Tests
def test_celsius_to_fahrenheit() -> None:
    """Test that Celsius is properly converted to Fahrenheit."""
    assert celsius_to_fahrenheit(12.0) == pytest.approx(53.6)  # type: ignore


def test_metres_to_feet() -> None:
    """Test that metres are properly converted to feet."""
    assert metres_to_feet(5.0) == pytest.approx(16.4)  # type: ignore


def test_pascals_to_psi() -> None:
    """Test that metres are properly converted to feet."""
    assert pascals_to_psi(87181) == pytest.approx(12.64)  # type: ignore
