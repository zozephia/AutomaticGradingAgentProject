# C++ 作业的 AST 静态检查

表中的名称省略了前缀，实际规则值以 `topic1.`、`topic2.` 或 `topic3.` 开头。


| 专题   | 规则                              | 查找的主要证据                                                                                                  |
| -------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 一     | `require_self_linear_list`        | 数组或数据指针与长度字段，或带数据和后继指针的链表节点                                                          |
| 一、三 | `no_std_sort`                     | 直接调用标准排序或堆操作，按调用位置计数                                                                        |
| 一、三 | `require_self_quick_sort`         | 分区的比较和写回，以及分区后的递归或显式栈处理                                                                  |
| 一     | `require_self_heap_sort`          | 子节点下标、调整堆，以及建堆和取顶阶段                                                                          |
| 二     | `require_term_struct`             | 同一结构中有词和释义字段，支持常见字符串及字符数组、指针                                                        |
| 二     | `require_bst_node_struct`         | 同一节点有指向自身类型的左右孩子指针                                                                            |
| 二     | `require_avl_node_struct`         | 左右孩子之外还有整数高度或平衡因子字段                                                                          |
| 二     | `require_avl_balance_maintenance` | 同一旋转中调整孩子链接，并给两个节点更新高度或平衡因子，支持调用更新函数                                        |
| 二     | `no_std_map_as_core`              | 识别有序 map/set 的变量或字段。已有自定义树时只报告名称表明字典用途的存储，常见 visited/seen/cache 辅助变量跳过 |
| 三     | `require_adjacency_list`          | 顶点的邻居集合、按顶点索引的边容器，或顶点首边指针与链式边节点                                                  |
| 三     | `require_self_dijkstra`           | 距离初始化、扫描未访问点取最短距离或使用最小优先队列、条件松弛并写回同一目标距离                                |
| 三     | `require_self_merge_sort`         | 比较两个区间的元素并写入同一输出序列，结合递归分段或迭代倍增区间宽度                                            |

各专题实现位于 [linear_list.py](rules/linear_list.py)、[tree.py](rules/tree.py) 和 [graph.py](rules/graph.py)。测试与三个专题的 C++ 样例都在 [tests/AST](../../tests/AST)。
