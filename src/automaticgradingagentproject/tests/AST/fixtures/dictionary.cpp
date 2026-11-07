// ============================================================================
//  基于二叉排序树(BST)的英汉词典查询系统
//  编译: g++ -std=c++17 -O2 -o dict dict.cpp
// ============================================================================
#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <chrono>
#include <random>
#include <algorithm>
#include <numeric>
#include <iomanip>
#include <cmath>

using namespace std;

// ========================= 1. 数据结构定义 =========================

// 词条结构体：word 为关键字（唯一），meaning 为释义
struct Entry {
    string word;
    string meaning;
    Entry() = default;
    Entry(const string& w, const string& m) : word(w), meaning(m) {}
};

// BST 节点：左子树所有 word 小于当前节点，右子树所有 word 大于当前节点
struct BSTNode {
    Entry    entry;
    BSTNode* left;
    BSTNode* right;
    explicit BSTNode(const string& w, const string& m)
        : entry(w, m), left(nullptr), right(nullptr) {}
};

// 节点创建函数：左右孩子初始化为空
BSTNode* createNode(const string& word, const string& meaning) {
    return new BSTNode(word, meaning);
}

// ========================= 2. 插入 =========================
// 返回插入后的树根；isNew = true 表示新插入，false 表示更新了已有词条
BSTNode* insert(BSTNode* root, const string& word, const string& meaning, bool& isNew) {
    if (root == nullptr) {                 // 树空 / 找到空位
        isNew = true;
        return createNode(word, meaning);
    }
    if (word < root->entry.word) {
        root->left  = insert(root->left,  word, meaning, isNew);
    } else if (word > root->entry.word) {
        root->right = insert(root->right, word, meaning, isNew);
    } else {
        root->entry.meaning = meaning;     // 已存在，更新释义
        isNew = false;
    }
    return root;
}

// ========================= 3. 查找 =========================
// 非递归查找：返回 true 表示找到，meaning 输出释义
bool searchBST(BSTNode* root, const string& word, string& meaning) {
    BSTNode* cur = root;
    while (cur) {
        if (word < cur->entry.word)       cur = cur->left;
        else if (word > cur->entry.word)  cur = cur->right;
        else { meaning = cur->entry.meaning; return true; }
    }
    return false;
}

// ========================= 4. 删除 =========================
// removed = true 表示删除成功，oldMeaning 返回被删除词条的释义
BSTNode* deleteBST(BSTNode* root, const string& word, bool& removed, string& oldMeaning) {
    if (root == nullptr) { removed = false; return nullptr; }

    if (word < root->entry.word) {
        root->left  = deleteBST(root->left,  word, removed, oldMeaning);
    } else if (word > root->entry.word) {
        root->right = deleteBST(root->right, word, removed, oldMeaning);
    } else {
        removed    = true;
        oldMeaning = root->entry.meaning;

        // 情况1/2：叶子节点 或 只有一个孩子 —— 用孩子（或 null）替代
        if (root->left == nullptr) {
            BSTNode* r = root->right;
            delete root;
            return r;
        }
        if (root->right == nullptr) {
            BSTNode* l = root->left;
            delete root;
            return l;
        }

        // 情况3：左右孩子都存在 —— 用右子树最小节点（中序后继）替代
        BSTNode* minNode = root->right;
        while (minNode->left) minNode = minNode->left;
        root->entry = minNode->entry;
        bool dummy; string dm;
        root->right = deleteBST(root->right, minNode->entry.word, dummy, dm);
    }
    return root;
}

// ========================= 5. 辅助工具函数 =========================

void destroyTree(BSTNode* root) {
    if (!root) return;
    destroyTree(root->left);
    destroyTree(root->right);
    delete root;
}

int nodeCount(BSTNode* root) {
    return root ? 1 + nodeCount(root->left) + nodeCount(root->right) : 0;
}

int treeHeight(BSTNode* root) {
    if (!root) return 0;
    return 1 + max(treeHeight(root->left), treeHeight(root->right));
}

// 中序遍历：输出所有词条（按 word 升序）
void inOrder(BSTNode* root, vector<Entry>& out) {
    if (!root) return;
    inOrder(root->left, out);
    out.push_back(root->entry);
    inOrder(root->right, out);
}

bool startsWith(const string& s, const string& p) {
    return s.size() >= p.size() && s.compare(0, p.size(), p) == 0;
}

// 前缀（模糊）查找：利用 BST 性质剪枝，只访问可能命中的分支
void prefixSearch(BSTNode* root, const string& prefix, vector<Entry>& res) {
    if (!root) return;
    // 左子树中可能有 <= 当前节点，只要当前节点 > prefix 或以 prefix 开头才需搜左边
    if (root->entry.word > prefix || startsWith(root->entry.word, prefix))
        prefixSearch(root->left, prefix, res);
    if (startsWith(root->entry.word, prefix))
        res.push_back(root->entry);
    // 右子树中可能有更大节点，只要当前节点 < prefix 或以 prefix 开头才需搜右边
    if (root->entry.word < prefix || startsWith(root->entry.word, prefix))
        prefixSearch(root->right, prefix, res);
}

// 树形结构可视化（缩进式）
void printTree(BSTNode* root, const string& prefix, bool isLeft, bool isRoot) {
    if (!root) return;
    cout << prefix;
    if (isRoot) cout << "── ";
    else        cout << (isLeft ? "├── " : "└── ");
    cout << root->entry.word << " : " << root->entry.meaning << "\n";

    string newPrefix = prefix + (isRoot ? "   " : (isLeft ? "│  " : "   "));
    printTree(root->left,  newPrefix, true,  false);
    printTree(root->right, newPrefix, false, false);
}

