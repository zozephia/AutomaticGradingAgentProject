from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from automaticgradingagentproject.core.ast_validation import AST_validation
from automaticgradingagentproject.core.enums.ast_rule_enum import AstRuleEnum as R
from automaticgradingagentproject.models.marking import Code, Rule


def test_configured_rules_follow_submission_topic(tmp_path, monkeypatch):
    url = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    monkeypatch.setenv("AST_DATABASE_URL", url)
    engine = create_engine(url)
    path = Path(__file__).parent / "fixtures/topic1.cpp"
    try:
        Code.__table__.create(engine)
        Rule.__table__.create(engine)
        with Session(engine) as db:
            for i, topic in enumerate([82, 19], start=1):
                db.add(Code(id=i, source_code=str(path.resolve()), content_hash=str(i), user_id="test", topic_id=topic))
            for name in [R.TOPIC1_NO_STD_SORT.name, R.TOPIC1_NO_STD_SORT.value, "format_error"]:
                db.add(Rule(name=name, weight=1, topic_id=82))
            db.commit()
        assert AST_validation(1) == {"ast_error": {"count": 0, R.TOPIC1_NO_STD_SORT.value: {"count": 0}}}
        assert AST_validation(2) == {"ast_error": {"count": 0}}
        with pytest.raises(ValueError, match="源码记录不存在"):
            AST_validation(3)
    finally:
        engine.dispose()


def test_missing_database_stays_absent(tmp_path, monkeypatch):
    path = tmp_path / "app.db"
    monkeypatch.setenv("AST_DATABASE_URL", f"sqlite:///{path.as_posix()}")
    with pytest.raises(FileNotFoundError):
        AST_validation(1)
    assert not path.exists()
