"""Tahap 3: Evaluator menjalankan AST."""

import os
import importlib

from . import ast_nodes as ast
from .errors import NameErrorTea, RuntimeErrorTea, TeaError
from .lexer import Lexer
from .parser import Parser


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.values = {}

    def get(self, name, line):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name, line)
        raise NameErrorTea(f"variabel '{name}' belum dideklarasikan", line)

    def set(self, name, value, line):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value, line)
            return
        raise NameErrorTea(
            f"variabel '{name}' belum dideklarasikan "
            f"(pakai 'let {name} = ...' dulu)", line)

    def declare(self, name, value):
        self.values[name] = value


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception):
    def __init__(self, line=None):
        self.line = line


class ContinueSignal(Exception):
    def __init__(self, line=None):
        self.line = line


class Function:
    def __init__(self, name, params, body, closure, evaluator=None):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.evaluator = evaluator
        # Flask (dan framework Python lain) memakai __name__ untuk nama route
        self.__name__ = name
        self.__doc__ = None

    def __call__(self, *args, **kwargs):
        """Bisa dipanggil dari Python (mis. Flask memanggil handler route)."""
        if self.evaluator is None:
            raise RuntimeErrorTea(
                f"fungsi '{self.name}' tidak bisa dipanggil dari Python")
        return self.evaluator.invoke(self, list(args) + list(kwargs.values()),
                                     None)


