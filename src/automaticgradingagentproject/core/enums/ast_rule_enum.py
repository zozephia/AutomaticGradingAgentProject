from enum import Enum


class AstRuleEnum(str, Enum):
    """AST 静态校验规则枚举（教师不可增删，只能启用/禁用并配置扣分）"""

    # ========== 专题一：线性表 + 快速排序 / 堆排序 ==========
    TOPIC1_NO_STD_SORT = "topic1.no_std_sort"
    # 禁止型：禁止直接调用 std::sort / qsort 等系统排序函数

    TOPIC1_REQUIRE_SELF_LINEAR_LIST = "topic1.require_self_linear_list"
    # 要求型：必须自行实现线性表结构（顺序表或链表），不得直接使用 std::vector / std::list 作为核心存储

    TOPIC1_REQUIRE_SELF_QUICK_SORT = "topic1.require_self_quick_sort"
    # 要求型：必须自行实现快速排序（含分区逻辑与递归/迭代调用）

    TOPIC1_REQUIRE_SELF_HEAP_SORT = "topic1.require_self_heap_sort"
    # 要求型：必须自行实现堆排序（含建堆与调整堆逻辑）

    # ========== 专题二：词条结构 + BST / AVL ==========
    TOPIC2_REQUIRE_TERM_STRUCT = "topic2.require_term_struct"
    # 要求型：必须定义词条结构体（含词条 key 与释义/数据字段）

    TOPIC2_REQUIRE_BST_NODE_STRUCT = "topic2.require_bst_node_struct"
    # 要求型：必须定义 BST 节点结构（含左右孩子指针）

    TOPIC2_REQUIRE_AVL_NODE_STRUCT = "topic2.require_avl_node_struct"
    #(可选) 要求型：必须定义 AVL 节点结构（含左右孩子指针与平衡因子/高度字段）

    TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE = "topic2.require_avl_balance_maintenance"
    #(可选) 要求型：AVL 实现必须包含平衡因子维护逻辑（旋转后更新平衡因子/高度）

    TOPIC2_NO_STD_MAP_AS_CORE = "topic2.no_std_map_as_core"
    # 禁止型：禁止直接使用 std::map / std::set 作为 BST/AVL 核心实现替代

    # ========== 专题三：图 + Dijkstra + 排序 ==========
    TOPIC3_REQUIRE_ADJACENCY_LIST = "topic3.require_adjacency_list"
    # 要求型：必须使用邻接表存储图（节点含边表/邻接点集合）

    TOPIC3_REQUIRE_SELF_DIJKSTRA = "topic3.require_self_dijkstra"
    # 要求型：必须自行实现 Dijkstra 算法（含距离数组初始化、松弛、选最小未访问点）

    TOPIC3_REQUIRE_SELF_QUICK_SORT = "topic3.require_self_quick_sort"
    # 要求型：排序逻辑中快速排序必须自行实现

    TOPIC3_REQUIRE_SELF_MERGE_SORT = "topic3.require_self_merge_sort"
    # 要求型：排序逻辑中归并排序必须自行实现

    TOPIC3_NO_STD_SORT = "topic3.no_std_sort"
    # 禁止型：禁止直接调用 std::sort / qsort 等系统排序函数替代自行实现