string trim(const string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

// ========================= 6. 文件批量导入 / 导出 =========================

void loadFromFile(BSTNode*& root, const string& filename) {
    ifstream fin(filename);
    if (!fin) { cout << "  [错误] 无法打开文件: " << filename << "\n"; return; }
    string line; int total = 0, added = 0;
    while (getline(fin, line)) {
        line = trim(line);
        if (line.empty() || line[0] == '#') continue;
        istringstream iss(line);
        string w;
        if (!(iss >> w)) continue;
        string meaning;
        getline(iss, meaning);
        meaning = trim(meaning);
        bool isNew;
        root = insert(root, w, meaning, isNew);
        ++total; if (isNew) ++added;
    }
    cout << "  [OK] 导入完成: 共处理 " << total << " 行，新增 " << added << " 条，"
         << "当前词条总数 " << nodeCount(root) << "\n";
}

void exportToFile(BSTNode* root, const string& filename) {
    ofstream fout(filename);
    if (!fout) { cout << "  [错误] 无法创建文件: " << filename << "\n"; return; }
    vector<Entry> all;
    inOrder(root, all);
    for (auto& e : all) fout << e.word << " " << e.meaning << "\n";
    cout << "  [OK] 已导出 " << all.size() << " 条记录到 " << filename << "\n";
}

// ========================= 7. 交互式字典系统 =========================

void printMenu() {
    cout << "\n╔════════════ 二叉排序树(BST) 词典系统 ════════════╗\n"
         << "║  1. 插入 / 更新词条                              ║\n"
         << "║  2. 查找词条                                     ║\n"
         << "║  3. 删除词条                                     ║\n"
         << "║  4. 显示全部词条（中序遍历）                     ║\n"
         << "║  5. 前缀模糊查找                                 ║\n"
         << "║  6. 打印树结构                                   ║\n"
         << "║  7. 从文件批量导入                               ║\n"
         << "║  8. 导出到文件                                   ║\n"
         << "║  9. 统计信息                                     ║\n"
         << "║  0. 退出                                         ║\n"
         << "╚══════════════════════════════════════════════════╝\n"
         << "请选择: ";
}

void runInteractive() {
    BSTNode* root = nullptr;
    string line;

    while (true) {
        printMenu();
        if (!getline(cin, line)) break;
        line = trim(line);
        if (line.empty()) continue;

        int choice;
        try { choice = stoi(line); }
        catch (...) { cout << "  [错误] 请输入数字 0~9\n"; continue; }

        switch (choice) {
        case 1: {
            string w = trim([] { cout << "  单词: "; string s; getline(cin, s); return s; }());
            if (w.empty()) { cout << "  [错误] 单词不能为空\n"; break; }
            cout << "  释义: ";
            string m; getline(cin, m); m = trim(m);
            bool isNew;
            root = insert(root, w, m, isNew);
            cout << (isNew ? "  [OK] 插入成功\n" : "  [OK] 词条已存在，释义已更新\n");
            break;
        }
        case 2: {
            cout << "  待查单词: ";
            string w; getline(cin, w); w = trim(w);
            string m;
            if (searchBST(root, w, m))
                cout << "  查找结果: " << w << " → " << m << "\n";
            else
                cout << "  未找到单词 \"" << w << "\"\n";
            break;
        }
        case 3: {
            cout << "  待删单词: ";
            string w; getline(cin, w); w = trim(w);
            bool removed; string old;
            root = deleteBST(root, w, removed, old);
            if (removed) cout << "  删除成功: " << w << "（原释义: " << old << "）\n";
            else         cout << "  未找到单词 \"" << w << "\"，删除失败\n";
            break;
        }
        case 4: {
            vector<Entry> all;
            inOrder(root, all);
            if (all.empty()) { cout << "  字典为空\n"; break; }
            cout << "  共 " << all.size() << " 条（按字母升序）:\n";
            cout << "  " << string(50, '-') << "\n";
            for (size_t i = 0; i < all.size(); ++i)
                cout << "  " << setw(4) << i + 1 << ". " << all[i].word
                     << "  →  " << all[i].meaning << "\n";
            break;
        }
        case 5: {
            cout << "  输入前缀: ";
            string p; getline(cin, p); p = trim(p);
            vector<Entry> res;
            prefixSearch(root, p, res);
            if (res.empty()) cout << "  没有以 \"" << p << "\" 开头的单词\n";
            else {
                cout << "  找到 " << res.size() << " 个匹配项:\n";
                for (auto& e : res) cout << "    " << e.word << "  →  " << e.meaning << "\n";
            }
            break;
        }
        case 6:
            if (!root) cout << "  （空树）\n";
            else printTree(root, "", false, true);
            break;
        case 7: {
            cout << "  文件名: ";
            string f; getline(cin, f); f = trim(f);
            loadFromFile(root, f);
            break;
        }
        case 8: {
            cout << "  导出文件名: ";
            string f; getline(cin, f); f = trim(f);
            exportToFile(root, f);
            break;
        }
        case 9: {
            int n = nodeCount(root), h = treeHeight(root);
            double ideal = n > 0 ? (log2(n + 1.0)) : 0;
            cout << "  词条总数 : " << n << "\n"
                 << "  树高度   : " << h << "\n"
                 << "  理想高度 : log2(n+1) ≈ " << fixed << setprecision(2) << ideal << "\n";
            break;
        }
        case 0:
            destroyTree(root);
            cout << "  已释放内存，再见！\n";
            return;
        default:
            cout << "  [错误] 无效选项\n";
        }
    }
    destroyTree(root);
}


// ========================= 8. 主函数 =========================

int main() {
    cout << "欢迎使用基于二叉排序树(BST)的词典查询系统\n";
    runInteractive();
    return 0;
}
