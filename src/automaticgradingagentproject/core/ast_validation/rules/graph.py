"""专题三：图的表示、最短路及两种手写排序的结构特征。"""
import re

from ...enums.ast_rule_enum import AstRuleEnum as R
from ..parser import nodes, text
from .linear_list import LOOPS, calls, compact, function_name, no_std_sort, require_quick_sort
from .records import members


def require_adjacency_list(root):
    # 邻接点容器的数组 / 嵌套容器，或顶点记录内的边集合。
    lists = r"(?<!\w)(?:vector|list|forward_list|deque)<"
    adjacent = {"adj", "adjlist", "adjacency", "adjacencylist", "neighbors", "neighbours", "edges", "outedges"}
    appended = set()
    for call in nodes(root, "call_expression"):
        callee = call.child_by_field_name("function")
        if text(callee.child_by_field_name("field")) in {"push_back", "emplace_back", "push_front"}:
            receiver = callee.child_by_field_name("argument")
            if receiver.type == "subscript_expression":
                appended.add(compact(receiver.child_by_field_name("argument")).split(".")[-1])
    for decl in nodes(root, "declaration", "field_declaration", "parameter_declaration"):
        typ = compact(decl.child_by_field_name("type"))
        if not re.search(lists, typ):
            continue
        for var in decl.children_by_field_name("declarator"):
            names = nodes(var, "identifier", "field_identifier")
            if not names:
                continue
            name = text(names[0])
            collection = len(re.findall(lists, typ)) >= 2 or var.type == "array_declarator"
            if collection and (name in appended or name.lower() in adjacent):
                # 逐行初始化为定长向量是常见的邻接矩阵。
                if not re.search(lists, compact(var)):
                    return 0
            if decl.type == "field_declaration" and not collection and name.lower() in adjacent:
                return 0
    # 链式邻接表：边结点有终点和后继，顶点/顶点数组持有同类型首边指针。
    records = list(members(root))
    edge_types = {name for name, fields in records if fields.keys() & {"to", "dest", "adjvex", "target", "v"}
                  and any(typ.removeprefix("struct ") == name and decl.type == "pointer_declarator"
                          for typ, decl in fields.values())}
    for _, fields in records:
        for name, (typ, decl) in fields.items():
            if name in {"first", "firstedge", "firstarc", "head", "edges"} and typ.removeprefix("struct ") in edge_types:
                if decl.type == "pointer_declarator":
                    return 0
    return 1


def _indexed(expr):
    if expr is not None and expr.type == "subscript_expression":
        return compact(expr.child_by_field_name("argument"))
    return ""


def _updates(block):
    return [(w.child_by_field_name("left"), w.child_by_field_name("right"))
            for w in nodes(block, "assignment_expression") if text(w.child_by_field_name("operator")) == "="]


def _initialized(fn, dist, before):
    prefix = [w for w in nodes(fn, "assignment_expression") if w.start_byte < before]
    writes = [compact(w.child_by_field_name("right")) for w in prefix
              if _indexed(w.child_by_field_name("left")) == dist]
    if "0" not in writes:
        return False
    if any(value != "0" for value in writes):
        return True
    for call in nodes(fn, "call_expression"):
        if call.start_byte < before and compact(call.child_by_field_name("function")).split("::")[-1] in {"fill", "fill_n", "memset"}:
            if dist in [text(i) for i in nodes(call, "identifier")]:
                return True
    # Tree-sitter 也可能把局部 vector<int> d(n, INF) 解析成函数声明。
    for decl in nodes(fn, "declaration"):
        if decl.start_byte >= before or "vector<" not in compact(decl.child_by_field_name("type")):
            continue
        for var in decl.children_by_field_name("declarator"):
            if compact(var.child_by_field_name("declarator")) != dist:
                continue
            args = var.child_by_field_name("value") or var.child_by_field_name("parameters")
            if args is not None and len(args.named_children) >= 2:
                return True
    return False


def _selects_min(fn, loop, dist, before):
    # 密集图：在松弛之前比较候选距离，并从未访问候选中选点。
    guards = [g for g in nodes(loop, "if_statement") if g.start_byte < before]
    for guard in guards:
        cond = guard.child_by_field_name("condition")
        if any(_indexed(s) == dist for s in nodes(cond, "subscript_expression")):
            if ("!" in compact(cond) or "==false" in compact(cond) or "==0" in compact(cond)) and _updates(guard):
                if any(text(op.child_by_field_name("operator")) in {"<", ">"} for op in nodes(cond, "binary_expression")):
                    return True
    # 稀疏图：同一最小优先队列取队首并出队，随后按距离或访问标记跳过旧记录。
    invoked = set(calls(loop))
    for decl in nodes(fn, "declaration"):
        typ = compact(decl.child_by_field_name("type"))
        if "priority_queue<" in typ and "greater<" in typ:
            name = compact(decl.child_by_field_name("declarator"))
            if {name + ".top", name + ".pop"} <= invoked and any(nodes(g, "continue_statement") for g in guards):
                return True
    return False


