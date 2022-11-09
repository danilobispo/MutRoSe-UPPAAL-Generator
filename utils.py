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
    def __init__(self, name, preconditions=None, effects=None):
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


class Variable(object):
    def __init__(self, var_name, type_name) -> None:
        self.var_name: str = var_name
        self.type_name: str = type_name
        self.predicates_name_list: list[str] = []

    def __hash__(self):
        return hash((self.var_name, self.type_name))

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.var_name == other.var_name and self.type_name == other.type_name

    def __repr__(self) -> str:
        return f'MethodData: ("{self.var_name}","{self.type_name}, {self.predicates_name_list}")'


class GoalTreeNode:
    def __init__(self, name: str, children: list[str], isTask: bool) -> None:
        self.name: str = name
        self.children: list[str] = children
        self.isTask: bool = isTask

    def __repr__(self) -> str:
        return f'GoalTreeNode: ("{self.name}","{self.children}, {self.isTask}")'


class GoalInfo:
    def __init__(self, node_id: str, node_name: str, context: str, group: bool, divisible: bool) -> None:
        self.node_id = node_id
        self.node_name = node_name
        self.context = context
        self.group = group
        self.divisible = divisible

    def __repr__(self) -> str:
        return f"GoalInfo: \nId:{self.node_id}\nNode Name:{self.node_name}\nContext:{self.context}\nGroup:{self.group}\nDivisible:{self.divisible}\n"


class AbstractTaskWithId:
    def __init__(self, id, name, methods):
        self.id = id
        self.name = name
        self.methods = methods
    
    def __repr__(self) -> str:
        return f'Abstract Task (AT): ("{self.id} {self.name}","{self.methods}")'



