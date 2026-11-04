#include <algorithm>
#include <string>

struct Entry { std::string word, meaning; };
struct Node {
    Entry entry;
    Node *left, *right;
    int height;
};

int height(Node *n) { return n ? n->height : 0; }
void update(Node *n) {
    n->height = 1 + std::max(height(n->left), height(n->right));
}

Node *rotate_right(Node *x) {
    Node *y = x->left;
    x->left = y->right;
    y->right = x;
    update(x);
    update(y);
    return y;
}
