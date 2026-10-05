"""
Radical Language Semantic Analyzer.
Tracks symbol tables across scopes and verifies const immutability invariants at compile-time.
"""

import ast
from typing import Any, Optional
from radical.exceptions import RadicalCompileError


class Scope:
    """Represents a lexical scope for symbol resolution."""
    def __init__(self, name: str = "<module>", parent: Optional["Scope"] = None) -> None:
        self.name = name
        self.parent = parent
        # Maps const symbol name -> [lineno, col_offset, filename, is_initialized]
        self.constants: dict[str, list[Any]] = {}
        self.variables: set[str] = set()

    def declare_const(self, name: str, lineno: int, col: int, filename: str) -> None:
        if name in self.constants:
            prev_line, prev_col, _, _ = self.constants[name]
            raise RadicalCompileError(
                message=f"Cannot redeclare constant '{name}' (previously declared at line {prev_line}, col {prev_col})",
                filename=filename,
                lineno=lineno,
                col_offset=col,
            )
        self.constants[name] = [lineno, col, filename, False]
        self.variables.add(name)

    def is_const(self, name: str) -> Optional[list[Any]]:
        """Returns declaration metadata if name is a constant in this or enclosing scope."""
        if name in self.constants:
            return self.constants[name]
        if self.parent:
            return self.parent.is_const(name)
        return None


