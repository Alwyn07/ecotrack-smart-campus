VOLTAGE = 230


def calculate_current(power):
    if power == 0:
        return 0

    return power / VOLTAGE


def calculate_energy(power, hours):
    power_kw = power / 1000
    return power_kw * hours