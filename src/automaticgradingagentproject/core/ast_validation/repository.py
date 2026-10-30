"""只读接入现有数据库模型；环境变量覆盖仅作用于本模块。"""
import os


def source_path(code_id):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from automaticgradingagentproject.core.database import SessionLocal
    from automaticgradingagentproject.models.marking import Code

    url = os.environ.get("AST_DATABASE_URL")
    engine = create_engine(url) if url else None
    try:
        with Session(engine) if engine is not None else SessionLocal() as session:
            record = session.get(Code, code_id)
            if record is None:
                raise ValueError(f"源码记录不存在：{code_id}")
            return record.source_code
    finally:
        if engine is not None:
            engine.dispose()
