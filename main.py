import eseries
from prefixed import Float


# Format a copyable resistance value
def resistance(value):
    return f"{Float(value):.2H}"


# Format a number according to the SI prefixes
def si(value, precision=2):
    return ("{:!." + str(precision) + "h}").format(Float(value))


# Equality testing for floats
def float_eq(a, b):
    return abs(a - b) < 1e-9


# Checks if "a" is a 10-multiple of "b"
def ten_multiple_of(a, b, limit=3):
    for i in range(limit):
        if float_eq(a, b * 10 ** i):
            return True
    return False


def resistor_divider(f, target, series, f_output_for_current=False, *constraints):
    high = float("inf")
    high_r1 = high_r2 = high_i = 0
    low = float("-inf")
    low_r1 = low_r2 = low_i = 0

    for r1 in eseries.erange(series, 1, 10e6):  # Stop at 10 MOhm
        for r2 in eseries.erange(series, 1, 10e6):
            try:
                result = f(r1, r2)
                for constraint in constraints:
                    if not constraint(r1, r2, result):
                        break
                else:
                    u = result if f_output_for_current else target
                    # For tracking the smallest current, add a constraint to limit it from becoming too small
                    i = u / (r1 + r2)

                    if result > target:
                        if result < high or (result == high and i < high_i):
                            high = result
                            high_r1 = r1
                            high_r2 = r2
                            high_i = i
                    else:
                        if result > low or (result == low and i < low_i):
                            low = result
                            low_r1 = r1
                            low_r2 = r2
                            low_i = i

            except ZeroDivisionError:
                pass

    print(
        f"Nearest above: r1 = {resistance(high_r1)} and r2 = {resistance(high_r2)}: {si(high, 3)}V ({(high - target) * 100 / target:.3g} % error), {si(high_i)}A")
    print(
        f"Nearest below: r1 = {resistance(low_r1)} and r2 = {resistance(low_r2)}: {si(low, 3)}V ({(target - low) * 100 / target:.3g} % error), {si(low_i)}A")


if __name__ == "__main__":
    # TPS7A90 output voltage control
    v_ref = 0.8
    resistor_divider(
        lambda r1, r2: ((r1 + r2) * v_ref) / r2,  # Observe float precision!
        2.9,
        eseries.E24,
        True,
        lambda r1, r2, res: v_ref / r2 >= 5e-6, # TPS7A90 noise constraint
        lambda r1, r2, res: res / (r1 + r2) >= 300e-6, # Reasonable minimum current
        lambda r1, r2, res: res / (r1 + r2) <= 1e-3, # Maximum current
        lambda r1, r2, res: not float_eq(r2, 910), # 910 Ohm resistors are not basic parts
        # lambda r1, r2, res: not ten_multiple_of(r2, 9.1),
    )
