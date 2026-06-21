from __future__ import annotations
from dataclasses import dataclass, field

class Node: pass

@dataclass
class Statement(Node):
    code: str

@dataclass
class Sequence(Node):
    body: list[Node] = field(default_factory=list)

@dataclass
class If(Node):
    condition: str
    then_body: list[Node]
    else_body: list[Node] = field(default_factory=list)

@dataclass
class While(Node):
    condition: str
    body: list[Node]

@dataclass
class DoWhile(Node):
    body: list[Node]
    condition: str

@dataclass
class Switch(Node):
    expr: str
    cases: list['Case']

@dataclass
class Case(Node):
    value: str | None
    body: list[Node]

@dataclass
class TryCatch(Node):
    try_body: list[Node]
    catches: list['Catch']

@dataclass
class Catch(Node):
    class_name: str
    var_name: str
    body: list[Node]

@dataclass
class Label(Node):
    name: str

@dataclass
class GotoFallback(Node):
    label: str

@dataclass
class RawPHP(Node):
    lines: list[str]
