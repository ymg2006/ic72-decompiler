from __future__ import annotations

from .ast_nodes import Case, Catch, DoWhile, GotoFallback, If, Label, RawPHP, Sequence, Statement, Switch, TryCatch, While, Node


def render_node(node: Node, indent: int = 0) -> str:
    pad = "    " * indent
    if isinstance(node, RawPHP):
        return "\n".join(pad + line if line else "" for line in node.lines)
    if isinstance(node, Statement):
        return pad + node.code
    if isinstance(node, Label):
        return pad + node.name + ":"
    if isinstance(node, GotoFallback):
        return pad + "goto " + node.label + ";"
    if isinstance(node, Sequence):
        return "\n".join(render_node(child, indent) for child in node.body)
    if isinstance(node, If):
        out = [pad + "if (" + node.condition + ") {"]
        out += [render_node(child, indent + 1) for child in node.then_body]
        if node.else_body:
            out.append(pad + "} else {")
            out += [render_node(child, indent + 1) for child in node.else_body]
        out.append(pad + "}")
        return "\n".join(out)
    if isinstance(node, While):
        out = [pad + "while (" + node.condition + ") {"]
        out += [render_node(child, indent + 1) for child in node.body]
        out.append(pad + "}")
        return "\n".join(out)
    if isinstance(node, DoWhile):
        out = [pad + "do {"]
        out += [render_node(child, indent + 1) for child in node.body]
        out.append(pad + "} while (" + node.condition + ");")
        return "\n".join(out)
    if isinstance(node, Switch):
        out = [pad + "switch (" + node.expr + ") {"]
        for case in node.cases:
            out.append(pad + ("    default:" if case.value is None else "    case " + case.value + ":"))
            out += [render_node(child, indent + 2) for child in case.body]
            out.append(pad + "        break;")
        out.append(pad + "}")
        return "\n".join(out)
    if isinstance(node, TryCatch):
        out = [pad + "try {"]
        out += [render_node(child, indent + 1) for child in node.try_body]
        out.append(pad + "}")
        for c in node.catches:
            out[-1] += " catch (" + c.class_name + " " + c.var_name + ") {"
            out += [render_node(child, indent + 1) for child in c.body]
            out.append(pad + "}")
        return "\n".join(out)
    raise TypeError(type(node).__name__)


def render(nodes: list[Node]) -> list[str]:
    text = "\n".join(render_node(n, 0) for n in nodes)
    return text.splitlines()