def _relaxations(loop):
    for guard in nodes(loop, "if_statement"):
        cond = guard.child_by_field_name("condition")
        for target, value in _updates(guard.child_by_field_name("consequence")):
            dist = _indexed(target)
            if not dist:
                continue
            # 改善条件与实际写回必须针对同一距离和候选值。
            for cmp in nodes(cond, "binary_expression"):
                left, right = compact(cmp.child_by_field_name("left")), compact(cmp.child_by_field_name("right"))
                op = text(cmp.child_by_field_name("operator"))
                if (left, op, right) not in {(compact(target), ">", compact(value)), (compact(value), "<", compact(target))}:
                    continue
                candidates = [value]
                if value.type == "identifier":
                    candidates.extend(init.child_by_field_name("value") for init in nodes(loop, "init_declarator")
                                      if init.start_byte < guard.start_byte
                                      and compact(init.child_by_field_name("declarator")) == text(value))
                if any(expr is not None and expr.type == "binary_expression"
                       and text(expr.child_by_field_name("operator")) == "+" for expr in candidates):
                    yield dist, guard.start_byte


def require_dijkstra(root):
    for fn in nodes(root, "function_definition"):
        for loop in nodes(fn, *LOOPS):
            for dist, before in _relaxations(loop):
                if _initialized(fn, dist, loop.start_byte) and _selects_min(fn, loop, dist, before):
                    return 0
    return 1


def _merges_runs(block):
    # 双游标比较、从两侧写入同一输出序列。限定在同一个归并循环内。
    for loop in nodes(block, *LOOPS):
        for branch in nodes(loop, "if_statement"):
            alt = branch.child_by_field_name("alternative")
            if alt is None:
                continue
            for cmp in nodes(branch.child_by_field_name("condition"), "binary_expression"):
                if text(cmp.child_by_field_name("operator")) not in {"<", "<=", ">", ">="}:
                    continue
                left, right = (nodes(cmp.child_by_field_name(side), "subscript_expression") for side in ("left", "right"))
                if not left or not right or compact(left[0]) == compact(right[0]):
                    continue
                def destinations(arm, source):
                    destinations = set()
                    for target, value in _updates(arm):
                        reads = {compact(n).replace("++", "") for n in nodes(value, "subscript_expression")}
                        if compact(source) in reads and _indexed(target):
                            destinations.add(_indexed(target))
                    for call in nodes(arm, "call_expression"):
                        callee = call.child_by_field_name("function")
                        if text(callee.child_by_field_name("field")) == "push_back":
                            reads = nodes(call.child_by_field_name("arguments"), "subscript_expression")
                            if any(compact(n).replace("++", "") == compact(source) for n in reads):
                                destinations.add(compact(callee.child_by_field_name("argument")))
                    return destinations
                yes = branch.child_by_field_name("consequence")
                if destinations(yes, left[0]) & destinations(alt, right[0]) or destinations(yes, right[0]) & destinations(alt, left[0]):
                    return True
    return False


def require_merge_sort(root):
    functions = nodes(root, "function_definition")
    mergers = {function_name(f) for f in functions if _merges_runs(f)}
    for fn in functions:
        invoked = calls(fn)
        if not (mergers.intersection(invoked) or function_name(fn) in mergers):
            continue
        if invoked.count(function_name(fn)) >= 2:
            return 0
        for loop in nodes(fn, *LOOPS):
            step = compact(loop.child_by_field_name("update"))
            if re.fullmatch(r"(\w+)(?:\*=2|<<=1|=\1\*2|=2\*\1)", step):
                if mergers.intersection(calls(loop)) or _merges_runs(loop):
                    return 0
    return 1


CHECKS = {
    R.TOPIC3_REQUIRE_ADJACENCY_LIST: require_adjacency_list,
    R.TOPIC3_REQUIRE_SELF_DIJKSTRA: require_dijkstra,
    R.TOPIC3_REQUIRE_SELF_QUICK_SORT: require_quick_sort,
    R.TOPIC3_REQUIRE_SELF_MERGE_SORT: require_merge_sort,
    R.TOPIC3_NO_STD_SORT: no_std_sort,
}
