#include <vector>
#include <utility>
#include <limits>

struct Edge { int to, weight; };
using std::vector;

vector<int> shortest(const vector<vector<Edge>>& adj, int start) {
    int n = adj.size();
    vector<int> d(n, std::numeric_limits<int>::max());
    vector<bool> used(n, false);
    d[start] = 0;
    for (int step = 0; step < n; ++step) {
        int u = -1;
        for (int i = 0; i < n; ++i)
            if (!used[i] && (u < 0 || d[i] < d[u])) u = i;
        if (u == -1 || d[u] == std::numeric_limits<int>::max()) break;
        used[u] = true;
        for (auto e : adj[u])
            if (d[u] + e.weight < d[e.to]) d[e.to] = d[u] + e.weight;
    }
    return d;
}

void combine(int a[], int l, int m, int r) {
    vector<int> out;
    int i=l, j=m+1;
    while (i <= m && j <= r) {
        if (a[i] <= a[j]) out.push_back(a[i++]);
        else out.push_back(a[j++]);
    }
    while (i <= m) out.push_back(a[i++]);
    while (j <= r) out.push_back(a[j++]);
    for (int k=l; k<=r; ++k) a[k] = out[k-l];
}

void halves(int a[], int l, int r) {
    if (l >= r) return;
    int m = l + (r-l)/2;
    halves(a,l,m);
    halves(a,m+1,r);
    combine(a,l,m,r);
}

void partition_sort(int a[], int l, int r) {
    if (l >= r) return;
    int i=l, j=r, pivot=a[(l+r)/2];
    while (i<=j) {
        while (a[i]<pivot) ++i;
        while (a[j]>pivot) --j;
        if (i<=j) std::swap(a[i++], a[j--]);
    }
    if (l<j) partition_sort(a,l,j);
    if (i<r) partition_sort(a,i,r);
}
