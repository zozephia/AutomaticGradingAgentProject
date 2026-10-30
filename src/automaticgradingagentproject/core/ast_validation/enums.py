from enum import StrEnum


class AstRuleEnum(StrEnum):
    TOPIC1_NO_STD_SORT = "topic1.no_std_sort"
    TOPIC1_REQUIRE_SELF_LINEAR_LIST = "topic1.require_self_linear_list"
    TOPIC1_REQUIRE_SELF_QUICK_SORT = "topic1.require_self_quick_sort"
    TOPIC1_REQUIRE_SELF_HEAP_SORT = "topic1.require_self_heap_sort"
    TOPIC2_REQUIRE_TERM_STRUCT = "topic2.require_term_struct"
    TOPIC2_REQUIRE_BST_NODE_STRUCT = "topic2.require_bst_node_struct"
    TOPIC2_REQUIRE_AVL_NODE_STRUCT = "topic2.require_avl_node_struct"
    TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE = "topic2.require_avl_balance_maintenance"
    TOPIC2_NO_STD_MAP_AS_CORE = "topic2.no_std_map_as_core"
    TOPIC3_REQUIRE_ADJACENCY_LIST = "topic3.require_adjacency_list"
    TOPIC3_REQUIRE_SELF_DIJKSTRA = "topic3.require_self_dijkstra"
    TOPIC3_REQUIRE_SELF_QUICK_SORT = "topic3.require_self_quick_sort"
    TOPIC3_REQUIRE_SELF_MERGE_SORT = "topic3.require_self_merge_sort"
    TOPIC3_NO_STD_SORT = "topic3.no_std_sort"
