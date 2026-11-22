"""Unit-aware conversions and dimensional validation using Pint (docs/09, docs/10).

Critical rule (docs/09 §5, docs/11 §2.2):
`rpm` is converted to numeric revolutions per second `1/s` (60 rpm == 1.0 1/s),
NOT via radians (`2*pi` error in tip speed and Reynolds number).
"""

from __future__ import annotations

import pint

from scalebridge_science.contracts import Provenance, Quantity, ValueNature


class UnitDimensionError(ValueError):
    """Raised when a unit is unknown or incompatible with the expected physical dimension."""


class AmbiguousUnitError(ValueError):
    """Raised when a unit requires explicit user disambiguation (e.g. bare '%')."""


ureg = pint.UnitRegistry(autoconvert_offset_to_baseunit=True)
ureg.define("percent_air_saturation = [do_saturation] = pct_air_sat")
ureg.define("vvm = 1 / minute")
ureg.define("SLPM = liter / minute = slpm")
ureg.define("pH_unit = [] = pH")
ureg.define("OD_unit = [] = AU = OD600")

PINT_VERSION: str = getattr(pint, "__version__", "unknown")


VARIABLE_UNIT_SPECS: dict[str, dict[str, str | list[str]]] = {
    # Time-series & batch variables
    "ph": {"si": "pH", "display": "pH", "accepted": ["pH", "dimensionless", ""]},
    "dissolved_oxygen": {
        "si": "percent_air_saturation",
        "display": "% air sat",
        "accepted": ["percent_air_saturation", "% air sat", "%_air_sat", "pct_air_sat"],
    },
    "dissolved_oxygen_conc": {
        "si": "mol / m**3",
        "display": "mmol/L",
        "accepted": ["mol/m^3", "mol/m**3", "mmol/L", "mmol/l", "mol/L"],
    },
    "temperature": {
        "si": "kelvin",
        "display": "degC",
        "accepted": ["degC", "celsius", "K", "kelvin", "degF"],
    },
    "agitation_speed": {
        "si": "1 / second",
        "display": "rpm",
        "accepted": ["rpm", "1/min", "1/s", "1/second", "rps"],
    },
    "airflow": {
        "si": "m**3 / second",
        "display": "L/min",
        "accepted": [
            "L/min",
            "l/min",
            "mL/min",
            "m^3/h",
            "m**3/h",
            "m^3/s",
            "m**3/s",
            "SLPM",
            "slpm",
        ],
    },
    "oxygen_flow": {
        "si": "m**3 / second",
        "display": "L/min",
        "accepted": [
            "L/min",
            "l/min",
            "mL/min",
            "m^3/h",
            "m**3/h",
            "m^3/s",
            "m**3/s",
            "SLPM",
            "slpm",
        ],
    },
    "gas_flow_total": {
        "si": "m**3 / second",
        "display": "L/min",
        "accepted": [
            "L/min",
            "l/min",
            "mL/min",
            "m^3/h",
            "m**3/h",
            "m^3/s",
            "m**3/s",
            "SLPM",
            "slpm",
        ],
    },
    "headspace_pressure": {
        "si": "pascal",
        "display": "bar",
        "accepted": ["Pa", "pascal", "kPa", "bar", "mbar", "psi", "atm"],
    },
    "feed_rate": {
        "si": "m**3 / second",
        "display": "mL/h",
        "accepted": ["mL/h", "ml/h", "L/h", "l/h", "mL/min", "m^3/s", "m**3/s"],
    },
    "feed_cumulative": {
        "si": "m**3",
        "display": "mL",
        "accepted": ["mL", "ml", "L", "l", "m^3", "m**3"],
    },
    "working_volume": {
        "si": "m**3",
        "display": "L",
        "accepted": ["L", "l", "mL", "ml", "m^3", "m**3"],
    },
    "our": {
        "si": "mol / (m**3 * second)",
        "display": "mmol/(L*h)",
        "accepted": ["mmol/(L*h)", "mmol/L/h", "mol/(m^3*s)", "mol/(m**3*s)", "mmol/(l*h)"],
    },
    "cer": {
        "si": "mol / (m**3 * second)",
        "display": "mmol/(L*h)",
        "accepted": ["mmol/(L*h)", "mmol/L/h", "mol/(m^3*s)", "mol/(m**3*s)", "mmol/(l*h)"],
    },
    "power_draw": {
        "si": "watt",
        "display": "W",
        "accepted": ["W", "watt", "kW", "kilowatt"],
    },
    "od600": {"si": "OD600", "display": "OD600", "accepted": ["OD600", "AU", "dimensionless", ""]},
    "biomass_dcw": {
        "si": "kg / m**3",
        "display": "g/L",
        "accepted": ["g/L", "g/l", "kg/m^3", "kg/m**3", "mg/mL"],
    },
    "substrate_glucose": {
        "si": "kg / m**3",
        "display": "g/L",
        "accepted": ["g/L", "g/l", "kg/m^3", "kg/m**3", "mg/L"],
    },
    "product_titre": {
        "si": "kg / m**3",
        "display": "g/L",
        "accepted": ["g/L", "g/l", "kg/m^3", "kg/m**3", "mg/L"],
    },
    # Vessel & medium parameters
    "total_volume": {"si": "m**3", "display": "L", "accepted": ["L", "l", "mL", "m^3", "m**3"]},
    "working_volume_min": {
        "si": "m**3",
        "display": "L",
        "accepted": ["L", "l", "mL", "m^3", "m**3"],
    },
    "working_volume_max": {
        "si": "m**3",
        "display": "L",
        "accepted": ["L", "l", "mL", "m^3", "m**3"],
    },
    "vessel_inner_diameter": {
        "si": "meter",
        "display": "m",
        "accepted": ["m", "meter", "mm", "cm"],
    },
    "vessel_height": {"si": "meter", "display": "m", "accepted": ["m", "meter", "mm", "cm"]},
    "liquid_height_at_working_volume": {
        "si": "meter",
        "display": "m",
        "accepted": ["m", "meter", "mm", "cm"],
    },
    "impeller_diameter": {"si": "meter", "display": "m", "accepted": ["m", "meter", "mm", "cm"]},
    "impeller_power_number": {
        "si": "dimensionless",
        "display": "dimensionless",
        "accepted": ["dimensionless", ""],
    },
    "agitation_speed_min": {
        "si": "1 / second",
        "display": "rpm",
        "accepted": ["rpm", "1/min", "1/s", "1/second", "rps"],
    },
    "agitation_speed_max": {
        "si": "1 / second",
        "display": "rpm",
        "accepted": ["rpm", "1/min", "1/s", "1/second", "rps"],
    },
    "motor_power_limit": {
        "si": "watt",
        "display": "W",
        "accepted": ["W", "watt", "kW", "kilowatt"],
    },
    "gas_flow_min": {
        "si": "m**3 / second",
        "display": "L/min",
        "accepted": [
            "L/min",
            "l/min",
            "mL/min",
            "m^3/h",
            "m**3/h",
            "m^3/s",
            "m**3/s",
            "SLPM",
            "slpm",
        ],
    },
    "gas_flow_max": {
        "si": "m**3 / second",
        "display": "L/min",
        "accepted": [
            "L/min",
            "l/min",
            "mL/min",
            "m^3/h",
            "m**3/h",
            "m^3/s",
            "m**3/s",
            "SLPM",
            "slpm",
        ],
    },
    "max_headspace_pressure": {
        "si": "pascal",
        "display": "bar",
        "accepted": ["Pa", "pascal", "kPa", "bar", "mbar", "psi", "atm"],
    },
    "cooling_capacity": {"si": "watt", "display": "W", "accepted": ["W", "watt", "kW", "kilowatt"]},
    "temperature_min": {
        "si": "kelvin",
        "display": "degC",
        "accepted": ["degC", "celsius", "K", "kelvin", "degF"],
    },
    "temperature_max": {
        "si": "kelvin",
        "display": "degC",
        "accepted": ["degC", "celsius", "K", "kelvin", "degF"],
    },
    "density": {
        "si": "kg / m**3",
        "display": "kg/m^3",
        "accepted": ["kg/m^3", "kg/m**3", "g/L", "g/cm^3", "g/mL"],
    },
    "viscosity": {
        "si": "pascal * second",
        "display": "mPa*s",
        "accepted": ["Pa*s", "pascal*second", "mPa*s", "cP", "centipoise"],
    },
    "oxygen_saturation_concentration": {
        "si": "mol / m**3",
        "display": "mmol/L",
        "accepted": ["mol/m^3", "mol/m**3", "mmol/L", "mmol/l", "mol/L"],
    },
    "kla": {
        "si": "1 / second",
        "display": "1/h",
        "accepted": ["1/s", "1/second", "1/h", "1/hour", "1/min", "h^-1", "s^-1"],
    },
    "mixing_time": {
        "si": "second",
        "display": "s",
        "accepted": ["s", "second", "min", "minute"],
    },
    "max_tip_speed": {
        "si": "meter / second",
        "display": "m/s",
        "accepted": ["m/s", "meter/second", "cm/s"],
    },
    "max_p_per_v": {
        "si": "watt / m**3",
        "display": "W/m^3",
        "accepted": ["W/m^3", "W/m**3", "kW/m^3", "kW/m**3", "W/L"],
    },
    "min_do_required": {
        "si": "percent_air_saturation",
        "display": "% air sat",
        "accepted": ["percent_air_saturation", "% air sat", "%_air_sat", "pct_air_sat"],
    },
    "max_vvm": {
        "si": "1 / second",
        "display": "vvm",
        "accepted": ["vvm", "1/min", "1/s"],
    },
    "estimated_heat_load": {
        "si": "watt",
        "display": "W",
        "accepted": ["W", "watt", "kW", "kilowatt"],
    },
}