class Evaluator:
    def __init__(self, input_fn=None):
        self.globals = Environment()
        # Sistem modul: cache per file, stack untuk deteksi melingkar
        self.module_cache = {}    # path absolut -> dict ekspor
        self.module_stack = []    # path yang sedang dieksekusi
        self.base_dir = os.getcwd()  # direktori file yang sedang berjalan
        self.input_fn = input_fn  # pengganti input() (untuk web/REPL)
        self._install_builtins()
        self._install_web()

    # --- Builtins ---
    def _install_builtins(self):
        def tea_print(*args, **kwargs):
            end = kwargs.pop("end", "\n")
            flush = kwargs.pop("flush", False)
            sep = kwargs.pop("sep", " ")
            if kwargs:
                nama = ", ".join(kwargs)
                raise RuntimeErrorTea(
                    f"print(): argumen tidak dikenal: {nama} "
                    f"(yang didukung: end, flush, sep)")
            if not isinstance(end, str) or not isinstance(sep, str):
                raise RuntimeErrorTea("print(): 'end' dan 'sep' harus string")
            print(*[self.to_string(a) for a in args], end=end, sep=sep,
                  flush=bool(flush))
            return None

        def tea_len(x):
            if isinstance(x, (list, str, dict)):
                return len(x)
            raise RuntimeErrorTea(f"len() tidak mendukung tipe {type(x).__name__}")

        def tea_input(prompt=""):
            try:
                if self.input_fn is not None:
                    return self.input_fn(prompt)
                return input(prompt)
            except EOFError:
                return ""

        def tea_str(x):
            return self.to_string(x)

        def tea_num(x):
            if isinstance(x, bool):
                return 1 if x else 0
            if isinstance(x, (int, float)):
                return x
            if isinstance(x, str):
                try:
                    return int(x)
                except ValueError:
                    try:
                        return float(x)
                    except ValueError:
                        raise RuntimeErrorTea(f"num(): '{x}' bukan angka")
            raise RuntimeErrorTea(f"num(): tidak bisa mengubah {type(x).__name__}")

        def tea_push(lst, *values):
            if not isinstance(lst, list):
                raise RuntimeErrorTea(
                    f"push() membutuhkan list, diberi {self.type_name(lst)}")
            lst.extend(values)
            return lst

        def tea_pop(lst):
            if not isinstance(lst, list):
                raise RuntimeErrorTea(
                    f"pop() membutuhkan list, diberi {self.type_name(lst)}")
            if not lst:
                raise RuntimeErrorTea("pop(): list kosong")
            return lst.pop()

        def tea_keys(d):
            if not isinstance(d, dict):
                raise RuntimeErrorTea(
                    f"keys() membutuhkan dictionary, diberi {self.type_name(d)}")
            return list(d.keys())

        def tea_values(d):
            if not isinstance(d, dict):
                raise RuntimeErrorTea(
                    f"values() membutuhkan dictionary, diberi {self.type_name(d)}")
            return list(d.values())

        def tea_range(*args):
            if len(args) not in (1, 2, 3):
                raise RuntimeErrorTea("range() butuh 1 sampai 3 argumen")
            for v in args:
                if not isinstance(v, int) or isinstance(v, bool):
                    raise RuntimeErrorTea("range() membutuhkan angka bulat")
            if len(args) == 1:
                start, end, step = 0, args[0], 1
            elif len(args) == 2:
                start, end, step = args[0], args[1], 1
            else:
                start, end, step = args
            if step == 0:
                raise RuntimeErrorTea("range(): step tidak boleh 0")
            return list(range(start, end, step))

        def tea_type(x):
            return self.type_name(x)

        def tea_includes(container, item):
            return self.contains(item, container)

        def tea_upper(s):
            if not isinstance(s, str):
                raise RuntimeErrorTea(
                    f"upper() membutuhkan string, diberi {self.type_name(s)}")
            return s.upper()

        def tea_lower(s):
            if not isinstance(s, str):
                raise RuntimeErrorTea(
                    f"lower() membutuhkan string, diberi {self.type_name(s)}")
            return s.lower()

        def tea_trim(s):
            if not isinstance(s, str):
                raise RuntimeErrorTea(
                    f"trim() membutuhkan string, diberi {self.type_name(s)}")
            return s.strip()

        def tea_split(s, sep):
            if not isinstance(s, str):
                raise RuntimeErrorTea(
                    f"split() membutuhkan string, diberi {self.type_name(s)}")
            if not isinstance(sep, str):
                raise RuntimeErrorTea(
                    f"split(): pemisah harus string, diberi {self.type_name(sep)}")
            if sep == "":
                return list(s)
            return s.split(sep)

        def tea_join(lst, sep):
            if not isinstance(lst, list):
                raise RuntimeErrorTea(
                    f"join() membutuhkan list, diberi {self.type_name(lst)}")
            if not isinstance(sep, str):
                raise RuntimeErrorTea(
                    f"join(): pemisah harus string, diberi {self.type_name(sep)}")
            return sep.join(self.to_string(v) for v in lst)

        def tea_abs(x):
            if isinstance(x, bool) or not isinstance(x, (int, float)):
                raise RuntimeErrorTea(
                    f"abs() membutuhkan angka, diberi {self.type_name(x)}")
            return abs(x)

        def tea_min_max(func, name, args):
            if len(args) == 1 and isinstance(args[0], list):
                values = args[0]
            else:
                values = list(args)
            if not values:
                raise RuntimeErrorTea(f"{name}() butuh minimal satu nilai")
            for v in values:
                if isinstance(v, bool) or not isinstance(v, (int, float)):
                    raise RuntimeErrorTea(f"{name}() membutuhkan angka")
            return func(values)

        def tea_min(*args):
            return tea_min_max(min, "min", args)

        def tea_max(*args):
            return tea_min_max(max, "max", args)

        def tea_pyimport(name):
            """Impor modul Python: let m = pyimport("math")"""
            if not isinstance(name, str):
                raise RuntimeErrorTea(
                    f"pyimport() membutuhkan string, diberi {self.type_name(name)}")
            try:
                return importlib.import_module(name)
            except ModuleNotFoundError:
                raise RuntimeErrorTea(
                    f"pyimport(): modul Python '{name}' tidak ditemukan")
            except Exception as e:
                raise RuntimeErrorTea(
                    f"pyimport(): gagal memuat '{name}': {e}")

        self.globals.declare("print", tea_print)
        self.globals.declare("len", tea_len)
        self.globals.declare("input", tea_input)
        self.globals.declare("str", tea_str)
        self.globals.declare("num", tea_num)
        self.globals.declare("push", tea_push)
        self.globals.declare("pop", tea_pop)
        self.globals.declare("keys", tea_keys)
        self.globals.declare("values", tea_values)
        self.globals.declare("range", tea_range)
        self.globals.declare("type", tea_type)
        self.globals.declare("includes", tea_includes)
        self.globals.declare("upper", tea_upper)
        self.globals.declare("lower", tea_lower)
        self.globals.declare("trim", tea_trim)
        self.globals.declare("split", tea_split)
        self.globals.declare("join", tea_join)
        self.globals.declare("abs", tea_abs)
        self.globals.declare("min", tea_min)
        self.globals.declare("max", tea_max)
        self.globals.declare("pyimport", tea_pyimport)

    # --- Utility ---
    def type_name(self, value):
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "boolean"
        if isinstance(value, (int, float)):
            return "number"
        if isinstance(value, str):
            return "string"
        if isinstance(value, list):
            return "list"
        if isinstance(value, dict):
            return "dict"
        if isinstance(value, Function) or callable(value):
            return "function"
        # Objek Python lain (hasil pyimport): nama kelasnya
        return type(value).__name__

    # --- Utility ---
    def to_string(self, value, nested=False):
        if value is None:
            return "nil"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, str):
            # string dalam wadah (list/dict) dikutip agar tidak tertukar
            return f'"{value}"' if nested else value
        if isinstance(value, list):
            return "[" + ", ".join(self.to_string(v, True) for v in value) + "]"
        if isinstance(value, dict):
            items = ", ".join(
                f"{self.to_string(k, True)}: {self.to_string(v, True)}"
                for k, v in value.items())
            return "{" + items + "}"
        if isinstance(value, Function):
            return f"<fn {value.name}>"
        return str(value)

    def is_truthy(self, value):
        if value is None or value is False:
            return False
        if isinstance(value, (int, float)) and value == 0:
            return False
        if isinstance(value, str) and value == "":
            return False
        return True

    def iterate(self, value, line):
        """Daftar nilai yang bisa diiterasi oleh for...in."""
        if isinstance(value, list):
            return list(value)  # salinan, aman jika list diubah di dalam loop
        if isinstance(value, str):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        raise RuntimeErrorTea(
            "for...in hanya mendukung list, string, dan dictionary", line)

    # --- Web (Flask) ---
    def _install_web(self):
        """Modul `Web`: bikin server web di dalam TeaScript.

        Flask diimpor saat `Web.app()` dipanggil, bukan saat Evaluator dibuat,
        supaya TeaScript tetap bisa dipakai tanpa Flask terpasang.
        Web.app() juga mengubah atribut blocking jadi non-blocking saat
        TEASCRIPT_NO_BLOCK diset (mode test).
        """
        evaluator = self

        def to_response(value, jsonify):
            """Ubah nilai balik handler TeaScript jadi respons Flask."""
            if value is None:
                return "", 204
            if isinstance(value, bool):
                return "", 200 if value else 500
            if isinstance(value, (int, float)):
                return str(value), 200
            if isinstance(value, (str, bytes)):
                return value
            if isinstance(value, (list, dict)):
                return jsonify(value)
            raise RuntimeErrorTea(
                f"handler Flask tidak bisa mengembalikan tipe "
                f"{evaluator.type_name(value)}")

        class WebApp:
            def __init__(self, name="teascript"):
                try:
                    flask = importlib.import_module("flask")
                except ImportError:
                    raise RuntimeErrorTea(
                        "Web.app() butuh Flask. Install dulu:\n"
                        "  pip install flask   (atau: pip install "
                        "'teascript[web]')")
                self.flask = flask
                self.app = flask.Flask(name)
                self.routes = {}

            def route(self, rule, *args, **kwargs):
                def daftar(handler):
                    if rule in self.routes:
                        nama_lama = getattr(self.routes[rule], "name", "?")
                        raise RuntimeErrorTea(
                            f"route '{rule}' sudah dipakai handler "
                            f"'{nama_lama}'")
                    self.routes[rule] = handler
                    jsonify = self.flask.jsonify

                    def view(*vargs, **vkwargs):
                        hasil = handler(*vargs, **vkwargs)
                        return to_response(hasil, jsonify)

                    view.__name__ = f"tea_{len(self.routes)}_{handler.name}"
                    self.app.route(rule, *args, **kwargs)(view)
                    return handler
                return daftar

            def plain(self, path, handler):
                self.route(path)(handler)
                return handler

            def test_client(self):
                return self.app.test_client()

            def run(self, *args, **kwargs):
                evaluator.guard_blocking("run")
                # port/host dari env, supaya `tea-web --port N` berlaku
                kwargs.setdefault(
                    "port", int(os.environ.get("TEASCRIPT_PORT", 5000)))
                kwargs.setdefault(
                    "host", os.environ.get("TEASCRIPT_HOST", "127.0.0.1"))
                return self.app.run(*args, **kwargs)

        class WebModule:
            def app(self, name="teascript"):
                return WebApp(name)

        self.globals.declare("Web", WebModule())

    # --- Entry ---
    def run(self, program, base_dir=None):
        if base_dir is not None:
            self.base_dir = base_dir
        try:
            for stmt in program.statements:
                self.execute(stmt, self.globals)
        except BreakSignal as s:
            raise RuntimeErrorTea("'break' di luar loop", s.line)
        except ContinueSignal as s:
            raise RuntimeErrorTea("'continue' di luar loop", s.line)

    # --- Sistem modul ---
    def resolve_module(self, name, path, line):
        """Cari file modul, kembalikan path absolut."""
        if path is not None:
            candidate = path if os.path.isabs(path) \
                else os.path.join(self.base_dir, path)
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
            raise RuntimeErrorTea(f"file modul '{path}' tidak ditemukan", line)

        stdlib = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "modules")
        search_dirs = [self.base_dir, stdlib]
        search_dirs += [d for d in
                        os.environ.get("TEASCRIPT_PATH", "").split(os.pathsep)
                        if d]
        for d in search_dirs:
            candidate = os.path.join(d, name + ".tea")
            if os.path.isfile(candidate):
                return os.path.abspath(candidate)
        dicari = ", ".join(os.path.join(d, name + ".tea") for d in search_dirs)
        raise RuntimeErrorTea(
            f"modul '{name}' tidak ditemukan (dicari di: {dicari})", line)

    def load_module(self, name, path, line):
        """Eksekusi file modul sekali, kembalikan dict ekspornya."""
        abs_path = self.resolve_module(name, path, line)
        if abs_path in self.module_cache:
            return self.module_cache[abs_path]
        if abs_path in self.module_stack:
            chain = " -> ".join(
                os.path.basename(p) for p in self.module_stack + [abs_path])
            raise RuntimeErrorTea(f"import melingkar: {chain}", line)

        fname = os.path.basename(abs_path)
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError as e:
            raise RuntimeErrorTea(f"tidak bisa membaca modul '{fname}': {e}",
                                  line)

        try:
            tokens = Lexer(source).tokenize()
            program = Parser(tokens).parse()
        except TeaError as e:
            e.message = f"{fname}: {e.message}"
            raise

        prev_base = self.base_dir
        self.base_dir = os.path.dirname(abs_path)
        self.module_stack.append(abs_path)
        mod_env = Environment(parent=self.globals)
        try:
            for stmt in program.statements:
                self.execute(stmt, mod_env)
        except TeaError as e:
            e.message = f"{fname}: {e.message}"
            raise
        except BreakSignal as s:
            raise RuntimeErrorTea(f"{fname}: 'break' di luar loop", s.line)
        except ContinueSignal as s:
            raise RuntimeErrorTea(f"{fname}: 'continue' di luar loop", s.line)
        finally:
            self.module_stack.pop()
            self.base_dir = prev_base

        # Nama privat (diawali _) tidak diekspor
        namespace = {k: v for k, v in mod_env.values.items()
                     if not k.startswith("_")}
        self.module_cache[abs_path] = namespace
        return namespace

    # --- Statements ---
    def execute(self, node, env):
        if isinstance(node, ast.Let):
            value = self.evaluate(node.value, env)
            env.declare(node.name, value)

        elif isinstance(node, ast.KwArg):
            # Keyword argument di luar daftar argumen pemanggilan
            raise RuntimeErrorTea(
                "keyword argument (let _nama = ...) hanya boleh di dalam "
                "daftar argumen fungsi Python", node.line)

        elif isinstance(node, ast.Bind):
            # `let nama = nilai` di dalam argumen: deklarasikan lalu lanjut
            value = self.evaluate(node.value, env)
            env.declare(node.name, value)

        elif isinstance(node, ast.Assign):
            value = self.evaluate(node.value, env)
            env.set(node.name, value, node.line)

        elif isinstance(node, ast.IndexAssign):
            target = self.evaluate(node.target, env)
            index = self.evaluate(node.index, env)
            value = self.evaluate(node.value, env)
            self.assign_index(target, index, value, node.line)

        elif isinstance(node, ast.ExprStmt):
            self.evaluate(node.expr, env)

        elif isinstance(node, ast.If):
            cond = self.evaluate(node.condition, env)
            if self.is_truthy(cond):
                for s in node.then_body:
                    self.execute(s, env)
            else:
                for s in node.else_body:
                    self.execute(s, env)

        elif isinstance(node, ast.While):
            while self.is_truthy(self.evaluate(node.condition, env)):
                try:
                    for s in node.body:
                        self.execute(s, env)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break

        elif isinstance(node, ast.ForIn):
            iterable = self.evaluate(node.iterable, env)
            items = self.iterate(iterable, node.line)
            for item in items:
                env.declare(node.name, item)
                try:
                    for s in node.body:
                        self.execute(s, env)
                except ContinueSignal:
                    continue
                except BreakSignal:
                    break

        elif isinstance(node, ast.Break):
            raise BreakSignal(node.line)

        elif isinstance(node, ast.Continue):
            raise ContinueSignal(node.line)

        elif isinstance(node, ast.Import):
            namespace = self.load_module(node.name, node.path, node.line)
            env.declare(node.name, namespace)

        elif isinstance(node, ast.FromImport):
            namespace = self.load_module(node.module, None, node.line)
            for n in node.names:
                if n not in namespace:
                    raise RuntimeErrorTea(
                        f"modul '{node.module}' tidak mengekspor '{n}'",
                        node.line)
                env.declare(n, namespace[n])

        elif isinstance(node, ast.FnDef):
            fn = Function(node.name, node.params, node.body, env,
                          evaluator=self)
            env.declare(node.name, fn)

        elif isinstance(node, ast.Return):
            value = self.evaluate(node.value, env)
            raise ReturnSignal(value)

        else:
            raise RuntimeErrorTea(f"statement tidak dikenal: {type(node).__name__}",
                                  getattr(node, "line", None))

    # --- Expressions ---
    def evaluate(self, node, env):
        if isinstance(node, ast.Number):
            return node.value
        if isinstance(node, ast.String):
            return node.value
        if isinstance(node, ast.Bool):
            return node.value
        if isinstance(node, ast.Nil):
            return None
        if isinstance(node, ast.Ident):
            return env.get(node.name, node.line)

        if isinstance(node, ast.ListLit):
            return [self.evaluate(e, env) for e in node.elements]

        if isinstance(node, ast.DictLit):
            d = {}
            for key_node, value_node in node.pairs:
                key = self.evaluate(key_node, env)
                self.check_hashable(key, key_node.line)
                d[key] = self.evaluate(value_node, env)
            return d

        if isinstance(node, ast.Unary):
            if node.op == "-":
                v = self.evaluate(node.operand, env)
                if not isinstance(v, (int, float)) or isinstance(v, bool):
                    raise RuntimeErrorTea("operator '-' hanya untuk angka", node.line)
                return -v
            if node.op == "not":
                return not self.is_truthy(self.evaluate(node.operand, env))

        if isinstance(node, ast.Binary):
            return self.eval_binary(node, env)

        if isinstance(node, ast.Ternary):
            cond = self.evaluate(node.condition, env)
            if self.is_truthy(cond):
                return self.evaluate(node.then, env)
            return self.evaluate(node.otherwise, env)

        if isinstance(node, ast.Interp):
            out = []
            for part in node.parts:
                if isinstance(part, str):
                    out.append(part)
                else:
                    out.append(self.to_string(self.evaluate(part, env)))
            return "".join(out)

        if isinstance(node, ast.Bind):
            # jalur ekspresi: print(let x = 1) -> deklarasikan, nilainya dipakai
            value = self.evaluate(node.value, env)
            env.declare(node.name, value)
            return value

        if isinstance(node, ast.Call):
            callee = self.evaluate(node.callee, env)
            args = []
            kwargs = {}
            for a in node.args:
                if isinstance(a, ast.KwArg):
                    # `let _as_text = true` di dalam argumen → kwarg as_text=true
                    kwargs[a.name] = self.evaluate(a.value, env)
                else:
                    args.append(self.evaluate(a, env))
            return self.call(callee, args, node.line, kwargs)

        if isinstance(node, ast.Index):
            target = self.evaluate(node.target, env)
            index = self.evaluate(node.index, env)
            return self.index_get(target, index, node.line)

        if isinstance(node, ast.Slice):
            target = self.evaluate(node.target, env)
            start = self.evaluate(node.start, env) if node.start is not None else None
            end = self.evaluate(node.end, env) if node.end is not None else None
            return self.slice_get(target, start, end, node.line)

        raise RuntimeErrorTea(f"ekspresi tidak dikenal: {type(node).__name__}",
                              getattr(node, "line", None))

    def eval_binary(self, node, env):
        op = node.op

        # short-circuit
        if op == "and":
            left = self.evaluate(node.left, env)
            if not self.is_truthy(left):
                return left
            return self.evaluate(node.right, env)
        if op == "or":
            left = self.evaluate(node.left, env)
            if self.is_truthy(left):
                return left
            return self.evaluate(node.right, env)

        left = self.evaluate(node.left, env)
        right = self.evaluate(node.right, env)

        if op == "+":
            # string concat jika salah satu string
            if isinstance(left, str) or isinstance(right, str):
                return self.to_string(left) + self.to_string(right)
            self.check_numbers(left, right, op, node.line)
            return left + right
        if op == "-":
            self.check_numbers(left, right, op, node.line)
            return left - right
        if op == "*":
            # string * angka → ulangi string
            if isinstance(left, str) and isinstance(right, int) and not isinstance(right, bool):
                if right < 0:
                    return ""
                return left * right
            if isinstance(right, str) and isinstance(left, int) and not isinstance(left, bool):
                if left < 0:
                    return ""
                return right * left
            self.check_numbers(left, right, op, node.line)
            return left * right
        if op == "/":
            self.check_numbers(left, right, op, node.line)
            if right == 0:
                raise RuntimeErrorTea("pembagian dengan nol", node.line)
            return left / right
        if op == "%":
            self.check_numbers(left, right, op, node.line)
            if right == 0:
                raise RuntimeErrorTea("modulo dengan nol", node.line)
            return left % right
        if op == "==":
            return self.is_equal(left, right)
        if op == "!=":
            return not self.is_equal(left, right)
        if op == "in":
            return self.contains(left, right, node.line)
        if op == "not in":
            return not self.contains(left, right, node.line)
        if op == "<":
            self.check_comparable(left, right, op, node.line)
            return left < right
        if op == ">":
            self.check_comparable(left, right, op, node.line)
            return left > right
        if op == "<=":
            self.check_comparable(left, right, op, node.line)
            return left <= right
        if op == ">=":
            self.check_comparable(left, right, op, node.line)
            return left >= right

        raise RuntimeErrorTea(f"operator tidak dikenal: {op}", node.line)

    def check_numbers(self, a, b, op, line):
        if isinstance(a, bool) or isinstance(b, bool):
            raise RuntimeErrorTea(f"operator '{op}' tidak mendukung boolean", line)
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise RuntimeErrorTea(f"operator '{op}' membutuhkan angka", line)

    def check_comparable(self, a, b, op, line):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) \
                and not isinstance(a, bool) and not isinstance(b, bool):
            return
        if isinstance(a, str) and isinstance(b, str):
            return
        raise RuntimeErrorTea(f"operator '{op}' tidak bisa membandingkan tipe ini", line)

    def is_equal(self, a, b):
        if a is None and b is None:
            return True
        if isinstance(a, bool) or isinstance(b, bool):
            return a is b
        return a == b

    def contains(self, item, container, line=None):
        """Cek keanggotaan untuk operator `in` dan builtin includes()."""
        if isinstance(container, str):
            if not isinstance(item, str):
                raise RuntimeErrorTea(
                    "operator 'in' untuk string membutuhkan string di kiri, "
                    f"diberi {self.type_name(item)}", line)
            return item in container
        if isinstance(container, list):
            return any(self.is_equal(item, v) for v in container)
        if isinstance(container, dict):
            self.check_hashable(item, line)
            return item in container
        raise RuntimeErrorTea(
            f"operator 'in' tidak mendukung tipe {self.type_name(container)}",
            line)

    def check_hashable(self, key, line=None):
        try:
            hash(key)
        except TypeError:
            raise RuntimeErrorTea(
                "key dictionary harus berupa string, angka, boolean, atau nil",
                line)

    def slice_get(self, target, start, end, line):
        if not isinstance(target, (list, str)):
            raise RuntimeErrorTea(
                f"slice tidak mendukung tipe {self.type_name(target)}", line)
        for name, v in (("awal", start), ("akhir", end)):
            if v is not None and (not isinstance(v, int) or isinstance(v, bool)):
                raise RuntimeErrorTea(
                    f"batas {name} slice harus angka bulat", line)
        n = len(target)
        s = 0 if start is None else start
        e = n if end is None else end
        if s < 0:
            s += n
        if e < 0:
            e += n
        s = max(0, min(s, n))
        e = max(0, min(e, n))
        return target[s:e]

    def call(self, callee, args, line, kwargs=None):
        kwargs = kwargs or {}
        if isinstance(callee, Function):
            if kwargs:
                raise RuntimeErrorTea(
                    "keyword argument (let _nama = ...) hanya untuk fungsi Python",
                    line)
            if len(args) != len(callee.params):
                raise RuntimeErrorTea(
                    f"fungsi '{callee.name}' butuh {len(callee.params)} argumen, "
                    f"diberi {len(args)}", line)
            return self.invoke(callee, args, line)
        if callable(callee):
            try:
                result = callee(*args, **kwargs)
            except RuntimeErrorTea as e:
                if e.line is None:
                    e.line = line  # lengkapi posisi error dari pemanggilan
                raise
            except Exception as e:
                raise RuntimeErrorTea(f"error saat memanggil fungsi bawaan: {e}", line)
            return self.from_python(result)
        raise RuntimeErrorTea("nilai tidak bisa dipanggil", line)

    def invoke(self, fn, args, line=None):
        """Jalankan fungsi TeaScript dengan argumen yang sudah siap."""
        local = Environment(parent=fn.closure)
        for p, a in zip(fn.params, args):
            local.declare(p, a)
        try:
            for stmt in fn.body:
                self.execute(stmt, local)
        except ReturnSignal as r:
            return self.to_python(r.value)
        except BreakSignal as s:
            raise RuntimeErrorTea("'break' di luar loop", s.line)
        except ContinueSignal as s:
            raise RuntimeErrorTea("'continue' di luar loop", s.line)
        return None

    def to_python(self, value):
        """Siapkan nilai TeaScript untuk dikembalikan ke kode Python.

        Nilai balik fungsi TeaScript jadi callable Python, sehingga bisa
        dipakai sebagai handler (Flask, tombol, callback) tanpa pembungkus.
        """
        if callable(value) and getattr(value, "evaluator", None) is self:
            return value
        return value

    def from_python(self, value):
        """Kembalikan nilai hasil pemanggilan Python apa adanya.

        dict/list/str/angka sudah cocok untuk TeaScript; objek Python lain
        tetap jadi nilai opak yang bisa diberi atribut.
        """
        return value

    def guard_blocking(self, name):
        """Cegah pemanggilan yang memblokir proses (server/menu).

        Dipakai untuk Web/Flask: `app.run()` sebenarnya tidak memblokir,
        sehingga contoh web tetap aman dijalankan di test.
        """
        if os.environ.get("TEASCRIPT_NO_BLOCK"):
            raise RuntimeErrorTea(
                f"{name}() dimatikan karena TEASCRIPT_NO_BLOCK diset "
                f"(mode non-interaktif)")
        return True

    def index_get(self, target, index, line):
        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErrorTea("indeks list harus angka bulat", line)
            if index < 0 or index >= len(target):
                raise RuntimeErrorTea(f"indeks {index} di luar batas list", line)
            return target[index]
        if isinstance(target, dict):
            self.check_hashable(index, line)
            if index not in target:
                raise RuntimeErrorTea(f"key '{index}' tidak ada di dictionary", line)
            return target[index]
        if isinstance(target, str):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErrorTea("indeks string harus angka bulat", line)
            if index < 0 or index >= len(target):
                raise RuntimeErrorTea(f"indeks {index} di luar batas string", line)
            return target[index]

        # Objek Python (hasil pyimport): akses atribut, mis. m.sqrt
        if isinstance(index, str) and not isinstance(target, Function) \
                and not isinstance(target, (int, float, bool)) \
                and target is not None:
            try:
                return getattr(target, index)
            except AttributeError:
                raise RuntimeErrorTea(
                    f"objek Python tidak punya atribut '{index}'", line)

        raise RuntimeErrorTea("tipe ini tidak mendukung indeks", line)

    def assign_index(self, target, index, value, line):
        if isinstance(target, list):
            if not isinstance(index, int) or isinstance(index, bool):
                raise RuntimeErrorTea("indeks list harus angka bulat", line)
            if index < 0 or index >= len(target):
                raise RuntimeErrorTea(f"indeks {index} di luar batas list", line)
            target[index] = value
            return
        if isinstance(target, dict):
            self.check_hashable(index, line)
            target[index] = value
            return
        # Objek Python: set atribut, mis. obj.attr = 1
        if isinstance(index, str) and not isinstance(target, (Function, str)) \
                and not isinstance(target, (int, float, bool)) \
                and target is not None:
            try:
                setattr(target, index, value)
                return
            except (AttributeError, TypeError):
                raise RuntimeErrorTea(
                    f"tidak bisa mengubah atribut '{index}' pada objek Python",
                    line)
        raise RuntimeErrorTea("tipe ini tidak mendukung assignment indeks", line)