class Appliance:
    def __init__(self, name, rated_power, quantity=1, status=False):
        self.name = name
        self.rated_power = rated_power
        self.quantity = quantity
        self.status = status

    def get_power(self):
        if self.status:
            return self.rated_power * self.quantity
        return 0

    def turn_on(self):
        self.status = True

    def turn_off(self):
        self.status = False