def _normalize_unit_token(unit_str: str) -> str:
    token = unit_str.strip()
    if token in ("%", "percent"):
        raise AmbiguousUnitError(
            "Bare '%' is ambiguous. Specify 'percent_air_saturation' for DO or a molar/volume fraction unit."
        )
    if token in ("rpm", "RPM"):
        return "1 / minute"
    if token in ("rps", "RPS"):
        return "1 / second"
    if token in ("% air sat", "pct_air_sat", "%_air_sat"):
        return "percent_air_saturation"
    if token in ("h^-1", "hr^-1", "1/hr"):
        return "1 / hour"
    if token in ("s^-1",):
        return "1 / second"
    return token.replace("^", "**")


def convert_value(value: float, from_unit: str, to_unit: str) -> float:
    """Convert `value` from `from_unit` to `to_unit` with strict dimensional checking."""
    src_norm = _normalize_unit_token(from_unit)
    dst_norm = _normalize_unit_token(to_unit)
    try:
        q = ureg.Quantity(value, src_norm)
        converted = q.to(dst_norm)
        return float(converted.magnitude)
    except (pint.UndefinedUnitError, pint.DimensionalityError, ValueError) as exc:
        raise UnitDimensionError(
            f"Cannot convert {value} from '{from_unit}' to '{to_unit}': {exc}"
        ) from exc


