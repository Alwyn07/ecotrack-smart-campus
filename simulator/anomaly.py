def detect_energy_waste(room, power_threshold=500):
    """
    Detect energy wastage when a room is unoccupied
    but still consuming significant power.
    """

    if room.occupancy == 0 and room.calculate_power() > power_threshold:
        return True

    return False