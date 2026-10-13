from appliances import Appliance
from campus import Room, Building
from energy import calculate_current, calculate_energy
from anomaly import detect_energy_waste

import pandas as pd
import os


# ============================================================
# CREATE BUILDINGS
# ============================================================

building_a = Building("Building A")
building_b = Building("Building B")


# ============================================================
# CREATE ROOMS
# ============================================================

classroom_101 = Room("Classroom 101", 40)
classroom_102 = Room("Classroom 102", 40)
computer_lab = Room("Computer Lab", 40)

classroom_201 = Room("Classroom 201", 40)
laboratory = Room("Laboratory", 40)
office = Room("Office", 15)


# ============================================================
# ADD ROOMS TO BUILDINGS
# ============================================================

building_a.add_room(classroom_101)
building_a.add_room(classroom_102)
building_a.add_room(computer_lab)

building_b.add_room(classroom_201)
building_b.add_room(laboratory)
building_b.add_room(office)


# ============================================================
# CLASSROOM 101 APPLIANCES
# ============================================================

lights_101 = Appliance("LED Lights", 18, 6)
fans_101 = Appliance("Fans", 70, 4)
ac_101 = Appliance("AC", 1500, 1)
projector_101 = Appliance("Projector", 300, 1)

classroom_101.add_appliance(lights_101)
classroom_101.add_appliance(fans_101)
classroom_101.add_appliance(ac_101)
classroom_101.add_appliance(projector_101)


# ============================================================
# CLASSROOM 102 APPLIANCES
# ============================================================

lights_102 = Appliance("LED Lights", 18, 6)
fans_102 = Appliance("Fans", 70, 4)
ac_102 = Appliance("AC", 1500, 1)

classroom_102.add_appliance(lights_102)
classroom_102.add_appliance(fans_102)
classroom_102.add_appliance(ac_102)


# ============================================================
# COMPUTER LAB APPLIANCES
# ============================================================

lights_lab = Appliance("LED Lights", 18, 8)
fans_lab = Appliance("Fans", 70, 6)
computers_lab = Appliance("Computers", 250, 20)

computer_lab.add_appliance(lights_lab)
computer_lab.add_appliance(fans_lab)
computer_lab.add_appliance(computers_lab)


# ============================================================
# CLASSROOM 201 APPLIANCES
# ============================================================

lights_201 = Appliance("LED Lights", 18, 6)
fans_201 = Appliance("Fans", 70, 4)

classroom_201.add_appliance(lights_201)
classroom_201.add_appliance(fans_201)


# ============================================================
# LABORATORY APPLIANCES
# ============================================================

lights_lab2 = Appliance("LED Lights", 18, 8)
fans_lab2 = Appliance("Fans", 70, 4)
ac_lab1 = Appliance("AC", 1500, 1)
ac_lab2 = Appliance("AC", 1500, 1)

laboratory.add_appliance(lights_lab2)
laboratory.add_appliance(fans_lab2)
laboratory.add_appliance(ac_lab1)
laboratory.add_appliance(ac_lab2)


# ============================================================
# OFFICE APPLIANCES
# ============================================================

lights_office = Appliance("LED Lights", 18, 4)
ac_office = Appliance("AC", 1500, 1)
computers_office = Appliance("Computers", 250, 3)

office.add_appliance(lights_office)
office.add_appliance(ac_office)
office.add_appliance(computers_office)


# ============================================================
# BUILDINGS AND ROOMS
# ============================================================

buildings = [building_a, building_b]

rooms = [
    classroom_101,
    classroom_102,
    computer_lab,
    classroom_201,
    laboratory,
    office
]


# ============================================================
# ROOM → BUILDING MAPPING
# ============================================================

room_buildings = {
    "Classroom 101": "Building A",
    "Classroom 102": "Building A",
    "Computer Lab": "Building A",
    "Classroom 201": "Building B",
    "Laboratory": "Building B",
    "Office": "Building B"
}


# ============================================================
# RESET SIMULATION
# ============================================================

def reset_simulation():

    for room in rooms:

        room.occupancy = 0

        for appliance in room.appliances:
            appliance.turn_off()


# ============================================================
# SIMULATE PARTICULAR HOUR
# ============================================================

