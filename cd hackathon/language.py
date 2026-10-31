
import re
from dataclasses import dataclass

# LEXICAL ANALYSIS

@dataclass
class Token:
    kind: str
    value: str
    pos: int


TOKEN_RE = re.compile(
    r"\s+|//[^\n]*|"
    r"(?P<number>\d+(?:\.\d+)?)|"
    r"(?P<string>\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')|"
    r"(?P<ident>[A-Za-z][A-Za-z0-9_]*)|"
    r"(?P<op>==|!=|<=|>=|[+\-*/%<>=!(){};,])"
)


def lex(source):
    tokens = []
    pos = 0

    while pos < len(source):
        match = TOKEN_RE.match(source, pos)

        if not match:
            raise SyntaxError(
                f"Unexpected character {source[pos]!r} at position {pos}"
            )

        raw = match.group(0)
        start = pos
        pos = match.end()

        if raw.isspace() or raw.startswith("//"):
            continue

        kind = match.lastgroup

        if kind == "number":
            tokens.append(Token("NUMBER", raw, start))

        elif kind == "string":
            tokens.append(Token("STRING", raw[1:-1], start))

        elif kind == "ident":
            upper = raw.upper()

            if upper in {
                "LET", "PRINT", "IF", "ELSE",
                "WHILE", "TRUE", "FALSE"
            }:
                tokens.append(Token(upper, raw, start))
            else:
                tokens.append(Token("IDENT", raw, start))

        else:
            tokens.append(Token(raw, raw, start))

    tokens.append(Token("EOF", "", len(source)))

    return tokens


# ABSTRACT SYNTAX TREE

@dataclass
class Node:
    kind: str
    value: object = None
    children: list = None


# PARSER

PRECEDENCE = {
    "==": 1,
    "!=": 1,
    "<": 1,
    "<=": 1,
    ">": 1,
    ">=": 1,
    "+": 2,
    "-": 2,
    "*": 3,
    "/": 3,
    "%": 3
}


class Parser:

    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0

    def current(self):
        return self.tokens[self.i]

    def take(self, kind=None):
        token = self.current()

        if kind and token.kind != kind:
            raise SyntaxError(
                f"Expected {kind}, got {token.kind} "
                f"at position {token.pos}"
            )

        self.i += 1
        return token

    def parse(self):
        statements = []

        while self.current().kind != "EOF":
            statements.append(self.statement())

        return Node("program", children=statements)

    def block(self):
        self.take("{")
        body = []

        while self.current().kind not in {"}", "EOF"}:
            body.append(self.statement())

        self.take("}")
        return body

    def statement(self):
        kind = self.current().kind

        if kind == "LET":
            self.take()
            name = self.take("IDENT").value
            self.take("=")
            expr = self.expression()
            self.take(";")

            return Node("let", name, [expr])

        if kind == "IDENT":
            name = self.take().value
            self.take("=")
            expr = self.expression()
            self.take(";")

            return Node("assign", name, [expr])

        if kind == "PRINT":
            self.take()
            expr = self.expression()
            self.take(";")

            return Node("print", children=[expr])

        if kind == "IF":
            self.take()
            self.take("(")
            condition = self.expression()
            self.take(")")

            yes = self.block()
            no = []

            if self.current().kind == "ELSE":
                self.take()
                no = self.block()

            return Node(
                "if",
                children=[
                    condition,
                    Node("block", children=yes),
                    Node("block", children=no)
                ]
            )

        if kind == "WHILE":
            self.take()
            self.take("(")
            condition = self.expression()
            self.take(")")

            body = self.block()

            return Node(
                "while",
                children=[
                    condition,
                    Node("block", children=body)
                ]
            )

        raise SyntaxError(
            f"Unexpected token {self.current().kind} "
            f"at position {self.current().pos}"
        )

    def expression(self, min_prec=0):
        left = self.primary()

        while (
            self.current().kind in PRECEDENCE
            and PRECEDENCE[self.current().kind] >= min_prec
        ):
            op = self.take().kind
            prec = PRECEDENCE[op]
            right = self.expression(prec + 1)

            left = Node("binary", op, [left, right])

        return left

    def primary(self):
        token = self.current()

        if token.kind == "NUMBER":
            self.take()

            value = (
                float(token.value)
                if "." in token.value
                else int(token.value)
            )

            return Node("literal", value)

        if token.kind == "STRING":
            self.take()
            return Node("literal", token.value)

        if token.kind in {"TRUE", "FALSE"}:
            self.take()
            return Node("literal", token.kind == "TRUE")

        if token.kind == "IDENT":
            self.take()
            return Node("variable", token.value)

        if token.kind == "-":
            self.take()
            return Node("unary", "-", [self.primary()])

        if token.kind == "!":
            self.take()
            return Node("unary", "!", [self.primary()])

        if token.kind == "(":
            self.take()
            value = self.expression()
            self.take(")")
            return value

        raise SyntaxError(
            f"Expected an expression at position {token.pos}"
        )


