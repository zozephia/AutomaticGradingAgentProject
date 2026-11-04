from pathlib import Path

import pytest

from automaticgradingagentproject.core.ast_validation import validate_source
from automaticgradingagentproject.core.enums.ast_rule_enum import AstRuleEnum as R

TREE = (Path(__file__).parent / "fixtures/topic2.cpp").read_text()
RULES = [r for r in R if r.value.startswith("topic2.")]


def test_avl_example():
    assert validate_source(TREE, RULES)["ast_error"]["count"] == 0


@pytest.mark.parametrize(("code", "rule", "expected"), [
    ("struct E { char key[20]; char *meaning; };", R.TOPIC2_REQUIRE_TERM_STRUCT, 0),
    ("struct E { int key, meaning; };", R.TOPIC2_REQUIRE_TERM_STRUCT, 1),
    ("struct E { std::string word; }; struct F { std::string meaning; };", R.TOPIC2_REQUIRE_TERM_STRUCT, 1),
    ("struct N { N *left, right; };", R.TOPIC2_REQUIRE_BST_NODE_STRUCT, 1),
    ("struct N { N *left, *right; };", R.TOPIC2_REQUIRE_AVL_NODE_STRUCT, 1),
    (TREE.replace("update(y);", ""), R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE, 1),
    (TREE.replace("x->left = y->right;", ""), R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE, 1),
    (TREE.replace("update(x);", "x->height = height(x->left)+1;").replace("update(y);", "y->height = height(y->left)+1;"), R.TOPIC2_REQUIRE_AVL_BALANCE_MAINTENANCE, 0),
    ("using namespace std; map<int,int> dict; set<int> words;", R.TOPIC2_NO_STD_MAP_AS_CORE, 2),
    ("using Table = std::map<int,int>; Table words;", R.TOPIC2_NO_STD_MAP_AS_CORE, 1),
    ("using Table = std::map<int,int>;", R.TOPIC2_NO_STD_MAP_AS_CORE, 0),
    ("other::map<int,int> d;", R.TOPIC2_NO_STD_MAP_AS_CORE, 0),
    (TREE + "std::set<Node*> visited;", R.TOPIC2_NO_STD_MAP_AS_CORE, 0),
])
def test_tree_rules(code, rule, expected):
    assert validate_source(code, [rule])["ast_error"][rule.value]["count"] == expected
