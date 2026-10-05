"""
Compile-time constant folding AST transformation for Radical.
"""

import ast


class RadicalConstantFolder(ast.NodeTransformer):
    """
    Evaluates constant arithmetic, power, bitwise, string concatenation,
    and boolean operations at compile time.
    """
    def __init__(self) -> None:
        self.folded_count = 0

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.left, ast.Constant) and isinstance(node.right, ast.Constant):
            lv = node.left.value
            rv = node.right.value
            if isinstance(lv, (int, float, str, bool)) and isinstance(rv, (int, float, str, bool)):
                try:
                    res = None
                    if isinstance(node.op, ast.Add): res = lv + rv
                    elif isinstance(node.op, ast.Sub): res = lv - rv
                    elif isinstance(node.op, ast.Mult):
                        if not (isinstance(lv, str) and rv > 1000) and not (isinstance(rv, str) and lv > 1000):
                            res = lv * rv
                    elif isinstance(node.op, ast.Div) and rv != 0: res = lv / rv
                    elif isinstance(node.op, ast.FloorDiv) and rv != 0: res = lv // rv
                    elif isinstance(node.op, ast.Mod) and rv != 0: res = lv % rv
                    elif isinstance(node.op, ast.Pow) and abs(rv) <= 64: res = lv ** rv
                    elif isinstance(node.op, ast.LShift) and 0 <= rv <= 64: res = lv << rv
                    elif isinstance(node.op, ast.RShift) and 0 <= rv <= 64: res = lv >> rv
                    elif isinstance(node.op, ast.BitOr): res = lv | rv
                    elif isinstance(node.op, ast.BitAnd): res = lv & rv
                    elif isinstance(node.op, ast.BitXor): res = lv ^ rv

                    if res is not None:
                        self.folded_count += 1
                        new_node = ast.Constant(value=res)
                        return ast.copy_location(new_node, node)
                except Exception:
                    pass
        return node

    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.AST:
        self.generic_visit(node)
        if isinstance(node.operand, ast.Constant):
            v = node.operand.value
            if isinstance(v, (int, float, bool)):
                try:
                    res = None
                    if isinstance(node.op, ast.USub): res = -v
                    elif isinstance(node.op, ast.UAdd): res = +v
                    elif isinstance(node.op, ast.Not): res = not v
                    elif isinstance(node.op, ast.Invert): res = ~v

                    if res is not None:
                        self.folded_count += 1
                        new_node = ast.Constant(value=res)
                        return ast.copy_location(new_node, node)
                except Exception:
                    pass
        return node
