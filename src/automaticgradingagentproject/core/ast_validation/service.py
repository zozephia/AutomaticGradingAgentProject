from pathlib import Path

from .enums import AstRuleEnum
from .parser import parse


def _selected(items):
    if not isinstance(items, (list, tuple)):
        raise TypeError("list 必须是规则名称列表")
    selected = []
    for item in items:
        try:
            rule = AstRuleEnum[item] if isinstance(item, str) and item in AstRuleEnum.__members__ else AstRuleEnum(item)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"未知 AST 规则：{item!r}") from exc
        if not rule.value.startswith("topic1."):
            raise NotImplementedError(f"尚未实现：{rule.value}")
        if rule not in selected:
            selected.append(rule)
    return selected


def validate_source(source: str, rules):
    """便于测试和本地调试，不需要数据库。"""
    selected = _selected(rules)
    if not selected:
        return {"ast_error": {"count": 0}}
    from .rules.linear_list import CHECKS
    root = parse(source)
    result = {"count": 0}
    for rule in selected:
        count = CHECKS[rule](root)
        result[rule.value] = {"count": count}
        result["count"] += count
    return {"ast_error": result}


def validate_file(path, rules):
    selected = _selected(rules)
    path = Path(path)
    if not path.is_absolute() or path.suffix.lower() != ".cpp":
        raise ValueError("源码路径必须是 .cpp 文件的绝对路径")
    # utf-8-sig 同时支持普通 UTF-8 和带 BOM 的 UTF-8；不静默替换非法字符。
    return validate_source(path.read_text(encoding="utf-8-sig"), selected)


def AST_validation(code_id, list):
    """按数据库 Code.id 查找 .cpp，返回选定规则的错误次数。"""
    selected = _selected(list)
    if not isinstance(code_id, int) or isinstance(code_id, bool) or code_id <= 0:
        raise ValueError("code_id 必须是正整数")
    from .repository import source_path
    return validate_file(source_path(code_id), selected)
