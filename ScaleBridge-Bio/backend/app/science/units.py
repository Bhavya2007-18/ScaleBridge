from typing import Any
import pint

# Standardized scientific unit registry for ScaleBridge Bio
ureg = pint.UnitRegistry()
Q_ = ureg.Quantity

# Predefined standard dimensions
ureg.define("percent = 0.01 = %")
ureg.define("vvm = 1 / minute")  # Volume of gas per volume of liquid per minute

def to_si(val: float, unit_str: str, target_unit: str) -> float:
    """Safely converts values between engineering units with strict dimensionality checking."""
    try:
        q = ureg.Quantity(val, unit_str)
        converted = q.to(target_unit)
        return float(converted.magnitude)
    except Exception as e:
        raise ValueError(f"Incompatible unit conversion from {unit_str} to {target_unit}: {str(e)}")
