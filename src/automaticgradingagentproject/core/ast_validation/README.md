# C++ 作业的 AST 静态检查

`AST_validation(code_id)` 读取一次提交的 C++ 源码，按教师给该专题配置的规则返回错误次数。可以把语法树理解为一张代码结构图。比如注释和真正的函数调用属于不同节点，所以注释里的 `std::sort(a,b)` 不算违规调用。

## 安装和运行

在仓库根目录运行以下命令。项目使用 Python 3.13 或以上，uv 同步锁文件中的解析器、SQLAlchemy 和 pytest。

```powershell
uv sync --locked
uv run pytest -q src/automaticgradingagentproject/core/tests/AST
```

如果手头没有数据库，可以直接体验一条树规则。在仓库根目录运行 `uv run python`，然后执行：

```python
from automaticgradingagentproject.core.ast_validation import validate_source

validate_source("struct N { N *left, *right; };", ["topic2.require_avl_node_struct"])
# {'ast_error': {'count': 1, 'topic2.require_avl_node_struct': {'count': 1}}}
```

这个结构有左右孩子，但缺少高度或平衡因子，所以勾选 AVL 节点检查时会记 1 次。换成 BST 节点检查则记 0 次。

## 项目服务如何调用

```python
from automaticgradingagentproject.core.ast_validation import AST_validation

result = AST_validation(code_id=27)  # 27 为示例，使用实际上传记录的主键
```

1. `repository.py` 从 `source_code` 表按主键读取源码的绝对路径和 `topic_id`。
2. 用同一个 `topic_id` 查询 `rule` 表。数据库专题 ID 可以是任意主键。教师配置的 `Rule.name` 应存共享 AST 枚举值（如 `topic2.require_bst_node_struct`）或枚举成员名。其他模块的规则跳过，重复的 AST 规则只执行一次。当前表结构中，同专题的规则记录即配置项，`weight` 用于评分，检查器只返回次数。
3. `service.py` 读取单个 `.cpp`，优先尝试 UTF-8（含 BOM），其次尝试 GB18030/GBK。所选规则共享一次解析结果。返回字典先列总 `count`，再列每项规则的 `count`。要求型规则缺失记 1，禁止型规则按命中的源码位置计数。
4. 只配置 BST 时，AVL 规则不会出现在返回值中。专题没有配置 AST 规则时，入口仍检查记录、路径和编码，返回 `{"ast_error": {"count": 0}}`。

数据库连接默认使用项目的 `SessionLocal`。本地联调可将 `AST_DATABASE_URL` 指向已有数据库，例如 `sqlite:///C:/path/to/grading.db`。仓库无需包含数据库文件。缺少数据库或源码、编码无法识别、源码语法不能解析时会抛出异常，由上层处理。数据库配置中拼错的已知专题前缀规则也会报错。

本地调试另有 `validate_source(source, rules)`、`validate_file(absolute_path, rules)`，可以显式选择规则。枚举统一定义在 [core/enums/ast_rule_enum.py](../enums/ast_rule_enum.py)。要看某条规则具体执行哪个函数，查 [rules/__init__.py](rules/__init__.py) 的 `CHECKS` 表即可。

## 三个专题检查什么

表中的名称省略了前缀，实际规则值以 `topic1.`、`topic2.` 或 `topic3.` 开头。

| 专题 | 规则 | 查找的主要证据 |
| --- | --- | --- |
| 一 | `require_self_linear_list` | 数组或数据指针与长度字段，或带数据和后继指针的链表节点 |
| 一、三 | `no_std_sort` | 直接调用标准排序或堆操作，按调用位置计数 |
| 一、三 | `require_self_quick_sort` | 分区的比较和写回，以及分区后的递归或显式栈处理 |
| 一 | `require_self_heap_sort` | 子节点下标、调整堆，以及建堆和取顶阶段 |
| 二 | `require_term_struct` | 同一结构中有词和释义字段，支持常见字符串及字符数组、指针 |
| 二 | `require_bst_node_struct` | 同一节点有指向自身类型的左右孩子指针 |
| 二 | `require_avl_node_struct` | 左右孩子之外还有整数高度或平衡因子字段 |
| 二 | `require_avl_balance_maintenance` | 同一旋转中调整孩子链接，并给两个节点更新高度或平衡因子，支持调用更新函数 |
| 二 | `no_std_map_as_core` | 识别有序 map/set 的变量或字段。已有自定义树时只报告名称表明字典用途的存储，常见 visited/seen/cache 辅助变量跳过 |
| 三 | `require_adjacency_list` | 顶点的邻居集合、按顶点索引的边容器，或顶点首边指针与链式边节点 |
| 三 | `require_self_dijkstra` | 距离初始化、扫描未访问点取最短距离或使用最小优先队列、条件松弛并写回同一目标距离 |
| 三 | `require_self_merge_sort` | 比较两个区间的元素并写入同一输出序列，结合递归分段或迭代倍增区间宽度 |

各专题实现位于 [linear_list.py](rules/linear_list.py)、[tree.py](rules/tree.py) 和 [graph.py](rules/graph.py)。测试与三个专题的 C++ 样例都在 [core/tests/AST](../tests/AST)。

## 如何解释结果

检查器使用 Tree-sitter 的语法节点。它检查单个源码文件，没有跨头文件解析、宏展开、完整类型推导或运行时数据流。因此 `count=0` 表示本次选中的检查没有发现问题，算法输出仍由运行测试验证。

- 词条、左右孩子和高度识别使用常见成员名和类型。使用智能指针、类型别名或不同命名的合法实现可能需要人工复核。
- 判断容器是不是核心存储依赖声明及命名。例如某个未使用的树节点定义可能遮蔽实际使用 map 的证据。
- Dijkstra 覆盖常见距离数组、扫描选点和使用 `std::greater` 的优先队列写法。松弛逻辑拆到另一函数、使用自定义队列比较器等变体可能无法识别。归并、快排也只匹配已覆盖的控制流。
- 结果反映源码中的结构，包括可能从未执行的函数。建议遇到有争议的扣分时，对照具体规则和运行结果复核。
