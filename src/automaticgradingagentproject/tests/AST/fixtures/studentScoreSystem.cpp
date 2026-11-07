#include <iostream>
#include <string>
using namespace std;

// 学生结构体
struct Student {
    int id;
    string name;
    int score;
};

#define MAXSIZE 100
struct SqList {
    Student data[MAXSIZE];
    int length; // 当前有效元素个数
};

// 初始化顺序表
void InitList(SqList &L) {
    L.length = 0;
}

// 添加学生
void AddStudent(SqList &L, Student s) {
    if(L.length >= MAXSIZE) return;
    L.data[L.length++] = s;
}

// 打印顺序表全部学生
void PrintList(SqList &L) {
    cout << "学号\t姓名\t成绩\n";
    for(int i = 0; i < L.length; i++) {
        cout << L.data[i].id << "\t" << L.data[i].name << "\t" << L.data[i].score << endl;
    }
}

// 快速排序：按学号升序
void QuickSortById(SqList &L, int l, int r) {
    if(l >= r) return;
    int i = l, j = r;
    Student pivot = L.data[l];
    while(i < j) {
        while(i < j && L.data[j].id >= pivot.id) j--;
        L.data[i] = L.data[j];
        while(i < j && L.data[i].id <= pivot.id) i++;
        L.data[j] = L.data[i];
    }
    L.data[i] = pivot;
    QuickSortById(L, l, i-1);
    QuickSortById(L, i+1, r);
}

// 堆调整：维护小顶堆（堆顶为当前区间内成绩最小者）
void HeapAdjust(SqList &L, int idx, int len) {
    Student tmp = L.data[idx];
    for(int i = 2*idx+1; i < len; i = 2*i+1) {
        // 在左右孩子中选取成绩较小的一个
        if(i+1 < len && L.data[i+1].score < L.data[i].score)
            i++;
        if(L.data[i].score < tmp.score) {
            L.data[idx] = L.data[i];
            idx = i;
        } else break;
    }
    L.data[idx] = tmp;
}

// 堆排序：按成绩降序
// 建小顶堆后，依次将堆顶（当前最小值）交换到序列末尾，
// 使最小值逐个沉到尾部，最终序列即为成绩降序
void HeapSortByScore(SqList &L) {
    int n = L.length;
    for(int i = n/2 -1; i >=0; i--)
        HeapAdjust(L, i, n);
    for(int i = n-1; i>0; i--) {
        swap(L.data[0], L.data[i]);
        HeapAdjust(L, 0, i);
    }
}

int main() {
    SqList L;
    InitList(L);
    AddStudent(L, {1003, "Zhang", 82});
    AddStudent(L, {1001, "Li", 95});
    AddStudent(L, {1005, "Wang", 76});
    AddStudent(L, {1002, "Zhao", 88});
    AddStudent(L, {1004, "Chen", 91});

    cout << "原始数据：\n";
    PrintList(L);

    SqList list1 = L;
    QuickSortById(list1, 0, list1.length-1);
    cout << "\n快速排序（按学号升序）：\n";
    PrintList(list1);

    SqList list2 = L;
    HeapSortByScore(list2);
    cout << "\n堆排序（按成绩降序）：\n";
    PrintList(list2);

    return 0;
}
