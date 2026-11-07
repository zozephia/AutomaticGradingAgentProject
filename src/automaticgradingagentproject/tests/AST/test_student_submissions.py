"""用户真实作业的结构检查与缺陷对照测试。原始样例保持完整。"""
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from automaticgradingagentproject.core.ast_validation import (
    AST_validation, validate_file, validate_source,
)
from automaticgradingagentproject.core.enums.ast_rule_enum import AstRuleEnum as R
from automaticgradingagentproject.models.marking import Code, Rule

FIXTURES = Path(__file__).parent / "fixtures"
SCORE_RULES = [
    R.TOPIC1_NO_STD_SORT,
    R.TOPIC1_REQUIRE_SELF_LINEAR_LIST,
    R.TOPIC1_REQUIRE_SELF_QUICK_SORT,
    R.TOPIC1_REQUIRE_SELF_HEAP_SORT,
]
BST_RULES = [
    R.TOPIC2_REQUIRE_TERM_STRUCT,
    R.TOPIC2_REQUIRE_BST_NODE_STRUCT,
    R.TOPIC2_NO_STD_MAP_AS_CORE,
]
AVL_RULES = [
    R.TOPIC2_REQUIRE_AVL_NODE_STRUCT,
    R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE,
]


def passing_result(rules):
    return {"ast_error": {"count": 0, **{rule.value: {"count": 0} for rule in rules}}}


@pytest.mark.parametrize(("filename", "rules"), [
    ("studentScoreSystem.cpp", SCORE_RULES),
    ("dictionary.cpp", BST_RULES),
])
def test_original_submission_passes_its_requirements(filename, rules):
    assert validate_file((FIXTURES / filename).resolve(), rules) == passing_result(rules)


def test_bst_submission_reports_both_optional_avl_requirements():
    expected = passing_result(BST_RULES)["ast_error"]
    expected["count"] = 2
    expected.update({rule.value: {"count": 1} for rule in AVL_RULES})
    assert validate_file(
        (FIXTURES / "dictionary.cpp").resolve(), BST_RULES + AVL_RULES,
    ) == {"ast_error": expected}


@pytest.mark.parametrize(("function", "next_function", "missing_rule"), [
    ("QuickSortById", "HeapAdjust", R.TOPIC1_REQUIRE_SELF_QUICK_SORT),
    ("HeapAdjust", "HeapSortByScore", R.TOPIC1_REQUIRE_SELF_HEAP_SORT),
])
def test_empty_sort_body_is_detected(function, next_function, missing_rule):
    source = (FIXTURES / "studentScoreSystem.cpp").read_text(encoding="utf-8-sig")
    start = source.index(f"void {function}(")
    body = source.index("{", start)
    end = source.index(f"void {next_function}(", body)
    # 仅在内存副本里清空实现，保留函数签名和调用，验证检查不只认函数名。
    modified = source[:body] + "{}\n" + source[end:]
    expected = passing_result(SCORE_RULES)["ast_error"]
    expected["count"] = 1
    expected[missing_rule.value]["count"] = 1
    assert validate_source(modified, SCORE_RULES) == {"ast_error": expected}


def test_standard_sort_replacement_is_detected():
    source = (FIXTURES / "studentScoreSystem.cpp").read_text(encoding="utf-8-sig")
    call = "QuickSortById(list1, 0, list1.length-1);"
    assert source.count(call) == 1
    modified = source.replace(
        call,
        "std::sort(list1.data, list1.data + list1.length, "
        "[](const Student& a, const Student& b) { return a.id < b.id; });",
    )
    modified = "#include <algorithm>\n" + modified
    expected = passing_result(SCORE_RULES)["ast_error"]
    expected["count"] = 1
    expected[R.TOPIC1_NO_STD_SORT.value]["count"] = 1
    assert validate_source(modified, SCORE_RULES) == {"ast_error": expected}


def test_real_submissions_through_database_entry(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'submissions.db').as_posix()}"
    monkeypatch.setenv("AST_DATABASE_URL", url)
    engine = create_engine(url)
    try:
        Code.__table__.create(engine)
        Rule.__table__.create(engine)
        with Session(engine) as session:
            for code_id, topic_id, filename, rules in [
                (1, 81, "studentScoreSystem.cpp", SCORE_RULES),
                (2, 92, "dictionary.cpp", BST_RULES),
            ]:
                session.add(Code(
                    id=code_id, source_code=str((FIXTURES / filename).resolve()),
                    content_hash=filename, user_id="fixture", topic_id=topic_id,
                ))
                session.add_all(Rule(name=rule.value, weight=1, topic_id=topic_id) for rule in rules)
            session.commit()
        assert AST_validation(1) == passing_result(SCORE_RULES)
        assert AST_validation(2) == passing_result(BST_RULES)

        # 同一份 BST 提交，仅在配置启用 AVL 后报告这两项缺失。
        with Session(engine) as session:
            session.add_all(Rule(name=rule.value, weight=1, topic_id=92) for rule in AVL_RULES)
            session.commit()
        expected = passing_result(BST_RULES)["ast_error"]
        expected["count"] = 2
        expected.update({rule.value: {"count": 1} for rule in AVL_RULES})
        assert AST_validation(2) == {"ast_error": expected}
    finally:
        engine.dispose()
