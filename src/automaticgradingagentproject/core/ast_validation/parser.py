"""Tree-sitter CST 的命名节点视图"""
import re

from tree_sitter import Language, Parser
import tree_sitter_cpp


LOOPS = ("for_statement", "while_statement", "do_statement", "for_range_loop")


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
        # 缺失的分号等标点是匿名节点，不能只遍历 named_children。
        bad = root
        while not (bad.is_error or bad.is_missing):
            child = next((n for n in bad.children if n.has_error or n.is_missing), None)
            if child is None:
                break
            bad = child
        raise SourceParseError(f"C++ 解析失败：第 {bad.start_point.row + 1} 行，第 {bad.start_point.column + 1} 字节列")
    return root


def compact(node):
    return re.sub(r"\s+", "", text(node))


def function_name(fn):
    decl = fn.child_by_field_name("declarator")
    while decl is not None and decl.type != "function_declarator":
        decl = decl.child_by_field_name("declarator")
    # 类外定义的 Sorter::quickSort 只保留最后的函数名。
    return compact(decl.child_by_field_name("declarator")).split("::")[-1] if decl else ""


def call_name(callee):
    name = compact(callee)
    if name.startswith("this->"):
        name = name[len("this->"):]
    return name.split("::")[-1]


def calls(node):
    return [call_name(n.child_by_field_name("function")) for n in nodes(node, "call_expression")]


def visible_at(node, site):
    # using / namespace alias 必须在调用之前，且位于其祖先作用域。
    if node.start_byte >= site.start_byte:
        return False
    scope = node.parent
    parent = site
    while parent is not None:
        if parent == scope:
            return True
        parent = parent.parent
    return False


def members(root):
    """逐个读取类或结构体的字段，保留各自的指针和数组修饰。"""
    for record in nodes(root, "class_specifier", "struct_specifier"):
        body = record.child_by_field_name("body")
        if body is None:
            continue
        fields = {}
        for field in body.named_children:
            if field.type != "field_declaration":
                continue
            typ = text(field.child_by_field_name("type"))
            for decl in field.children_by_field_name("declarator"):
                ident = decl
                while ident is not None and ident.type != "field_identifier":
                    if ident.type == "function_declarator":
                        break
                    ident = ident.child_by_field_name("declarator")
                if ident is not None and ident.type == "field_identifier":
                    fields[text(ident).lower()] = (typ, decl)
        yield text(record.child_by_field_name("name")), fields
