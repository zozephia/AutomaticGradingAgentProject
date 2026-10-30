# AST 静态校验模块

本模块读取 C++ 源码，检查作业要求中的结构和算法特征，不运行学生程序。
AST 可以理解为代码的“结构图”：它能区分函数调用、变量、循环和注释。
本版本使用 Tree-sitter 的具体语法树（CST）命名节点进行结构检查，不是编译器的带类型 AST。

## 文件分工

- `service.py`：公开入口、规则校验和统一计数。
- `repository.py`：根据 `Code.id` 读取 `Code.source_code` 文件路径。
- `parser.py`：解析 C++ 和遍历语法树。
- `enums.py`：保留提示词中的全部规则枚举。
- `rules/linear_list.py`：专题一规则。
- `rules/tree.py`、`rules/graph.py`：后续扩展位置，当前选用对应规则会抛出 `NotImplementedError`。
- `tests/`：独立回归测试，不修改项目数据库。

## 安装与运行

在项目根目录的 PowerShell 中运行（Python 3.13 或以上）：

```powershell
python -m pip install -r src/automaticgradingagentproject/core/ast_validation/requirements.txt
$env:PYTHONPATH = "$PWD/src"
$env:AST_DATABASE_URL = "sqlite:///C:/Users/54275/Desktop/AutomaticGradingAgentProject/app.db"
```

数据库调用还需要项目已有的 SQLAlchemy 依赖。未设置 `AST_DATABASE_URL` 时复用
`core/database.py` 中的 `SessionLocal`；该文件目前写死了 D 盘地址，务必按实际环境配置。
数据库 `source_code` 字段必须保存现存 `.cpp` 文件的绝对路径，编码为 UTF-8（支持 BOM）。

```python
from automaticgradingagentproject.core.ast_validation import AST_validation, AstRuleEnum

result = AST_validation(1, [
    AstRuleEnum.TOPIC1_NO_STD_SORT,
    "topic1.require_self_linear_list",
])
```

输入支持枚举对象、枚举值字符串或枚举名称字符串，重复规则只执行一次。
仅返回选中的规则，未触发的规则 `count=0`，顶级 `count` 为各规则次数之和：

```json
{"ast_error": {"count": 2, "topic1.no_std_sort": {"count": 2}, "topic1.require_self_linear_list": {"count": 0}}}
```

本地调试可调用 `validate_source(source, rules)` 或 `validate_file(absolute_path, rules)`。
空规则列表返回零错误；数据库入口仍验证记录与路径。未知规则、缺失记录、文件读取失败、
编码错误和解析错误会抛出异常，由上层服务处理，不能把这些情况当作学生通过或扣分。

## 检查边界

静态特征只能给出复核线索，不能证明算法正确，也不能证明学生原创。
最终成绩还需结合沙盒运行结果和人工复核。规则的具体识别标准随专题一实现补充。

解析器接口参考：[Tree-sitter Python 官方文档](https://tree-sitter.github.io/py-tree-sitter/)。
