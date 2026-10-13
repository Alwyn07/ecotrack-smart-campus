class Room:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        self.occupancy = 0
        self.appliances = []

    def add_appliance(self, appliance):
        self.appliances.append(appliance)

    def calculate_power(self):
        total_power = 0

        for appliance in self.appliances:
            total_power += appliance.get_power()

        return total_power

    def display(self):
        print(f"\nRoom: {self.name}")
        print(f"Capacity: {self.capacity}")
        print(f"Occupancy: {self.occupancy}")

        print("\nAppliances:")

        for appliance in self.appliances:
            status = "ON" if appliance.status else "OFF"

            print(
                f"  {appliance.name:<12} "
                f"{status:<3} "
                f"{appliance.get_power():>4} W"
            )

        print(f"\nRoom Power: {self.calculate_power()} W")


class Building:
    def __init__(self, name):
        self.name = name
        self.rooms = []

    def add_room(self, room):
        self.rooms.append(room)

    def calculate_power(self):
        total_power = 0

        for room in self.rooms:
            total_power += room.calculate_power()

        return total_power