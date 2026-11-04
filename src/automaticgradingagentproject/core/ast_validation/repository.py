"""读取源码路径及该提交所属专题配置的 AST 规则。"""
import os
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ...models.marking import Code, Rule
from .rules import RULE_BY_NAME


def _read_submission(session, code_id):
    record = session.get(Code, code_id)
    if record is None:
        raise ValueError(f"源码记录不存在：{code_id}")
    names = session.scalars(select(Rule.name).where(Rule.topic_id == record.topic_id).order_by(Rule.id))
    rules = []
    for name in names:
        if name in RULE_BY_NAME:
            rules.append(RULE_BY_NAME[name])
        elif name.startswith(("topic1.", "topic2.", "topic3.", "TOPIC1_", "TOPIC2_", "TOPIC3_")):
            raise ValueError(f"专题配置了未知 AST 规则：{name}")
        # 同一个专题也可配置文档和沙盒规则。
    return record.source_code, rules


def submission(code_id):
    url = os.environ.get("AST_DATABASE_URL")
    engine = create_engine(url) if url else None
    try:
        with Session(engine) if engine is not None else SessionLocal() as session:
            db_url = session.get_bind().url
            if db_url.get_backend_name() == "sqlite" and db_url.database not in (None, "", ":memory:"):
                if not db_url.query.get("uri") and not Path(db_url.database).is_file():
                    raise FileNotFoundError(f"数据库不存在：{db_url.database}")
            return _read_submission(session, code_id)
    finally:
        if engine is not None:
            engine.dispose()
