"""Tree-sitter CST 的命名节点视图"""
from tree_sitter import Language, Parser
import tree_sitter_cpp


class SourceParseError(ValueError):
    """源码无法完整解析，不能据此生成扣分结果。"""


def walk(node):
    pending = [node]
    while pending:
        current = pending.pop()
        yield current
        pending.extend(reversed(current.named_children))


def text(node):
    return node.text.decode("utf-8") if node is not None else ""


def nodes(node, *kinds):
    return [item for item in walk(node) if item.type in kinds]


def parse(source: str):
    root = Parser(Language(tree_sitter_cpp.language())).parse(source.encode("utf-8")).root_node
    if root.has_error:
        bad = next(n for n in walk(root) if n.type == "ERROR" or n.is_missing)
        raise SourceParseError(f"C++ 解析失败：第 {bad.start_point.row + 1} 行，第 {bad.start_point.column + 1} 字节列")
    return root
