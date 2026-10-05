"""
Radical Language Unified Transpiler and AST Lowering Pipeline.
Orchestrates all lexical, syntactic, and semantic transformations.
"""

import ast
from typing import Optional, Any
from radical.parser import RadicalParser
from radical.semantics import RadicalSemanticAnalyzer
from radical.exceptions import RadicalCompileError
from radical.transforms.folding import RadicalConstantFolder

# Export for backwards compatibility
__all__ = ["RadicalTranspiler", "RadicalConstantFolder"]


class RadicalTranspiler:
    """
    Transforms Radical (.rad) source code into clean, valid Python 3.10+ code.
    """
    def __init__(self, filename: str = "<string>") -> None:
        self.filename = filename
        self.last_explanations: list[str] = []
        self.last_ast: Optional[ast.AST] = None

    def _transform_tokens(
        self,
        parser: RadicalParser,
        tokens: list[Any],
    ) -> tuple[list[Any], list[tuple[str, int, int]], dict[str, bool]]:
        """Applies all token-level transformations in defined compilation order."""
        all_constants: list[tuple[str, int, int]] = []
        reqs: dict[str, bool] = {
            "itertools": False,
            "dataclass": False,
            "ctypes": False,
            "runtime": False,
            "gpu": False,
        }

        # 0. Transform let mutable bindings
        tokens = parser.transform_let(tokens)

        # 0a. Transform tagged template literals
        tokens, _ = parser.transform_tagged_templates(tokens)

        # 0b. Transform using resource cleanup blocks
        tokens, _ = parser.transform_using(tokens)

        # 0c. Transform unsafe scoped blocks
        tokens, req_unsafe = parser.transform_unsafe(tokens)
        if req_unsafe:
            reqs["runtime"] = True

        # 0d. Transform native fn functions
        tokens, req_native = parser.transform_native_fn(tokens)
        if req_native:
            reqs["runtime"] = True

        # 0e. Transform enum ADTs / variants
        tokens, req_enum = parser.transform_enums(tokens)
        if req_enum:
            reqs["dataclass"] = True

        # 0f. Transform Rust-style ? error propagation
        tokens, _ = parser.transform_try_operator(tokens)

        # 0g. Transform copy-update `expr with { ... }`
        tokens, req_cw = parser.transform_struct_with(tokens)
        if req_cw:
            reqs["runtime"] = True

        # 0h. Transform traits (structural typing protocols)
        tokens, req_trait = parser.transform_traits(tokens)
        if req_trait:
            reqs["dataclass"] = True

        # 0i. Transform channel select blocks
        tokens, req_select = parser.transform_select(tokens)
        if req_select:
            reqs["runtime"] = True

        # 1. Transform destructuring
        tokens, dest_consts = parser.transform_destructuring(tokens)
        all_constants.extend(dest_consts)

        # 2. Transform const declarations
        tokens, consts = parser.transform_const(tokens)
        all_constants.extend(consts)

        # 3. Transform Mojo-style fn functions
        tokens, fn_consts = parser.transform_fn_functions(tokens)
        all_constants.extend(fn_consts)

        # 4. Transform struct declarations
        tokens, req_dc = parser.transform_structs(tokens)
        if req_dc:
            reqs["dataclass"] = True

        # 5. Transform Cartesian loops (A x B)
        tokens, req_iter = parser.transform_cartesian_loops(tokens)
        if req_iter:
            reqs["itertools"] = True

        # 6. Transform range literals (0..10, 1..=10)
        tokens = parser.transform_ranges(tokens)

        # 7. Transform raw ctypes memory buffers
        tokens, req_ctypes = parser.transform_raw_buffers(tokens)
        if req_ctypes:
            reqs["ctypes"] = True

        # 8. Transform multi-threaded parallel loops
        tokens, req_par = parser.transform_parallel_loops(tokens)
        if req_par:
            reqs["runtime"] = True

        # 9. Transform GPU constructs (gpu for, gpu fn)
        tokens, req_gpu = parser.transform_gpu_constructs(tokens)
        if req_gpu:
            reqs["gpu"] = True

        # 10. Transform deferred execution (defer)
        tokens, req_def = parser.transform_defer(tokens)
        if req_def:
            reqs["runtime"] = True

        # 11. Transform safe navigation (?., ?[], ?.())
        tokens = parser.transform_safe_nav(tokens)

        # 12. Transform nullish coalescing (??, ??=)
        tokens = parser.transform_coalescing(tokens)

        # 13. Transform arrow functions (=>)
        tokens = parser.transform_arrows(tokens)

        # 14. Transform pipeline operator (|>)
        tokens = parser.transform_pipelines(tokens)

        return tokens, all_constants, reqs

    def _generate_headers(self, python_code: str, reqs: dict[str, bool]) -> tuple[str, int]:
        """Generates preamble imports for standard library and runtime modules."""
        runtime_symbols = (
            "_rad_safe_attr", "_rad_safe_item", "_rad_safe_call",
            "_rad_coalesce", "_RadicalDeferStack", "_rad_parallel_for", "simd",
            "Result", "Ok", "Err", "Option", "Some", "Nil", "None_",
            "chan", "Channel", "select", "buffer", "TypedBuffer", "Arena", "arena",
            "_rad_unsafe_context", "_rad_copy_with", "_rad_native",
            "u8", "uint8", "byte", "i8", "int8", "u16", "uint16", "i16", "int16",
            "u32", "uint32", "i32", "int32", "u64", "uint64", "i64", "int64",
            "f16", "f32", "float32", "f64", "float64"
        )
        requires_runtime = reqs["runtime"] or any(h in python_code for h in runtime_symbols)
        requires_gpu = reqs["gpu"] or ("gpu" in python_code)

        headers: list[str] = []
        if reqs["itertools"] and "import itertools" not in python_code:
            headers.append("import itertools")
        if reqs["dataclass"]:
            if "from dataclasses import dataclass" not in python_code:
                headers.append("from dataclasses import dataclass")
        if ("import typing" not in python_code) and (reqs["dataclass"] or "typing." in python_code or "Protocol" in python_code):
            headers.append("import typing")
        if reqs["ctypes"] and "import ctypes" not in python_code:
            headers.append("import ctypes")

        if requires_runtime:
            runtime_imports = [
                "_rad_safe_attr", "_rad_safe_item", "_rad_safe_call",
                "_rad_coalesce", "_RadicalDeferStack", "_rad_parallel_for", "simd",
                "Result", "Ok", "Err", "Option", "Some", "Nil", "None_",
                "chan", "Channel", "select", "buffer", "TypedBuffer", "Arena", "arena",
                "_rad_unsafe_context", "_rad_copy_with", "_rad_native",
                "u8", "uint8", "byte", "i8", "int8", "u16", "uint16", "i16", "int16",
                "u32", "uint32", "i32", "int32", "u64", "uint64", "i64", "int64",
                "f16", "f32", "float32", "f64", "float64"
            ]
            needed = [name for name in runtime_imports if name in python_code]
            if needed:
                headers.append(f"from radical.runtime import {', '.join(needed)}")

        if requires_gpu:
            headers.append("from radical.gpu import gpu, GPUBuffer")

        header_str = "\n".join(headers) + ("\n\n" if headers else "")
        header_offset = header_str.count("\n") if header_str else 0
        return header_str, header_offset

    def _optimize_and_verify(
        self,
        full_code: str,
        header_offset: int,
        all_constants: list[tuple[str, int, int]],
    ) -> str:
        """Runs compile-time AST passes (constant folding) and semantic validation."""
        try:
            tree = ast.parse(full_code, filename=self.filename)

            # Compile-time constant folding pass
            folder = RadicalConstantFolder()
            tree = folder.visit(tree)
            ast.fix_missing_locations(tree)
            if folder.folded_count > 0:
                self.last_explanations.append(
                    f"constant folding → evaluated {folder.folded_count} constant operations at build time"
                )
                full_code = ast.unparse(tree)
            self.last_ast = tree

            # Static semantics and const assignment validation
            analyzer = RadicalSemanticAnalyzer(filename=self.filename)
            for name, line, col in all_constants:
                analyzer.register_const(name, line + header_offset, col)
            analyzer.visit(tree)
        except RadicalCompileError:
            raise
        except SyntaxError as e:
            adjusted_line = (e.lineno - header_offset) if (e.lineno and e.lineno > header_offset) else e.lineno
            raise RadicalCompileError(
                message=f"Syntax error in emitted code: {e.msg}",
                filename=self.filename,
                lineno=adjusted_line,
                col_offset=e.offset,
            ) from e

        return full_code

    def transpile(self, source: str, standalone: bool = False) -> str:
        """
        Transpiles Radical source code into standard Python code.
        If standalone is True, inlines minimal runtime helpers so the emitted
        file does not require the `radical` package to run.
        """
        parser = RadicalParser(filename=self.filename)
        tokens = parser.lexer.tokenize(source)

        tokens, all_constants, reqs = self._transform_tokens(parser, tokens)
        self.last_explanations = list(parser.explanations)

        # Reconstruct transformed Python code
        python_code = parser.tokens_to_source(tokens)

        # Generate preamble headers and imports
        header_str, header_offset = self._generate_headers(python_code, reqs)
        full_code = header_str + python_code

        # AST optimization and semantic verification
        return self._optimize_and_verify(full_code, header_offset, all_constants)

    def transpile_ast(self, source: str, standalone: bool = False) -> tuple[Optional[ast.AST], str]:
        """
        Transpiles source code and returns both the optimized AST and emitted Python code.
        """
        code = self.transpile(source, standalone=standalone)
        return self.last_ast, code
