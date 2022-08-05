class Precondition:
    def __init__(self, name, type, value, tied_to=None):
        self.name = name
        self.type = type
        self.value = value
        self.tied_to = tied_to if tied_to is not None else None