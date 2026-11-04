"""专题二：词条、二叉树节点、旋转维护与有序容器。"""
import re

from ...enums.ast_rule_enum import AstRuleEnum as R
from ..parser import nodes, text
from .linear_list import compact, function_name, _visible
from .records import members

LEFT = {"left", "lchild", "leftchild", "lc", "l"}
RIGHT = {"right", "rchild", "rightchild", "rc", "r"}
BALANCE = {"height", "h", "balance", "bf", "balancefactor", "balance_factor", "factor"}


def require_term(root):
    keys = {"word", "key", "term", "keyword", "english"}
    values = {"meaning", "definition", "description", "value", "data", "translation", "explanation", "chinese"}
    for _, fields in members(root):
        strings = {name for name, (typ, decl) in fields.items()
                   if typ.endswith("string") or (typ == "char" and decl.type in {"array_declarator", "pointer_declarator"})}
        if keys & strings and values & strings:
            return 0
    return 1


def _tree_nodes(root):
    for name, fields in members(root):
        links = {key for key, (typ, decl) in fields.items()
                 if typ.removeprefix("struct ") == name and decl.type == "pointer_declarator"}
        if LEFT & links and RIGHT & links:
            yield fields


def require_bst(root):
    return int(not any(_tree_nodes(root)))


def require_avl(root):
    for fields in _tree_nodes(root):
        if any(fields[key][0] in {"int", "short", "long", "unsigned", "signed char", "int8_t"}
               for key in BALANCE.intersection(fields)):
            return 0
    return 1


def _member(expr):
    if expr is None or expr.type != "field_expression":
        return "", ""
    return compact(expr.child_by_field_name("argument")), text(expr.child_by_field_name("field")).lower()


def require_maintenance(root):
    functions = nodes(root, "function_definition")
    updaters = set()
    for fn in functions:
        for write in nodes(fn, "assignment_expression"):
            if _member(write.child_by_field_name("left"))[1] in BALANCE:
                updaters.add(function_name(fn))
                break
    for fn in functions:
        writes = nodes(fn, "assignment_expression")
        for reverse in writes:
            upper, side = _member(reverse.child_by_field_name("left"))
            lower = compact(reverse.child_by_field_name("right"))
            opposite = LEFT if side in RIGHT else RIGHT if side in LEFT else set()
            if not opposite or not lower.isidentifier() or lower == upper:
                continue
            # 典型旋转：x->right = y->left; y->left = x（也支持先存下中间子树）。
            detached = any(_member(w.child_by_field_name("left"))[0] == lower
                           and _member(w.child_by_field_name("left"))[1] in opposite
                           for w in writes)
            if not detached:
                continue
            updated = {owner for w in writes if w.start_byte > reverse.start_byte
                       for owner, field in [_member(w.child_by_field_name("left"))] if field in BALANCE}
            for call in nodes(fn, "call_expression"):
                if call.start_byte > reverse.start_byte and compact(call.child_by_field_name("function")) in updaters:
                    updated.update(compact(arg) for arg in call.child_by_field_name("arguments").named_children)
            if {lower, upper} <= updated:
                return 0
    return 1


def no_map_as_core(root):
    directives = nodes(root, "using_declaration", "namespace_alias_definition")
    aliases = nodes(root, "alias_declaration", "type_definition")
    custom_tree = any(_tree_nodes(root))
    count = 0
    for decl in nodes(root, "declaration", "field_declaration"):
        typ = compact(decl.child_by_field_name("type"))
        site = decl
        for alias in reversed(aliases):
            name = alias.child_by_field_name("name") or alias.child_by_field_name("declarator")
            if typ == text(name) and _visible(alias, site):
                typ = compact(alias.child_by_field_name("type"))
                site = alias
        imports = {compact(d) for d in directives if _visible(d, site)}
        for directive in imports:
            match = re.fullmatch(r"namespace(\w+)=std;", directive)
            if match:
                typ = typ.removeprefix("::").replace(match[1] + "::", "std::", 1) if typ.startswith(match[1] + "::") else typ
        match = re.match(r"^(?:::)?(std::)?(map|set)<", typ)
        if not match or not (match[1] or "usingnamespacestd;" in imports or f"usingstd::{match[2]};" in imports):
            continue
        for var in decl.children_by_field_name("declarator"):
            var = var.child_by_field_name("declarator") if var.type == "init_declarator" else var
            if var.type not in {"identifier", "field_identifier"}:
                continue
            # 有自己的树时仅报告显式命名为字典/词库的存储，避免将 visited 等辅助集合扣分。
            if not custom_tree or re.search("dict|vocab|entries|wordmap|wordset", text(var), re.I):
                count += 1
    return count


CHECKS = {
    R.TOPIC2_REQUIRE_TERM_STRUCT: require_term,
    R.TOPIC2_REQUIRE_BST_NODE_STRUCT: require_bst,
    R.TOPIC2_REQUIRE_AVL_NODE_STRUCT: require_avl,
    R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE: require_maintenance,
    R.TOPIC2_NO_STD_MAP_AS_CORE: no_map_as_core,
}