def parse(tokens):
    return Parser(tokens).parse()


# INTERPRETER

def interpret(ast):
    env = {}
    output = []

    def evaluate(node):

        if node.kind == "literal":
            return node.value

        if node.kind == "variable":
            if node.value not in env:
                raise NameError(
                    f"Variable '{node.value}' is not defined"
                )

            return env[node.value]

        if node.kind == "unary":
            value = evaluate(node.children[0])

            if node.value == "-":
                return -value

            return not value

        if node.kind == "binary":
            a = evaluate(node.children[0])
            b = evaluate(node.children[1])

            operations = {
                "+": lambda: a + b,
                "-": lambda: a - b,
                "*": lambda: a * b,
                "/": lambda: a / b,
                "%": lambda: a % b,
                "==": lambda: a == b,
                "!=": lambda: a != b,
                "<": lambda: a < b,
                "<=": lambda: a <= b,
                ">": lambda: a > b,
                ">=": lambda: a >= b
            }

            return operations[node.value]()

        raise RuntimeError("Unknown expression")

    def execute(statement):

        if statement.kind in {"let", "assign"}:
            env[statement.value] = evaluate(
                statement.children[0]
            )

        elif statement.kind == "print":
            output.append(
                str(evaluate(statement.children[0]))
            )

        elif statement.kind == "if":
            if evaluate(statement.children[0]):
                branch = statement.children[1]
            else:
                branch = statement.children[2]

            for item in branch.children:
                execute(item)

        elif statement.kind == "while":
            count = 0

            while evaluate(statement.children[0]):
                for item in statement.children[1].children:
                    execute(item)

                count += 1

                if count > 10000:
                    raise RuntimeError("Loop limit exceeded")

    for statement in ast.children:
        execute(statement)

    return output, env


# COMPILER: AST TO INTERMEDIATE BYTECODE

def compile_ast(ast):
    code = []

    def emit(op, arg=None):
        code.append([op, arg])

    def expression(node):

        if node.kind == "literal":
            emit("PUSH", node.value)

        elif node.kind == "variable":
            emit("LOAD", node.value)

        elif node.kind == "unary":
            expression(node.children[0])

            if node.value == "-":
                emit("NEG")
            else:
                emit("NOT")

        elif node.kind == "binary":
            expression(node.children[0])
            expression(node.children[1])
            emit("BINARY", node.value)

    def statements(items):

        for node in items:

            if node.kind in {"let", "assign"}:
                expression(node.children[0])
                emit("STORE", node.value)

            elif node.kind == "print":
                expression(node.children[0])
                emit("PRINT")

            elif node.kind == "if":
                expression(node.children[0])
                emit("JUMP_IF_FALSE", None)

                false_jump = len(code) - 1

                statements(node.children[1].children)

                if node.children[2].children:
                    emit("JUMP", None)
                    end_jump = len(code) - 1

                    code[false_jump][1] = len(code)

                    statements(node.children[2].children)

                    code[end_jump][1] = len(code)

                else:
                    code[false_jump][1] = len(code)

            elif node.kind == "while":
                start = len(code)

                expression(node.children[0])
                emit("JUMP_IF_FALSE", None)

                exit_jump = len(code) - 1

                statements(node.children[1].children)

                emit("JUMP", start)

                code[exit_jump][1] = len(code)

    statements(ast.children)

    emit("HALT")

    return code


# VIRTUAL MACHINE

def run_vm(code):
    stack = []
    env = {}
    output = []

    ip = 0
    steps = 0

    while ip < len(code):

        steps += 1

        if steps > 100000:
            raise RuntimeError("VM instruction limit exceeded")

        op, arg = code[ip]
        ip += 1

        if op == "PUSH":
            stack.append(arg)

        elif op == "LOAD":
            if arg not in env:
                raise NameError(
                    f"Variable '{arg}' is not defined"
                )

            stack.append(env[arg])

        elif op == "STORE":
            env[arg] = stack.pop()

        elif op == "NEG":
            stack.append(-stack.pop())

        elif op == "NOT":
            stack.append(not stack.pop())

        elif op == "BINARY":
            b = stack.pop()
            a = stack.pop()

            operations = {
                "+": lambda: a + b,
                "-": lambda: a - b,
                "*": lambda: a * b,
                "/": lambda: a / b,
                "%": lambda: a % b,
                "==": lambda: a == b,
                "!=": lambda: a != b,
                "<": lambda: a < b,
                "<=": lambda: a <= b,
                ">": lambda: a > b,
                ">=": lambda: a >= b
            }

            stack.append(operations[arg]())

        elif op == "PRINT":
            output.append(str(stack.pop()))

        elif op == "JUMP":
            ip = arg

        elif op == "JUMP_IF_FALSE":
            if not stack.pop():
                ip = arg

        elif op == "HALT":
            break

    return output, env, steps
