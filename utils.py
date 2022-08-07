
class Precondition:
    def __init__(self, name, type, value, tied_to=None):
        self.name = name
        self.type = type
        self.value = value
        self.tied_to = tied_to if tied_to is not None else None
    
    def __repr__(self) -> str:
        return f'Precondition: ("{self.name}","{self.type}", "{self.value}", "{self.tied_to}")'

class Effect:
    def __init__(self, name, type, value, tied_to=None):
        self.name = name
        self.type = type
        self.value = value
        self.tied_to = tied_to if tied_to is not None else None
        
    def __repr__(self) -> str:
        return f'Effect:  ("{self.name}","{self.type}", "{self.value}", "{self.tied_to}")'

class Location:
    def __init__(self, name, preconditions = None, effects = None):
        self.name = name
        self.preconditions = preconditions if preconditions is not None else None
        self.effects = effects if effects is not None else None


class AbstractTask:
    def __init__(self, name, methods):
      self.name = name
      self.methods = methods
    
    def __repr__(self) -> str:
        return f'Abstract Task (AT): ("{self.name}","{self.methods}")'