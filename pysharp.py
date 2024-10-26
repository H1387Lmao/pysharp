import ply.lex as lex
import ply.yacc as yacc
import argparse
import os
import sys
import random
import math

# Argument parsing
argParser = argparse.ArgumentParser()
argParser.add_argument("-in", "--input", "--source", "-s", required=True, help="Input source file")
argParser.add_argument("--debug-mode", action="store_true", help="Enable debug mode")

args = argParser.parse_args()
debug_mode = args.debug_mode

# Check if the input file exists
if os.path.isfile(args.input):
    source_file = args.input
else:
    raise SyntaxError("File source does not exist!")

# Define tokens
tokens = [
    "INT", "IDENTIFIER", "PL", "SU", "MU", "DV", "LP", "RP", "EQ", "ISEQ", "OB", "CB", "COMMA", "STRING", "DQ"
]

keywords = {
    "if": "IF",
    "execute": "PYTHON",
    "for": "FOR",
    "else": "ELSE",
    "to": "TO",
    "include": "INCLUDE",
    "fn" : "FUNC",
    "return" : "RETURN",
}

tokens += keywords.values()

# Define regular expressions for tokens
t_PL = r'\+'
t_OB = r'\{'
t_CB = r'\}'
t_SU = r'-'
t_MU = r'\*'
t_DV = r'/'
t_LP = r'\('
t_RP = r'\)'
t_EQ = r'='
t_COMMA = r","
t_ISEQ = r'=='
t_DQ = r'"'

def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]  # Remove surrounding quotes
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_:0-9]*'
    if t.value in keywords:
        t.type = keywords[t.value]  # Correctly set the type if it is a keyword
    return t

