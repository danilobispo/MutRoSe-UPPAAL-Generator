from typing import List
import uppaalpy


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

class MethodData:
    def __init__(self, name, order, effects, preconditions):
        self.method_name = name
        self.order = order
        self.effects = effects
        self.preconditions = preconditions
    def __repr__(self) -> str:
        return f'MethodData: ("{self.method_name}","{self.order}","{self.effects}","{self.preconditions}")'


        
def generate_uppaal_template_from_method(
    target_nta: uppaalpy.NTA, 
    template_name: str, 
    method_order: List[MethodData]):
    print('kk eaemen')

    