def simulate_time(hour):

    reset_simulation()

    # --------------------------------------------------------
    # 07:00
    # --------------------------------------------------------

    if hour == 7:

        office.occupancy = 3

        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 08:00
    # --------------------------------------------------------

    elif hour == 8:

        classroom_101.occupancy = 20
        classroom_102.occupancy = 18
        classroom_201.occupancy = 20
        office.occupancy = 5

        lights_101.turn_on()
        fans_101.turn_on()

        lights_102.turn_on()
        fans_102.turn_on()

        lights_201.turn_on()
        fans_201.turn_on()

        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 09:00
    # --------------------------------------------------------

    elif hour == 9:

        classroom_101.occupancy = 32
        classroom_102.occupancy = 28
        computer_lab.occupancy = 35
        classroom_201.occupancy = 30
        laboratory.occupancy = 25
        office.occupancy = 8

        # Classroom 101
        lights_101.turn_on()
        fans_101.turn_on()
        projector_101.turn_on()

        # Classroom 102
        lights_102.turn_on()
        fans_102.turn_on()
        ac_102.turn_on()

        # Computer Lab
        lights_lab.turn_on()
        fans_lab.turn_on()
        computers_lab.turn_on()

        # Classroom 201
        lights_201.turn_on()
        fans_201.turn_on()

        # Laboratory
        lights_lab2.turn_on()
        fans_lab2.turn_on()
        ac_lab1.turn_on()
        ac_lab2.turn_on()

        # Office
        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 13:00
    # --------------------------------------------------------

    elif hour == 13:

        office.occupancy = 4

        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 14:00
    # --------------------------------------------------------

    elif hour == 14:

        classroom_101.occupancy = 25
        classroom_102.occupancy = 20
        computer_lab.occupancy = 40
        laboratory.occupancy = 30
        office.occupancy = 8

        # Classroom 101
        lights_101.turn_on()
        fans_101.turn_on()

        # Classroom 102
        lights_102.turn_on()
        fans_102.turn_on()
        ac_102.turn_on()

        # Computer Lab
        lights_lab.turn_on()
        fans_lab.turn_on()
        computers_lab.turn_on()

        # Laboratory
        lights_lab2.turn_on()
        fans_lab2.turn_on()
        ac_lab1.turn_on()
        ac_lab2.turn_on()

        # Office
        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 17:00
    # --------------------------------------------------------

    elif hour == 17:

        office.occupancy = 5

        lights_office.turn_on()
        ac_office.turn_on()
        computers_office.turn_on()


    # --------------------------------------------------------
    # 18:00 - ENERGY WASTE SCENARIO
    # --------------------------------------------------------

    elif hour == 18:

        classroom_102.occupancy = 0

        # Lights and AC accidentally left ON
        lights_102.turn_on()
        ac_102.turn_on()


# ============================================================
# RUN SIMULATION
# ============================================================

records = []

simulation_hours = [
    7,
    8,
    9,
    13,
    14,
    17,
    18
]


for hour in simulation_hours:

    simulate_time(hour)

    print("\n" + "=" * 60)
    print(f"TIME: {hour:02d}:00")
    print("=" * 60)


    # --------------------------------------------------------
    # CAMPUS POWER
    # --------------------------------------------------------

    total_power = 0

    for building in buildings:
        total_power += building.calculate_power()


    total_power_kw = total_power / 1000

    total_current = calculate_current(total_power)

    total_energy = calculate_energy(total_power, 1)


    print(f"Campus Power : {total_power_kw:.2f} kW")
    print(f"Campus Current: {total_current:.2f} A")
    print(f"Energy       : {total_energy:.2f} kWh")


    # --------------------------------------------------------
    # ROOM STATUS
    # --------------------------------------------------------

    print("\nROOM STATUS")
    print("-" * 60)


    for room in rooms:

        power = room.calculate_power()

        print(
            f"{room.name:<18} "
            f"Occupancy: {room.occupancy:<3} "
            f"Power: {power:>5} W"
        )


        # ----------------------------------------------------
        # ENERGY WASTE DETECTION
        # ----------------------------------------------------

        if detect_energy_waste(room):

            print("  ⚠ ENERGY WASTE DETECTED!")
            print("    Reason: Room is unoccupied but consuming power.")


        # ----------------------------------------------------
        # SAVE RECORD
        # ----------------------------------------------------

        record = {
            "timestamp": f"{hour:02d}:00",
            "building": room_buildings[room.name],
            "room": room.name,
            "occupancy": room.occupancy,
            "voltage": 230,
            "current": round(calculate_current(power), 2),
            "power": power,
            "energy": round(calculate_energy(power, 1), 2)
        }

        records.append(record)


# ============================================================
# CREATE DATAFRAME
# ============================================================

df = pd.DataFrame(records)


# ============================================================
# CREATE DATA FOLDER
# ============================================================

os.makedirs("../data", exist_ok=True)


# ============================================================
# SAVE CSV
# ============================================================

df.to_csv("../data/sample_data.csv", index=False)


# ============================================================
# FINAL OUTPUT
# ============================================================

print("\n" + "=" * 60)
print("SIMULATION COMPLETED")
print("=" * 60)

print(f"\nTotal records generated: {len(df)}")

print("\nCSV file created:")
print("../data/sample_data.csv")

print("\nFirst 10 records:")
print(df.head(10))