def t_INT(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Ignoring spaces, tabs, and newlines
t_ignore = " \t"

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += 1

# Error handling for lexer
def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Build lexer
lexer = lex.lex()

# AST Node Definitions
class NumberNode:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"{self.value}"

class ConditionNode:
    def __init__(self, op, l, r):
        self.op = op
        self.l = l
        self.r = r
    def __repr__(self):
        return f"CONDITION: ({self.l} {self.op} {self.r})"

class ForLoopNode:
    def __init__(self, identifier, range_, statements):
        self.identifier = identifier
        self.range = range_
        self.statements = statements

    def __repr__(self):
        return f"FOR {self.identifier} to {self.range} {{ {self.statements} }}"

class IfStatementNode:
    def __init__(self, condition, statements, elsestatements):
        self.condition = condition
        self.statements = statements
        self.else_statements = elsestatements

    def __repr__(self):
        return f"IF {self.condition} {{ {self.statements} }}" if self.else_statements==None else f"IF {self.condition} {{ {self.statements} }} ELSE {{ {self.else_statements} }}"

class ExecuteNode:
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"PRINT {self.value}"

class IdentifierNode:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"{self.name}"

class IncludeNode:
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"INCLUDE: {self.name}"

class BinaryOp:
    def __init__(self, op, l, r):
        self.op = op
        self.l = l
        self.r = r
    def __repr__(self):
        return f"({self.l} {self.op} {self.r})"

class FunctionCallNode:
    def __init__(self, function_name, arguments=None):
        self.args = arguments
        self.name = function_name
    def __repr__(self):
        return f"CALL: {self.name}, {self.args}"

class ArgumentsNode:
    def __init__(self, arguments):
        self.args = arguments
    def __repr__(self):
        return "NEEDS: "+",".join(map(str, self.args))

class ReturnNode:
    def __init__(self, arguments=None):
        self.args = arguments
    def __repr__(self):
        if self.args:
            if isinstance(self.args, (list, dict, tuple)):
                return f"RETURN: "+",".join(self.args)
            return f"RETURN {self.args}"
        else:
            return "RETURN"

class AssignNode:
    def __init__(self, identifier, value):
        self.identifier = identifier
        self.value = value
    def __repr__(self):
        return f"{self.identifier} := {self.value}"

class FunctionNode:
    def __init__(self, name, arguments, statements):
        self.name = name
        self.args = arguments
        self.statements = statements
    def __repr__(self):
        return f"FUNCTION: {self.name} {self.args} ( {self.statements} )"

# Define precedence and associativity
precedence = (
    ('left', 'PL', 'SU'),
    ('left', 'MU', 'DV'),
)

# Grammar rules


def p_statements(p):
    '''
    statements : statements statement
               | statement
    '''
    if len(p) == 3:  # More than one statement
        p[0] = p[1]  # Carry forward the previous statements
        if not isinstance(p[0], list):
            p[0] = [p[0]]  # Make it a list if it's a single statement
        p[0].append(p[2])  # Append the current statement
    else:  # Only one statement
        p[0] = [p[1]]  # Start a new list of statements

def p_statement_return(p):
    '''
    statement : RETURN
              | RETURN expr
    '''

    if len(p) == 2:
        p[0] = ReturnNode()
    else:
        p[0] = ReturnNode(p[2])

def p_statement_arguments(p):
    '''
    arguments : LP identifier_list RP
    '''

    p[0] = ArgumentsNode(p[2])  # Create ArgumentsNode with the identifier list

def p_identifier_list(p):
    '''
    identifier_list : IDENTIFIER
                    | identifier_list COMMA IDENTIFIER
                    | expr
                    | INT
                    | STRING
                    | identifier_list COMMA INT
                    | identifier_list COMMA statement
                    | identifier_list COMMA expr
                    | identifier_list COMMA STRING
                    | statement
    '''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_statement_function(p):
    '''
    statement : FUNC IDENTIFIER arguments OB statements CB
    '''
    p[0] = FunctionNode(p[2], p[3], p[5])

def p_statement_include(p):
    '''
    statement : INCLUDE IDENTIFIER
    '''

    p[0] = IncludeNode(p[2])

def p_statement_if(p):
    '''
    statement : IF condition OB statements CB
              | IF condition OB statements CB ELSE OB statements CB
    '''
    if len(p) == 6:
        p[0] = IfStatementNode(p[2], p[4], None)
    elif len(p) == 10:
        p[0] = IfStatementNode(p[2], p[4], p[8])

def p_statement_for(p):
    '''
    statement : FOR IDENTIFIER TO expr OB statements CB
              | FOR IDENTIFIER TO statement OB statements CB
    '''
    p[0] = ForLoopNode(p[2], p[4], p[6])

def p_statement_functioncall(p):
    '''
    statement : IDENTIFIER arguments
              | IDENTIFIER LP RP
    '''
    if len(p)==4:
        p[0] = FunctionCallNode(p[1])
    else:
        p[0] = FunctionCallNode(p[1], p[2])

def p_statement_python(p):
    '''
    statement : PYTHON LP STRING RP
    '''
    p[0] = ExecuteNode(p[3])

def p_statement_assign(p):
    '''
    statement : IDENTIFIER EQ expr
              | IDENTIFIER EQ statement
    '''
    p[0] = AssignNode(IdentifierNode(p[1]), p[3])

def p_condition(p):
    '''
    condition : expr ISEQ expr
    '''
    p[0] = ConditionNode(p[2], p[1], p[3])

def p_expr(p):
    '''
    expr : expr PL expr
         | expr SU expr
         | expr MU expr
         | expr DV expr
         | LP expr RP
         | INT
         | IDENTIFIER
         | STRING
    '''
    if len(p) == 2:
        if isinstance(p[1], int):
            p[0] = NumberNode(p[1])
        else:
            p[0] = IdentifierNode(p[1])
    elif len(p) == 4:
        if p[1] == "(":
            p[0] = p[2]
        else:
            p[0] = BinaryOp(p[2], p[1], p[3])

# Error rule for parser
def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error at EOF")

Variables = {
    "GLOBALS": {
        
    }
}
initiated_functions = {

}

call_stack = []

def execute(nodes):
    for node in nodes:
        execute_single_statement(node, variables=Variables["GLOBALS"])

def execute_single_statement(node, variables):
    if isinstance(node, BinaryOp):
        left = execute_single_statement(node.l, variables)
        right = execute_single_statement(node.r, variables)
        op = node.op
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            if right == 0:
                raise ZeroDivisionError("Division by zero")
            return left / right
    elif isinstance(node, FunctionNode):
        function_name = node.name

        Variables[function_name] = {
            
        }
        initiated_functions[function_name] = (node.args, node.statements)
    elif isinstance(node, FunctionCallNode):
        args_input = node.args
        funct_name = node.name

        if funct_name in initiated_functions:
            arguments, statements = initiated_functions[funct_name]
            if len(arguments.args) == len(args_input.args):
                localvariables = Variables[funct_name]
                for arg, argument in zip(args_input.args, arguments.args):
                    if isinstance(arg, FunctionCallNode):
                        localvariables[str(argument)] = execute_single_statement(arg, variables)
                    else:
                        if arg in variables:
                            localvariables[str(argument)] = variables[str(arg)]
                        else:
                            localvariables[str(argument)] = arg
                if debug_mode:
                    print(f"RUNNING {funct_name}, {Variables}")
                call_stack.append(funct_name)
                for statement in statements:
                    execute_single_statement(statement, localvariables)
        return Variables["GLOBALS"].get(f"{funct_name} Return", None)
    elif isinstance(node, IncludeNode):
        source = source_file

        source.removesuffix(".pysharp")
        if node.name == source:
            raise RuntimeError("Cannot include a module with the same name!")
        else:
            run(node.name+".pysharp")
    elif isinstance(node, AssignNode):
        identifier = node.identifier.name
        value = execute_single_statement(node.value, variables)
        variables[identifier] = value
        return value
    elif isinstance(node, ReturnNode):
        args = node.args
        func_parent = call_stack[-1]
        Variables["GLOBALS"][f"{func_parent} Return"] = execute_single_statement(args, variables)
    elif isinstance(node, ConditionNode):
        left = execute_single_statement(node.l, variables)
        right = execute_single_statement(node.r, variables)
        op = node.op
        return left == right
    elif isinstance(node, IfStatementNode):
        if execute_single_statement(node.condition, variables):
            for statement in node.statements:
                execute_single_statement(statement, variables)
        else:
            if node.else_statements:
                for statement in node.else_statements:
                    execute_single_statement(statement, variables)
    elif isinstance(node, ForLoopNode):
        identifier = node.identifier
        range_ = execute_single_statement(node.range, variables)
        statements = node.statements
        
        for identifier_count in range(1, range_ + 1):
            variables[identifier] = identifier_count
            for statement in statements:
                execute_single_statement(statement, variables)
    elif isinstance(node, ExecuteNode):
        if call_stack:
            func_name = call_stack[-1]
        else:
            func_name = "Execute"
        STRING = node.value
        for char in STRING:
            if char in "\t\n":
                raise RuntimeError("Cannot execute any malicious code")
        for keyword in ["import", "while", "lambda", "def", "locals()", "globals()"]:
            if keyword in STRING:
                raise RuntimeError("Cannot execute any malicious code")

        if call_stack:
            for key, value in Variables[func_name].items():
                if isinstance(value, str):
                    value = f'"{value}"'
                STRING = STRING.replace(key, str(value))


        try:
            eval_result = eval(STRING)
        except Exception as eval_error:
            try:
                exec("execute_input_value = " + STRING)
                eval_result = locals().get("execute_input_value")
            except Exception as exec_error:
                print("Execution error:", exec_error)
                eval_result = None

        Variables["GLOBALS"][f"{func_name} Return"] = eval_result
        return eval_result
    elif isinstance(node, IdentifierNode):
        value = node.name
        if value in variables:
            return variables[value]
        else:
            raise NameError(f"'{value}' is not defined")
    elif isinstance(node, NumberNode):
        return node.value

def run(fp=source_file):
    # Read the source file
    with open(fp, "r") as f:
        code = f.read()

    # Build parser
    parser = yacc.yacc()

    if debug_mode:
        lexer.input(code)
        for token in lexer:
            print(token)

    # Parse code and print AST
    ast = parser.parse(code, lexer=lexer)
    if debug_mode:
        print("AST:")
        print(ast)
    execute(ast)

run()
