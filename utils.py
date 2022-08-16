from typing import List

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

class Capability:
    def __init__(self, name, value, tied_to=None) -> None:
        #  I may still need to add the type here, capabilities also have types
        self.name = name
        self.value = value
        self.tied_to = tied_to if tied_to is not None else None

    def __repr__(self) -> str:
        return f'Capability:  ("{self.name}", "{self.value}", "{self.tied_to}")'

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

class MethodData:
    def __init__(self, name, order, effects, preconditions, capabilities):
        self.method_name = name
        self.order = order
        self.effects = effects
        self.preconditions = preconditions
        self.capabilities = capabilities
    def __repr__(self) -> str:
        return f'MethodData: ("{self.method_name}","{self.order}","{self.effects}","{self.preconditions}","{self.capabilities}")'

class Variable:
    def __init__(self, name, type) -> None:
        self.name = name
        self.type = type
    def __repr__(self) -> str:
        return f'MethodData: ("{self.name}","{self.type}")'

    