class RadicalSemanticAnalyzer(ast.NodeVisitor):
    """
    Traverses standard Python AST to enforce const invariants and variable safety.
    """
    def __init__(self, filename: str = "<string>", const_declarations: Optional[dict[str, list[tuple[int, int]]]] = None) -> None:
        self.filename = filename
        self.current_scope = Scope("<module>")
        self.pending_constants: list[tuple[str, int, int]] = []

    def push_scope(self, name: str) -> Scope:
        self.current_scope = Scope(name, parent=self.current_scope)
        return self.current_scope

    def pop_scope(self) -> Scope:
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent
        return self.current_scope

    def register_const(self, name: str, lineno: int, col: int) -> None:
        self.pending_constants.append((name, lineno, col))

    def _sync_constants_for_scope(self, scope_node: ast.AST) -> None:
        """Registers constants belonging to the current scope."""
        start_line = getattr(scope_node, "lineno", 1)
        end_line = getattr(scope_node, "end_lineno", 1000000000)
        remaining: list[tuple[str, int, int]] = []
        for name, line, col in self.pending_constants:
            if start_line <= line <= end_line:
                self.current_scope.declare_const(name, line, col, self.filename)
            else:
                remaining.append((name, line, col))
        self.pending_constants = remaining

    def check_assignment_target(self, target: ast.AST, lineno: int, col: int, is_init_allowed: bool = False) -> None:
        """Verifies that an assignment target is not an existing constant."""
        if isinstance(target, ast.Name):
            const_info = self.current_scope.is_const(target.id)
            if const_info is not None:
                decl_line, decl_col, _, is_initialized = const_info
                # If this is the initial assignment allowed for this constant, mark it
                if is_init_allowed and not is_initialized:
                    const_info[3] = True
                    return
                raise RadicalCompileError(
                    message=f"Cannot reassign constant '{target.id}' (declared as const at line {decl_line}, col {decl_col})",
                    filename=self.filename,
                    lineno=lineno,
                    col_offset=col,
                )
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                self.check_assignment_target(elt, lineno, col, is_init_allowed)

    def visit_Module(self, node: ast.Module) -> None:
        # Register module-level constants first
        for name, line, col in list(self.pending_constants):
            # Check if this constant is outside any top-level function/class
            is_in_child = False
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    c_start = getattr(child, "lineno", 1)
                    c_end = getattr(child, "end_lineno", 1)
                    if c_start <= line <= c_end:
                        is_in_child = True
                        break
            if not is_in_child:
                self.current_scope.declare_const(name, line, col, self.filename)
                self.pending_constants.remove((name, line, col))

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self.check_assignment_target(target, node.lineno, node.col_offset, is_init_allowed=True)
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.check_assignment_target(node.target, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        # Walrus operator :=
        self.check_assignment_target(node.target, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.check_assignment_target(node.target, node.lineno, node.col_offset)
        self.generic_visit(node)

    def _validate_native_fn(self, node: ast.FunctionDef) -> None:
        is_native = any(
            (isinstance(d, ast.Name) and d.id == "_rad_native") or
            (isinstance(d, ast.Call) and getattr(d.func, "id", "") == "_rad_native")
            for d in node.decorator_list
        )
        if not is_native:
            return

        for arg in node.args.args:
            if arg.arg == "self":
                continue
            if arg.annotation is None:
                raise RadicalCompileError(
                    f"native fn '{node.name}' cannot compile: parameter '{arg.arg}' must have an explicit type annotation.",
                    filename=self.filename,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )
            ann_str = ast.unparse(arg.annotation).lower()
            if any(bad in ann_str for bad in ("dict", "set", "list", "any", "object")):
                raise RadicalCompileError(
                    f"native fn '{node.name}' cannot compile: parameter '{arg.arg}: {ast.unparse(arg.annotation)}' is unsupported in native compiled tier. Only primitive numerics and continuous buffers are permitted.",
                    filename=self.filename,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )

        if node.returns is None:
            raise RadicalCompileError(
                f"native fn '{node.name}' cannot compile: missing return type annotation. Native compiled tier requires explicit return type.",
                filename=self.filename,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        ret_str = ast.unparse(node.returns).lower()
        if any(bad in ret_str for bad in ("dict", "set", "list", "any", "object")):
            raise RadicalCompileError(
                f"native fn '{node.name}' cannot compile: return type '{ast.unparse(node.returns)}' is unsupported in native compiled tier.",
                filename=self.filename,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        for sub in ast.walk(node):
            if isinstance(sub, (ast.Try, ast.Yield, ast.YieldFrom, ast.AsyncFor, ast.AsyncWith)):
                raise RadicalCompileError(
                    f"native fn '{node.name}' cannot compile: {type(sub).__name__} is unsupported in native tier.",
                    filename=self.filename,
                    lineno=getattr(sub, "lineno", node.lineno),
                    col_offset=getattr(sub, "col_offset", node.col_offset),
                )

    def _validate_try_operator_usage(self, node: ast.FunctionDef) -> None:
        has_try_op = False
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id.startswith("_rad_try_tmp_"):
                has_try_op = True
                break

        if has_try_op and node.returns is not None:
            ret_str = ast.unparse(node.returns)
            if ret_str in ("int", "float", "str", "bool", "None", "list", "dict", "tuple"):
                raise RadicalCompileError(
                    f"Cannot use '?' error propagation operator in function '{node.name}' declared to return '{ret_str}': enclosing function must return Result or Option.",
                    filename=self.filename,
                    lineno=node.lineno,
                    col_offset=node.col_offset,
                )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.check_assignment_target(ast.Name(id=node.name, ctx=ast.Store()), node.lineno, node.col_offset)
        self._validate_native_fn(node)
        self._validate_try_operator_usage(node)
        self.push_scope(node.name)
        self._sync_constants_for_scope(node)
        self.generic_visit(node)
        self.pop_scope()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.check_assignment_target(ast.Name(id=node.name, ctx=ast.Store()), node.lineno, node.col_offset)
        self.push_scope(node.name)
        self._sync_constants_for_scope(node)
        self.generic_visit(node)
        self.pop_scope()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.check_assignment_target(ast.Name(id=node.name, ctx=ast.Store()), node.lineno, node.col_offset)
        self.push_scope(node.name)
        self._sync_constants_for_scope(node)
        self.generic_visit(node)
        self.pop_scope()
