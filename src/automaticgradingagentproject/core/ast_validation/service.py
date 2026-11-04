from pathlib import Path

from ..enums.rule_type_enum import RuleTypeEnum
from .parser import parse
from .rules import CHECKS, RULE_BY_NAME


def _selected(items):
    if not isinstance(items, (list, tuple)):
        raise TypeError("list 必须是规则名称列表")
    selected = []
    for item in items:
        try:
            rule = RULE_BY_NAME[item]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"未知 AST 规则：{item!r}") from exc
        if rule not in CHECKS:
            raise NotImplementedError(f"尚未实现：{rule.value}")
        if rule not in selected:
            selected.append(rule)
    return selected


def validate_source(source: str, rules):
    """便于测试和本地调试，不需要数据库。"""
    return _run_checks(source, _selected(rules))


def _run_checks(source, selected):
    if not selected:
        return {RuleTypeEnum.AST_ERROR.value: {"count": 0}}
    root = parse(source)
    result = {"count": 0}
    for rule in selected:
        count = CHECKS[rule](root)
        result[rule.value] = {"count": count}
        result["count"] += count
    return {RuleTypeEnum.AST_ERROR.value: result}


def validate_file(path, rules):
    selected = _selected(rules)
    path = Path(path)
    if not path.is_absolute() or path.suffix.lower() != ".cpp":
        raise ValueError("源码路径必须是 .cpp 文件的绝对路径")
    data = path.read_bytes()
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        source = data.decode("gb18030")
    return _run_checks(source, selected)


def AST_validation(code_id):
    """按提交关联的专题配置选择 AST 规则。"""
    if not isinstance(code_id, int) or isinstance(code_id, bool) or code_id <= 0:
        raise ValueError("code_id 必须是正整数")
    from .repository import submission
    path, rules = submission(code_id)
    return validate_file(path, rules)
