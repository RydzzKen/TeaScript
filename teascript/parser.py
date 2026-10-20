"""Tahap 2: Parser mengubah token menjadi AST (recursive descent)."""

from .token import (
    Token, NUMBER, STRING, INTERP, IDENT, KEYWORD, OP, PUNCT, EOF,
    COMPOUND_OPS,
)
from .errors import SyntaxErrorTea
from . import ast_nodes as ast
from .lexer import Lexer


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # --- Helper ---
    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def check(self, type_, value=None):
        tok = self.current()
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def match(self, type_, value=None):
        if self.check(type_, value):
            return self.advance()
        return None

    def expect(self, type_, value=None, msg=None):
        tok = self.current()
        if not self.check(type_, value):
            expected = value if value is not None else type_
            found = "akhir file" if tok.type == EOF else repr(tok.value)
            raise SyntaxErrorTea(
                msg or f"diharapkan {expected!r} tetapi ditemukan {found}",
                tok.line, tok.column,
            )
        return self.advance()

    # --- Entry ---
    def parse(self):
        program = ast.Program(statements=[], line=1)
        while not self.check(EOF):
            program.statements.append(self.statement())
        return program

    # --- Statements ---
    def statement(self):
        tok = self.current()

        if self.match(KEYWORD, "let"):
            return self.let_stmt(tok)
        if self.match(KEYWORD, "if"):
            return self.if_stmt(tok)
        if self.match(KEYWORD, "while"):
            return self.while_stmt(tok)
        if self.match(KEYWORD, "for"):
            return self.for_stmt(tok)
        if self.match(KEYWORD, "fn"):
            return self.fn_stmt(tok)
        if self.match(KEYWORD, "return"):
            return self.return_stmt(tok)
        if self.match(KEYWORD, "break"):
            return ast.Break(line=tok.line)
        if self.match(KEYWORD, "continue"):
            return ast.Continue(line=tok.line)
        if self.match(KEYWORD, "import"):
            return self.import_stmt(tok)
        if self.match(KEYWORD, "from"):
            return self.from_import_stmt(tok)

        # Assignment atau ekspresi
        return self.expr_or_assign()

    def let_stmt(self, tok):
        name_tok = self.expect(IDENT, msg="diharapkan nama variabel setelah 'let'")
        self.expect(OP, "=", msg="diharapkan '=' setelah nama variabel")
        value = self.expression()
        return ast.Let(name=name_tok.value, value=value, line=tok.line)

    def if_stmt(self, tok):
        condition = self.expression()
        self.expect(PUNCT, "{", msg="diharapkan '{' setelah kondisi if")
        then_body = self.block()
        else_body = []
        if self.match(KEYWORD, "else"):
            if self.match(KEYWORD, "if"):
                # else if -> nested If
                inner = self.if_stmt(self.tokens[self.pos - 1])
                else_body = [inner]
            else:
                self.expect(PUNCT, "{", msg="diharapkan '{' setelah else")
                else_body = self.block()
        return ast.If(condition=condition, then_body=then_body,
                      else_body=else_body, line=tok.line)

    def while_stmt(self, tok):
        condition = self.expression()
        self.expect(PUNCT, "{", msg="diharapkan '{' setelah kondisi while")
        body = self.block()
        return ast.While(condition=condition, body=body, line=tok.line)

    def for_stmt(self, tok):
        name_tok = self.expect(IDENT, msg="diharapkan nama variabel setelah 'for'")
        self.expect(KEYWORD, "in", msg="diharapkan 'in' setelah nama variabel")
        iterable = self.expression()
        self.expect(PUNCT, "{", msg="diharapkan '{' setelah ekspresi for")
        body = self.block()
        return ast.ForIn(name=name_tok.value, iterable=iterable,
                         body=body, line=tok.line)

    def fn_stmt(self, tok):
        name_tok = self.expect(IDENT, msg="diharapkan nama fungsi setelah 'fn'")
        self.expect(PUNCT, "(", msg="diharapkan '(' setelah nama fungsi")
        params = []
        if not self.check(PUNCT, ")"):
            params.append(self.param_name())
            while self.match(PUNCT, ","):
                params.append(self.param_name())
        self.expect(PUNCT, ")", msg="diharapkan ')' setelah parameter")
        self.expect(PUNCT, "{", msg="diharapkan '{' untuk badan fungsi")
        body = self.block()
        return ast.FnDef(name=name_tok.value, params=params,
                         body=body, line=tok.line)

    def param_name(self):
        """Nama parameter. Keyword juga boleh (agar cocok dengan API Python,
        mis. `fn f(as_text)`), tapi bukan keyword yang punya arti operator."""
        tok = self.current()
        if tok.type == IDENT:
            return self.advance().value
        if tok.type == KEYWORD and tok.value not in ("true", "false", "nil",
                                                     "and", "or", "not",
                                                     "in", "if", "else"):
            return self.advance().value
        raise SyntaxErrorTea("diharapkan nama parameter",
                             tok.line, tok.column)

    def argument(self):
        """Satu argumen pemanggilan. `let _nama = nilai` diterjemahkan jadi
        keyword argument Python (mis. get_data(let _as_text = true))."""
        if self.check(KEYWORD, "let"):
            let_tok = self.advance()
            name_tok = self.expect(IDENT,
                                   msg="diharapkan nama setelah 'let' di argumen")
            if not name_tok.value.startswith("_"):
                raise SyntaxErrorTea(
                    "di dalam argumen, 'let' hanya untuk keyword argument "
                    "(nama harus diawali '_', mis. let _as_text = true)",
                    let_tok.line, let_tok.column)
            self.expect(OP, "=", msg="diharapkan '=' setelah nama keyword argument")
            value = self.expression()
            return ast.KwArg(name=name_tok.value[1:], value=value,
                             line=let_tok.line)
        return self.expression()

    def return_stmt(self, tok):
        # return boleh tanpa nilai
        if self.check(PUNCT, "}") or self.check(EOF):
            value = ast.Nil(line=tok.line)
        else:
            value = self.expression()
        return ast.Return(value=value, line=tok.line)

    def import_stmt(self, tok):
        # import "path/ke/file.tea" → nama binding dari nama file
        if self.check(STRING):
            path_tok = self.advance()
            path = path_tok.value
            stem = path.replace("\\", "/").rsplit("/", 1)[-1]
            stem = stem.rsplit(".", 1)[0] if "." in stem else stem
            return ast.Import(name=stem, path=path, line=tok.line)
        name_tok = self.expect(IDENT, msg="diharapkan nama modul setelah 'import'")
        return ast.Import(name=name_tok.value, path=None, line=tok.line)

    def from_import_stmt(self, tok):
        module_tok = self.expect(IDENT, msg="diharapkan nama modul setelah 'from'")
        self.expect(KEYWORD, "import", msg="diharapkan 'import' setelah nama modul")
        names = [self.expect(IDENT, msg="diharapkan nama yang diimpor").value]
        while self.match(PUNCT, ","):
            names.append(self.expect(IDENT, msg="diharapkan nama yang diimpor").value)
        return ast.FromImport(module=module_tok.value, names=names, line=tok.line)

    def block(self):
        stmts = []
        while not self.check(PUNCT, "}") and not self.check(EOF):
            stmts.append(self.statement())
        self.expect(PUNCT, "}", msg="diharapkan '}' untuk menutup blok")
        return stmts

    def expr_or_assign(self):
        tok = self.current()
        expr = self.expression()

        # Assignment: Ident = expr  atau  Index = expr
        if self.check(OP, "="):
            self.advance()
            value = self.expression()
            if isinstance(expr, ast.Ident):
                return ast.Assign(name=expr.name, value=value, line=tok.line)
            if isinstance(expr, ast.Index):
                return ast.IndexAssign(target=expr.target, index=expr.index,
                                       value=value, line=tok.line)
            raise SyntaxErrorTea("target assignment tidak valid",
                                 tok.line, tok.column)

        # Assignment gabungan: x += 1, xs[0] *= 2, dst.
        if self.check(OP) and self.current().value in COMPOUND_OPS:
            op_tok = self.advance()
            value = self.expression()
            base_op = op_tok.value[0]  # "+=" -> "+"
            if isinstance(expr, ast.Ident):
                combined = ast.Binary(
                    op=base_op,
                    left=ast.Ident(name=expr.name, line=expr.line),
                    right=value, line=op_tok.line)
                return ast.Assign(name=expr.name, value=combined, line=tok.line)
            if isinstance(expr, ast.Index):
                combined = ast.Binary(op=base_op, left=expr, right=value,
                                      line=op_tok.line)
                return ast.IndexAssign(target=expr.target, index=expr.index,
                                       value=combined, line=tok.line)
            raise SyntaxErrorTea("target assignment tidak valid",
                                 tok.line, tok.column)

        return ast.ExprStmt(expr=expr, line=tok.line)

    # --- Expressions (precedence climbing) ---
    def expression(self):
        return self.ternary()

    def ternary(self):
        condition = self.logical_or()
        if self.match(OP, "?"):
            then = self.expression()
            self.expect(PUNCT, ":", msg="diharapkan ':' dalam ternary")
            otherwise = self.ternary()  # asosiatif kanan: a ? b : c ? d : e
            return ast.Ternary(condition=condition, then=then,
                               otherwise=otherwise, line=condition.line)
        return condition

    def logical_or(self):
        left = self.logical_and()
        while self.match(KEYWORD, "or"):
            op_tok = self.tokens[self.pos - 1]
            right = self.logical_and()
            left = ast.Binary(op="or", left=left, right=right, line=op_tok.line)
        return left

    def logical_and(self):
        left = self.logical_not()
        while self.match(KEYWORD, "and"):
            op_tok = self.tokens[self.pos - 1]
            right = self.logical_not()
            left = ast.Binary(op="and", left=left, right=right, line=op_tok.line)
        return left

    def logical_not(self):
        if self.match(KEYWORD, "not"):
            op_tok = self.tokens[self.pos - 1]
            operand = self.logical_not()
            return ast.Unary(op="not", operand=operand, line=op_tok.line)
        return self.comparison()

    def comparison(self):
        left = self.term()
        while True:
            if self.check(OP) and self.current().value in ("==", "!=", "<", ">", "<=", ">="):
                op_tok = self.advance()
                right = self.term()
                left = ast.Binary(op=op_tok.value, left=left, right=right,
                                  line=op_tok.line)
            elif self.check(KEYWORD, "in"):
                # Python/JS: x in container
                op_tok = self.advance()
                right = self.term()
                left = ast.Binary(op="in", left=left, right=right,
                                  line=op_tok.line)
            elif self.check(KEYWORD, "not") and self.peek().type == KEYWORD \
                    and self.peek().value == "in":
                # Python: x not in container
                op_tok = self.advance()
                self.advance()  # konsumsi 'in'
                right = self.term()
                left = ast.Binary(op="not in", left=left, right=right,
                                  line=op_tok.line)
            else:
                break
        return left

    def term(self):
        left = self.factor()
        while self.check(OP) and self.current().value in ("+", "-"):
            op_tok = self.advance()
            right = self.factor()
            left = ast.Binary(op=op_tok.value, left=left, right=right,
                              line=op_tok.line)
        return left

    def factor(self):
        left = self.unary()
        while self.check(OP) and self.current().value in ("*", "/", "%"):
            op_tok = self.advance()
            right = self.unary()
            left = ast.Binary(op=op_tok.value, left=left, right=right,
                              line=op_tok.line)
        return left

    def unary(self):
        if self.check(OP, "-"):
            op_tok = self.advance()
            operand = self.unary()
            return ast.Unary(op="-", operand=operand, line=op_tok.line)
        return self.postfix()

    def postfix(self):
        expr = self.primary()
        while True:
            if self.match(PUNCT, "("):
                args = []
                if not self.check(PUNCT, ")"):
                    args.append(self.argument())
                    while self.match(PUNCT, ","):
                        args.append(self.argument())
                self.expect(PUNCT, ")", msg="diharapkan ')' setelah argumen")
                expr = ast.Call(callee=expr, args=args, line=expr.line)
            elif self.match(PUNCT, "["):
                expr = self.index_or_slice(expr)
            elif self.match(PUNCT, "."):
                # Dot access: modul.nama, objek_python.atribut, dict.key
                name_tok = self.expect(IDENT,
                                       msg="diharapkan nama setelah '.'")
                expr = ast.Index(
                    target=expr,
                    index=ast.String(value=name_tok.value, line=name_tok.line),
                    line=expr.line)
            else:
                break
        return expr

    def index_or_slice(self, target):
        # Slice tanpa batas awal: arr[:2]
        if self.match(PUNCT, ":"):
            end = None if self.check(PUNCT, "]") else self.expression()
            self.expect(PUNCT, "]", msg="diharapkan ']' setelah slice")
            return ast.Slice(target=target, start=None, end=end,
                             line=target.line)
        first = self.expression()
        # Slice: arr[1:3], arr[1:], arr[a+1:b]
        if self.match(PUNCT, ":"):
            end = None if self.check(PUNCT, "]") else self.expression()
            self.expect(PUNCT, "]", msg="diharapkan ']' setelah slice")
            return ast.Slice(target=target, start=first, end=end,
                             line=target.line)
        # Index biasa: arr[0]
        self.expect(PUNCT, "]", msg="diharapkan ']' setelah indeks")
        return ast.Index(target=target, index=first, line=target.line)

    def primary(self):
        tok = self.current()

        if self.match(NUMBER):
            return ast.Number(value=tok.value, line=tok.line)
        if self.match(STRING):
            return ast.String(value=tok.value, line=tok.line)
        if self.match(INTERP):
            return self.interp_expr(tok)
        if self.match(KEYWORD, "true"):
            return ast.Bool(value=True, line=tok.line)
        if self.match(KEYWORD, "false"):
            return ast.Bool(value=False, line=tok.line)
        if self.match(KEYWORD, "nil"):
            return ast.Nil(line=tok.line)
        if self.match(IDENT):
            return ast.Ident(name=tok.value, line=tok.line)
        if self.match(PUNCT, "("):
            expr = self.expression()
            self.expect(PUNCT, ")", msg="diharapkan ')' untuk menutup ekspresi")
            return expr
        if self.match(PUNCT, "["):
            return self.list_literal(tok)
        if self.match(PUNCT, "{"):
            return self.dict_literal(tok)

        if tok.type == EOF:
            raise SyntaxErrorTea("ekspresi tidak lengkap (menemukan akhir file)",
                                 tok.line, tok.column)
        raise SyntaxErrorTea(
            f"token tidak terduga: {tok.value!r}",
            tok.line, tok.column,
        )

    def list_literal(self, tok):
        elements = []
        if not self.check(PUNCT, "]"):
            elements.append(self.expression())
            while self.match(PUNCT, ","):
                elements.append(self.expression())
        self.expect(PUNCT, "]", msg="diharapkan ']' untuk menutup list")
        return ast.ListLit(elements=elements, line=tok.line)

    def dict_literal(self, tok):
        pairs = []
        if not self.check(PUNCT, "}"):
            pairs.append(self.dict_pair())
            while self.match(PUNCT, ","):
                pairs.append(self.dict_pair())
        self.expect(PUNCT, "}", msg="diharapkan '}' untuk menutup dictionary")
        return ast.DictLit(pairs=pairs, line=tok.line)

    def dict_pair(self):
        # key boleh identifier atau string
        tok = self.current()
        if self.match(IDENT):
            key = ast.String(value=tok.value, line=tok.line)
        elif self.match(STRING):
            key = ast.String(value=tok.value, line=tok.line)
        else:
            raise SyntaxErrorTea("diharapkan nama key di dictionary",
                                 tok.line, tok.column)
        self.expect(PUNCT, ":", msg="diharapkan ':' setelah key")
        value = self.expression()
        return (key, value)

    def interp_expr(self, tok):
        """Parse string interpolasi "${expr}".

        Bagian ekspresi di-parse ulang dengan lexer/parser baru,
        dengan offset baris/kolom agar posisi error tetap akurat.
        """
        parts = []
        for part in tok.value:
            if part[0] == "text":
                parts.append(part[1])
                continue
            _, src, line, col = part
            sub_tokens = Lexer(src, line_offset=line - 1,
                               column_offset=col - 1).tokenize()
            sub_program = Parser(sub_tokens).parse()
            if len(sub_program.statements) != 1 or \
                    not isinstance(sub_program.statements[0], ast.ExprStmt):
                raise SyntaxErrorTea(
                    "hanya ekspresi yang boleh di dalam ${}",
                    line, col,
                )
            parts.append(sub_program.statements[0].expr)
        return ast.Interp(parts=parts, line=tok.line)