def to_si_quantity(
    value: float,
    unit: str,
    variable_key: str,
    provenance: Provenance = "manual_entry",
    value_nature: ValueNature | None = None,
    source_ref: str | None = None,
    note: str | None = None,
) -> Quantity:
    """Validate `unit` against `variable_key` and return a normalized SI `Quantity`."""
    spec = VARIABLE_UNIT_SPECS.get(variable_key)
    if spec is None:
        raise UnitDimensionError(f"Unknown canonical variable or parameter key '{variable_key}'")

    si_unit = str(spec["si"])
    display_unit = str(spec["display"])
    val_si = convert_value(value, unit, si_unit)
    val_display = convert_value(val_si, si_unit, display_unit)

    resolved_nature: ValueNature
    if value_nature is not None:
        resolved_nature = value_nature
    elif provenance in ("sensor", "lab_assay"):
        resolved_nature = "measured"
    elif provenance == "published_correlation":
        resolved_nature = "estimated"
    elif provenance == "user_assumption":
        resolved_nature = "assumed"
    elif provenance == "calculated":
        resolved_nature = "calculated"
    else:
        resolved_nature = "measured"

    return Quantity(
        value=val_si,
        unit=si_unit,
        original_value=value,
        original_unit=unit,
        display_value=val_display,
        display_unit=display_unit,
        provenance=provenance,
        value_nature=resolved_nature,
        source_ref=source_ref,
        note=note,
    )
