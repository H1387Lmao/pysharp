import os
import sys
import argparse

TT_INT     = "INT"
TT_STRING  = "STRING"
TT_IDENTIF = "IDENTIFIER"
TT_PLUS    = "PLUS"
TT_MINUS   = "MINUS"
TT_MUL     = "MUL"
TT_DIV     = "DIV"
TT_LPAREN  = "LPAREN"
TT_RPAREN  = "RPAREN"

TT_EQUALS  = "EQUALS"

TT_EOF     = "EOF"

class Position:
    def __init__(self, lineno, position, text, tokens=[]):
        self.tokens = tokens
        self.text = text
        self.position = position
        self.lineno = lineno

    def advance(self):
        if self.position+1 < len(self.text):
            self.position = self.position+1 
            return
        self.position = None

    def char(self):
        char = self.text[self.position] if self.position!=None else self.position
        return char

    def token(self):
        token = self.tokens[self.position] if self.position!=None else self.position

        return token

def display_error(error):
    print("\n"+"\n".join(error))

def point(msg, line, startpos, endpos):
    if isinstance(startpos, Position):
        startpos = startpos.position
        endpos   = endpos.position
    point_with_arrow = line + "\n"

    for idx, char in enumerate(line):
        if idx >= startpos and idx <= endpos:
            point_with_arrow += "~"
        else:
            if char == "\t":
               point_with_arrow += " "*7
            point_with_arrow += " "
    return (msg, point_with_arrow)

class Token:
    def __init__(self, type, value=None, lineno=0):
        self.type = type
        self.value = value
        self.lineno = lineno

    def __repr__(self):
        return f"{self.type}:{self.value}" if self.value else self.type

class Lexer:
    def __init__(self, code):
        self.code = code 
        self.position = Position(1, -1, code)
        self.symbols = "+-/*()="

        self.alphanumerals = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        self.alphanumerals += self.alphanumerals.lower() + "0123456789"

    def tokenize(self):
        self.tokens = []
        self.current_token = ""
        self.current_line = ""
        self.pos_rel_to_line = -1

        while self.position.char():
            self.position.advance()
            char = self.position.char()
            if char == None:
                break 
            self.current_line += char
            self.pos_rel_to_line += 1
            if char in " \t":
                continue
            if char == "\n":
                self.position.lineno+=1
                self.current_line = ""
                self.pos_rel_to_line = -1
                continue

            if char in self.symbols:
                if self.current_token:
                    self.tokens.append(Token(self.get_type(), self.current_token, self.position.lineno))
                    self.current_token = ""

                if char == "+":
                    self.tokens.append(Token(TT_PLUS, char, self.position.lineno))
                elif char == "-":
                    self.tokens.append(Token(TT_MINUS, char, self.position.lineno))
                elif char == "*":
                    self.tokens.append(Token(TT_MUL, char, self.position.lineno))
                elif char == "/":
                    self.tokens.append(Token(TT_DIV, char, self.position.lineno))
                elif char == "(":
                    self.tokens.append(Token(TT_LPAREN, char, self.position.lineno))
                elif char == ")":
                    self.tokens.append(Token(TT_RPAREN, char, self.position.lineno))
                elif char == "=":
                    self.tokens.append(Token(TT_EQUALS, char, self.position.lineno))
            elif char in self.alphanumerals:
                self.current_token += char
            else:
                return None, point(f"Invalid Character: '{char}', At line: {self.position.lineno}", self.current_line,self.pos_rel_to_line, self.pos_rel_to_line)

        if self.current_token:
            self.tokens.append(Token(self.get_type(), self.current_token, self.position.lineno))

        self.tokens.append(Token(TT_EOF, "EOF", self.position.lineno))
        
        return self.tokens, None

    def get_type(self):
        if self.current_token.isdigit():
            return TT_INT
        elif self.current_token[0] and self.current_token[-1] == "\"":
            return TT_STRING
        else:
            return TT_IDENTIF

class ValueNode:
    def __init__(self, tk, nodetype="Value", operation=None):
        self.tk = tk
        self.value=tk
        self.op = operation
        self.nodetype = nodetype
    def __repr__(self):
        return f"{self.nodetype}:{self.tk.value}"

class BinOp:
    def __init__(self, operation, left, right):
        self.op = operation
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class Parser:
    def __init__(self, tokens, code):
        self.position = Position(0, -1, code, tokens)
        self.current_token = None
        self.advance()  # Initialize first token
        self.code=code

    def advance(self):
        """Advances position and updates current token."""
        self.position.advance()
        self.current_token = self.position.token()

    def parse(self):
        result, error = self.expr()
        return result, error

    def error(self, message):
        line = self.code.split("\n")[self.position.lineno - 1] + "      "

        startpos = self.position.position
        endpos = startpos + 6

        error_message, arrow = point(message, line, startpos, endpos)
        return None, [error_message, arrow]

    def factor(self):
        """Handles literals, identifiers, unary operators, and parentheses."""
        token = self.current_token

        if token.type in (TT_PLUS, TT_MINUS):
            # Handle unary operations
            op_token = token
            self.advance()
            factor, error = self.factor()
            if error:
                return None, error
            return ValueNode(factor, "Unary", op_token), None
        
        elif token.type == TT_INT:
            self.advance()
            return ValueNode(token, "Int"), None
        elif token.type == TT_STRING:
            self.advance()
            return ValueNode(token, "String"), None
        elif token.type == TT_IDENTIF:
            self.advance()
            return ValueNode(token, "Indentifier"), None
        elif token.type == TT_LPAREN:
            # Handle expressions in parentheses
            self.advance()
            expr, error = self.expr()
            if error:
                return None, error

            if self.current_token.type != TT_RPAREN:
                return self.error(f"Expected ')' at line {token.lineno}")

            self.advance()  # Skip the closing parenthesis
            return expr, None
        else:
            return self.error(f"Expected value at line {token.lineno}")

    def term(self):
        """Handles multiplication and division."""
        left, error = self.factor()
        if error:
            return None, error

        while self.current_token.type in (TT_MUL, TT_DIV):
            op_token = self.current_token
            self.advance()

            right, error = self.factor()
            if error:
                return None, error

            left = BinOp(op_token, left, right)
        
        return left, None

    def expr(self):
        """Handles addition and subtraction, including parentheses."""
        left, error = self.term()
        if error:
            return None, error

        while self.current_token.type in (TT_PLUS, TT_MINUS):
            op_token = self.current_token
            self.advance()

            right, error = self.term()
            if error:
                return None, error

            left = BinOp(op_token, left, right)

        return left, None

# Testing the parser
code = "10 * (3 + 1)"
lexer = Lexer(code)

tokens, error = lexer.tokenize()
if error:
    display_error(error)
    sys.exit()

parser = Parser(tokens, code)
node, error = parser.parse()

if error:
    display_error(error)
    sys.exit()

execute_node(node)
