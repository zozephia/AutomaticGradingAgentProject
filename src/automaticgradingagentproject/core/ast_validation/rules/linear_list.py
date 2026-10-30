"""专题一的语法结构启发式规则；识别边界见 README。"""
import re

from ..enums import AstRuleEnum as R
from ..parser import nodes, text

LOOPS = ("for_statement", "while_statement", "do_statement", "for_range_loop")
SORTS = {"sort", "stable_sort", "partial_sort", "partial_sort_copy", "nth_element",
         "qsort", "make_heap", "sort_heap", "push_heap", "pop_heap"}


def compact(node):
    return re.sub(r"\s+", "", text(node))


def function_name(fn):
    decl = fn.child_by_field_name("declarator")
    while decl is not None and decl.type != "function_declarator":
        decl = decl.child_by_field_name("declarator")
    return compact(decl.child_by_field_name("declarator")) if decl else ""


def calls(node):
    return [compact(n.child_by_field_name("function")) for n in nodes(node, "call_expression")]


def _visible(node, site):
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


def no_std_sort(root):
    count = 0
    directives = nodes(root, "using_declaration", "namespace_alias_definition")
    definitions = {function_name(n) for n in nodes(root, "function_definition")}
    for call in nodes(root, "call_expression"):
        callee = compact(call.child_by_field_name("function")).lstrip(":")
        callee = re.sub(r"<.*>$", "", callee)
        using = [compact(n) for n in directives if _visible(n, call)]
        for directive in using:
            match = re.fullmatch(r"namespace(\w+)=(std(?:::\w+)*);", directive)
            if match and callee.startswith(match[1] + "::"):
                callee = match[2] + callee[len(match[1]):]
        name = callee.split("::")[-1]
        if name not in SORTS:
            continue
        standard = callee.startswith("std::")
        if "::" not in callee and callee not in definitions:
            standard |= name == "qsort" or "usingnamespacestd;" in using or f"usingstd::{name};" in using
        count += int(standard)
    return count


def require_linear_list(root):
    for record in nodes(root, "struct_specifier", "class_specifier"):
        body = record.child_by_field_name("body")
        if body is None:
            continue
        fields = [n for n in body.named_children if n.type == "field_declaration"]
        name = text(record.child_by_field_name("name"))
        arrays = [f for f in fields if nodes(f, "array_declarator")]
        pointers = [f for f in fields if nodes(f, "pointer_declarator")]
        scalar = [f for f in fields if not nodes(f, "array_declarator", "pointer_declarator", "function_declarator")]
        # 顺序表：内置数组/非自指针存储 + 整型长度/容量字段。
        lengths = [f for f in scalar if text(f.child_by_field_name("type")) in
                   {"int", "unsigned", "unsigned int", "long", "size_t", "std::size_t"}]
        buffers = arrays + [f for f in pointers if text(f.child_by_field_name("type")) not in {name, f"struct {name}"}]
        if buffers and lengths:
            return 0
        # 链表：自类型指针 + 至少一个数据字段；拒绝常见的双孩子树节点。
        links = [f for f in pointers if text(f.child_by_field_name("type")) in {name, f"struct {name}"}]
        link_names = {text(n) for f in links for n in nodes(f, "field_identifier")}
        if links and len(links) <= 2 and any(f not in links for f in fields):
            if not ({"left", "right"} <= link_names or {"lchild", "rchild"} <= link_names):
                return 0
    return 1


def _comparison(node):
    return any(text(n.child_by_field_name("operator")) in {"<", ">", "<=", ">="}
               for n in nodes(node, "binary_expression"))


def _writes_elements(node):
    return any(nodes(n.child_by_field_name("left"), "subscript_expression")
               for n in nodes(node, "assignment_expression")
               if n.child_by_field_name("left") is not None) or any(
                   c in {"swap", "std::swap"} for c in calls(node))


def _partition(node):
    return bool(nodes(node, *LOOPS) and nodes(node, "subscript_expression")
                and _comparison(node) and _writes_elements(node))


def require_quick_sort(root):
    functions = nodes(root, "function_definition")
    partitions = {function_name(f) for f in functions if _partition(f)}
    for fn in functions:
        name = function_name(fn)
        invoked = calls(fn)
        # 常见递归快排：分区结构（内联或辅助函数）+ 两个子区间递归调用。
        if name and invoked.count(name) >= 2 and nodes(fn, "if_statement"):
            if _partition(fn) or partitions.intersection(invoked):
                return 0
        # 常见显式栈快排：循环分区、压栈与出栈。只识别成员调用栈形式。
        if nodes(fn, *LOOPS) and (_partition(fn) or partitions.intersection(invoked)):
            if any(c.endswith((".push", ".push_back")) for c in invoked) and any(
                    c.endswith((".pop", ".pop_back")) for c in invoked):
                return 0
    return 1


def _heap_adjust(fn):
    # 子结点下标计算 2*i / i*2 / i<<1 + 比较 + 元素交换/写回 + 下沉控制流。
    doubled = any(
        (text(n.child_by_field_name("operator")) == "*" and
         "2" in {compact(n.child_by_field_name("left")), compact(n.child_by_field_name("right"))})
        or (text(n.child_by_field_name("operator")) == "<<" and compact(n.child_by_field_name("right")) == "1")
        for n in nodes(fn, "binary_expression")
    )
    return bool(doubled and _comparison(fn) and nodes(fn, "subscript_expression")
                and _writes_elements(fn) and
                (nodes(fn, *LOOPS) or function_name(fn) in calls(fn)))


def require_heap_sort(root):
    functions = nodes(root, "function_definition")
    adjustments = {function_name(f) for f in functions if _heap_adjust(f)}
    for fn in functions:
        loops = nodes(fn, *LOOPS)
        # 建堆循环和逐个取堆顶循环均调用同一手写调整函数；取堆顶循环交换元素。
        for helper in adjustments - {function_name(fn)}:
            build = [loop for loop in loops if helper in calls(loop)]
            if len(build) >= 2 and any(_writes_elements(loop) for loop in build):
                return 0
        # 完全内联版本需要两个外层阶段，其中至少两个循环有下沉结构。
        if sum(_heap_adjust(loop) for loop in loops) >= 2 and _writes_elements(fn):
            return 0
    return 1


CHECKS = {
    R.TOPIC1_NO_STD_SORT: no_std_sort,
    R.TOPIC1_REQUIRE_SELF_LINEAR_LIST: require_linear_list,
    R.TOPIC1_REQUIRE_SELF_QUICK_SORT: require_quick_sort,
    R.TOPIC1_REQUIRE_SELF_HEAP_SORT: require_heap_sort,
}
