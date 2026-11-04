// A small, executable example; names are intentionally unrelated to algorithm names.
struct Sequence { int values[100]; int length; };

void exchange(int &a, int &b) { int t = a; a = b; b = t; }

int divide(int a[], int low, int high) {
    int pivot = a[high], i = low;
    for (int j = low; j < high; ++j) {
        if (a[j] < pivot) {
            int t = a[i]; a[i] = a[j]; a[j] = t;
            ++i;
        }
    }
    int t = a[i]; a[i] = a[high]; a[high] = t;
    return i;
}

void order_a(int a[], int low, int high) {
    if (low < high) {
        int p = divide(a, low, high);
        order_a(a, low, p - 1);
        order_a(a, p + 1, high);
    }
}

void descend(int a[], int n, int i) {
    int largest = i, left = 2 * i + 1, right = 2 * i + 2;
    if (left < n && a[left] > a[largest]) largest = left;
    if (right < n && a[right] > a[largest]) largest = right;
    if (largest != i) {
        int t = a[i]; a[i] = a[largest]; a[largest] = t;
        descend(a, n, largest);
    }
}

void order_b(int a[], int n) {
    for (int i = n / 2 - 1; i >= 0; --i) descend(a, n, i);
    for (int i = n - 1; i > 0; --i) {
        int t = a[0]; a[0] = a[i]; a[i] = t;
        descend(a, i, 0);
    }
}

int main() {
    Sequence s = {{3, 1, 2}, 3};
    order_a(s.values, 0, s.length - 1);
    order_b(s.values, s.length);
    return s.values[0] != 1 || s.values[1] != 2 || s.values[2] != 3;
}
