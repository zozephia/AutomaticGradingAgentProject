"""共享规则名称与 C++ 检查函数的对应关系。"""
from ...enums.ast_rule_enum import AstRuleEnum as R
from . import graph, linear_list, tree

CHECKS = {
    R.TOPIC1_NO_STD_SORT: linear_list.no_std_sort,
    R.TOPIC1_REQUIRE_SELF_LINEAR_LIST: linear_list.require_linear_list,
    R.TOPIC1_REQUIRE_SELF_QUICK_SORT: linear_list.require_quick_sort,
    R.TOPIC1_REQUIRE_SELF_HEAP_SORT: linear_list.require_heap_sort,
    R.TOPIC2_REQUIRE_TERM_STRUCT: tree.require_term,
    R.TOPIC2_REQUIRE_BST_NODE_STRUCT: tree.require_bst,
    R.TOPIC2_REQUIRE_AVL_NODE_STRUCT: tree.require_avl,
    R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE: tree.require_maintenance,
    R.TOPIC2_NO_STD_MAP_AS_CORE: tree.no_map_as_core,
    R.TOPIC3_REQUIRE_ADJACENCY_LIST: graph.require_adjacency_list,
    R.TOPIC3_REQUIRE_SELF_DIJKSTRA: graph.require_dijkstra,
    R.TOPIC3_REQUIRE_SELF_QUICK_SORT: linear_list.require_quick_sort,
    R.TOPIC3_REQUIRE_SELF_MERGE_SORT: graph.require_merge_sort,
    R.TOPIC3_NO_STD_SORT: linear_list.no_std_sort,
}

# 配置和调试入口都接受枚举名及其字符串值。
RULE_BY_NAME = {**R.__members__, **{rule.value: rule for rule in R}}
