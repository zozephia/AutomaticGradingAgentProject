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
最终成绩还需结合沙盒运行结果和人工复核。

| 规则 | 当前识别标准 | count 含义 |
| --- | --- | --- |
| `topic1.no_std_sort` | 调用 `std::sort`、`stable_sort`、`partial_sort`、`partial_sort_copy`、`nth_element`、`qsort` 或标准库堆操作；支持直接限定名、常见 using 和 namespace 别名 | 源码调用位置数量，同一循环内的一次调用记 1 |
| `topic1.require_self_linear_list` | struct/class 内有数组或数据指针与整数长度字段，或有自类型指针与数据字段的链表节点 | 未找到结构记 1，否则 0 |
| `topic1.require_self_quick_sort` | 循环、元素比较和写回构成分区特征；主函数带条件分支和两次自身调用，或循环分区配合栈 push/pop | 未找到特征记 1，否则 0 |
| `topic1.require_self_heap_sort` | 手写调整函数含二倍子节点索引、元素比较、写回和下沉；两个循环调用该函数完成建堆和取顶，或常见内联形式 | 未找到特征记 1，否则 0 |

识别不依赖函数必须叫 `quickSort` 或 `heapSort`，但目前辅助函数关联依靠名称，
未做编译器级的重载、模板实例化和类型解析。只写一个同名空函数不能通过。
注释和字符串里的 `std::sort` 不算调用。

具体限制请在接入评分时考虑：

- 只读取数据库指向的单个 `.cpp`，不递归读取 `.h` 或其他源文件，不展开宏、处理条件编译或解析函数指针。
  因而头文件中的自定义结构可能漏报，未启用的条件编译分支也可能参与检查。
- 结构存在不代表它是程序实际使用的核心存储；保留一个未使用的自定义结构、实际使用 vector 的程序可能通过。
  普通 vector/list 容器本身不满足自定义结构要求；辅助容器不会被一概禁止。
- 双向链表和树的结构可能相似，目前只排除常见 `left/right`、`lchild/rchild` 树节点命名。
  纯全局数组实现、智能指针链表、长度类型别名等不在当前结构模板覆盖内。
- 排序检查是特征匹配，不分析数据流和调用可达性。其他算法若具有类似特征可能误判为通过；
  尾递归快排、数组模拟栈、复杂分层建堆、成员函数互调等写法可能误判为缺失。
- 标准库检测支持常见直接调用；复杂作用域遮蔽、别名链、间接调用仍可能误报或漏报。
- Tree-sitter 检查语法结构，不做类型检查；能解析不代表能编译。
  语法错误抛出 `SourceParseError`，不会映射到 `ast_error` 扣分。

任务书专题一要求至少两种排序，快排和堆排是举例；本模块遵照传入列表单独启用规则，
没有自动启用所有规则，也不检查学生姓名、成绩字段或排序结果是否正确。

## 测试和阅读顺序

```powershell
$env:PYTHONPATH = "$PWD/src"
python -m unittest discover -s src/automaticgradingagentproject/core/ast_validation/tests -v
```

20 项测试覆盖规则正反例、枚举选择、计数、注释字符串、别名作用域、语法错误、路径、
编码以及真实临时 SQLite 数据库。测试不会修改项目 `app.db`。
本次在 Python 3.14、Tree-sitter 0.26.0、tree-sitter-cpp 0.23.4、SQLAlchemy 2.0.51 环境验证。
项目主依赖声明的 SQLAlchemy 版本较高，本次未安装或验证整套应用依赖。

建议先看 `tests/fixtures/topic1.cpp`，这是带顺序表、两种手写排序的最小示例；
再看 `service.py` 的返回结构，最后阅读 `rules/linear_list.py` 中各项判断。
增加树或图规则时，在对应规则文件实现函数，接入规则注册表，并调整 `service.py` 中的
已实现规则筛选，同时补充正反例测试。不要让未实现的规则默认返回通过。

解析器接口参考：[Tree-sitter Python 官方文档](https://tree-sitter.github.io/py-tree-sitter/)。
