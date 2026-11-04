from pathlib import Path

import pytest

from automaticgradingagentproject.core.ast_validation import validate_source
from automaticgradingagentproject.core.enums.ast_rule_enum import AstRuleEnum as R

GRAPH = (Path(__file__).parent / "fixtures/topic3.cpp").read_text()
MERGE = GRAPH.split("void partition_sort")[0]
RULES = [r for r in R if r.value.startswith("topic3.")]
ADJ = R.TOPIC3_REQUIRE_ADJACENCY_LIST
DIJKSTRA = R.TOPIC3_REQUIRE_SELF_DIJKSTRA
MERGESORT = R.TOPIC3_REQUIRE_SELF_MERGE_SORT
QUICKSORT = R.TOPIC3_REQUIRE_SELF_QUICK_SORT


def test_graph_example():
    assert validate_source(GRAPH, RULES)["ast_error"]["count"] == 0


@pytest.mark.parametrize(("source", "rule", "expected"), [
    ("int matrix[50][50];", ADJ, 1),
    ("void f(int n){std::vector<std::vector<int>> adj(n,std::vector<int>(n));}", ADJ, 1),
    ("struct City {std::vector<int> neighbors;};", ADJ, 0),
    ("struct Arc{int adjvex; Arc *next;}; struct Vertex{Arc *firstarc;};", ADJ, 0),
    ("std::vector<int> g[64]; void add(int u,int v){g[u].push_back(v);}", ADJ, 0),
    ("void dijkstra(){}", DIJKSTRA, 1),
    (GRAPH.replace("d[start] = 0;", ""), DIJKSTRA, 1),
    (GRAPH.replace("!used[i] && (u < 0 || d[i] < d[u])", "!used[i]"), DIJKSTRA, 1),
    (GRAPH.replace("d[e.to] = d[u] + e.weight", "d[e.to] = 0"), DIJKSTRA, 1),
    (MERGE, QUICKSORT, 1),
    ("void mergeSort(){}", MERGESORT, 1),
    (GRAPH[GRAPH.index("void partition_sort"):], MERGESORT, 1),
    (MERGE.replace("halves(a,m+1,r);", ""), MERGESORT, 1),
    (MERGE.replace("combine(a,l,m,r);", ""), MERGESORT, 1),
    (MERGE.replace("else out.push_back(a[j++]);", "else out.push_back(a[i++]);"), MERGESORT, 1),
    ("void f(){ std::sort(a,b); qsort(a,3,4,cmp); }", R.TOPIC3_NO_STD_SORT, 2),
])
def test_graph_rules(source, rule, expected):
    assert validate_source(source, [rule])["ast_error"][rule.value]["count"] == expected


def test_priority_queue_selection():
    code = """
    void shortest(int n,int src) {
        std::vector<int> d(n, INF);
        std::priority_queue<Pair,std::vector<Pair>,std::greater<Pair>> q;
        q.push({0,src}); d[src]=0;
        while(!q.empty()) {
            auto [cost,u] = q.top(); q.pop();
            if(cost>d[u]) continue;
            for(auto e:adj[u]){
                int candidate = cost + e.weight;
                if(d[e.to]>candidate) {d[e.to]=candidate; q.push({candidate,e.to});}
            }
        }
    }"""
    assert validate_source(code, [DIJKSTRA])["ast_error"]["count"] == 0
