from pathlib import Path
import tempfile
import pytest

from automaticgradingagentproject.core.ast_validation import (
    AST_validation, AstRuleEnum as R, validate_file, validate_source,
)
from automaticgradingagentproject.core.ast_validation.parser import SourceParseError

FIXTURE = Path(__file__).parent / "fixtures" / "topic1.cpp"
TOPIC1 = [r for r in R if r.value.startswith("topic1.")]


def count(source, rule):
    return validate_source(source, [rule])["ast_error"][rule.value]["count"]


class TestValidation:
    def test_full_example(self):
        assert validate_file(FIXTURE.resolve(), TOPIC1)["ast_error"]["count"] == 0

    def test_missing_all_requirements(self):
        result = validate_source("int main(){return 0;}", TOPIC1)["ast_error"]
        assert result["count"] == 3
        assert next(iter(result)) == "count"

    def test_sort_call_count(self):
        code = "void f(){std::sort(a,a+3); std::stable_sort(a,a+3); ::qsort(a,3,4,cmp); }"
        assert count(code, R.TOPIC1_NO_STD_SORT) == 3

    def test_comments_strings_declarations_are_not_calls(self):
        code = '''// std::sort(a,b);
        const char *s = "std::sort(a,b)";
        void quicksort(); void heapSort();'''
        assert count(code, R.TOPIC1_NO_STD_SORT) == 0
        assert count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT) == 1
        assert count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT) == 1

    def test_using_and_namespace_alias(self):
        for prefix, call in [("using namespace std;", "sort"),
                             ("using std::sort;", "sort"),
                             ("namespace s=std;", "s::sort"),
                             ("", "std::ranges::sort")]:
            assert count(prefix + "void f(){" + call + "(a,b);}", R.TOPIC1_NO_STD_SORT) == 1

    def test_using_does_not_leak_from_other_function(self):
        assert count("void f(){using namespace std;} void g(){sort(a,b);}", R.TOPIC1_NO_STD_SORT) == 0

    def test_custom_sort_not_banned(self):
        assert count("void sort(int*a,int*b){} void f(){sort(a,b); obj.sort();}", R.TOPIC1_NO_STD_SORT) == 0

    def test_list_structures(self):
        for code in ["struct L{int a[100]; int length;};",
                     "class L{Student *data; unsigned size;};",
                     "struct N{int value; N* next;};",
                     "typedef struct N{int value; struct N* next;} Node;"]:
            assert count(code, R.TOPIC1_REQUIRE_SELF_LINEAR_LIST) == 0

    def test_vector_and_empty_struct_are_not_custom_list(self):
        for code in ["struct List{};", "std::vector<int> a;", "struct L{std::vector<int> a; int size;};",
                     "struct N{int v; N*left; N*right;};"]:
            assert count(code, R.TOPIC1_REQUIRE_SELF_LINEAR_LIST) == 1

    def test_fake_sort_names_fail(self):
        code = "void quickSort(){} void heapSort(){}"
        assert count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT) == 1
        assert count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT) == 1

    def test_member_function_quick_sort(self):
        out_of_class = '''
        class Sorter {
        public:
            int partition(int a[], int low, int high);
            void quickSort(int a[], int low, int high);
        };
        int Sorter::partition(int a[], int low, int high) {
            int pivot = a[low], i = low, j = high;
            while (i < j) {
                while (i < j && a[j] >= pivot) --j;
                a[i] = a[j];
                while (i < j && a[i] <= pivot) ++i;
                a[j] = a[i];
            }
            a[i] = pivot;
            return i;
        }
        void Sorter::quickSort(int a[], int low, int high) {
            if (low < high) {
                int p = partition(a, low, high);
                quickSort(a, low, p - 1);
                quickSort(a, p + 1, high);
            }
        }'''
        this_calls = '''
        class Sorter {
        public:
            int partition(int a[], int low, int high) {
                int pivot = a[low], i = low, j = high;
                while (i < j) {
                    while (i < j && a[j] >= pivot) --j;
                    a[i] = a[j];
                    while (i < j && a[i] <= pivot) ++i;
                    a[j] = a[i];
                }
                a[i] = pivot;
                return i;
            }
            void quickSort(int a[], int low, int high) {
                if (low < high) {
                    int p = this->partition(a, low, high);
                    this->quickSort(a, low, p - 1);
                    this->quickSort(a, p + 1, high);
                }
            }
        };'''
        for code in (out_of_class, this_calls):
            assert count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT) == 0

    def test_member_function_heap_sort(self):
        code = '''
        class Heap {
        public:
            void sift(int a[], int n, int i);
            void heapSort(int a[], int n);
        };
        void Heap::sift(int a[], int n, int i) {
            int child = 2 * i;
            while (child <= n) {
                if (child + 1 <= n && a[child + 1] > a[child]) ++child;
                if (a[child] <= a[i]) return;
                int t = a[i]; a[i] = a[child]; a[child] = t;
                i = child; child = 2 * i;
            }
        }
        void Heap::heapSort(int a[], int n) {
            for (int i = n / 2; i >= 1; --i) sift(a, n, i);
            for (int i = n; i > 1; --i) { int t = a[1]; a[1] = a[i]; a[i] = t; sift(a, i - 1, 1); }
        }'''
        assert count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT) == 0

    def test_iterative_quick_sort(self):
        code = FIXTURE.read_text().split("void order_a")[0] + '''
        void iterative(int a[], int n) {
            std::stack<int> s; s.push(0); s.push(n-1);
            while(!s.empty()) {
                int h=s.top(); s.pop(); int l=s.top(); s.pop();
                if(l<h) {int p=divide(a,l,h); s.push(l); s.push(p-1); s.push(p+1); s.push(h);}
            }
        }'''
        assert count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT) == 0

    def test_heap_adjust_without_sort_driver_fails(self):
        code = FIXTURE.read_text().split("void order_b")[0]
        assert count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT) == 1

    def test_duplicates_names_and_values(self):
        assert validate_source("", [R.TOPIC1_NO_STD_SORT, "TOPIC1_NO_STD_SORT", "topic1.no_std_sort"]) == {"ast_error": {"count": 0, "topic1.no_std_sort": {"count": 0}}}

    def test_empty_selection(self):
        assert validate_source("not parsed", []) == {"ast_error": {"count": 0}}

    def test_invalid_rules(self):
        for rules, error in [(None, TypeError), ("topic1.no_std_sort", TypeError),
                             (["typo"], ValueError)]:
            with pytest.raises(error):
                validate_source("", rules)

    def test_invalid_syntax_raises_instead_of_deducting(self):
        with pytest.raises(SourceParseError):
            validate_source("int main( {", TOPIC1)

    def test_missing_semicolon_reports_parse_error(self):
        with pytest.raises(SourceParseError, match="第 1 行"):
            validate_source("struct Example {int field};", TOPIC1)

    def test_bad_paths(self):
        with pytest.raises(ValueError):
            validate_file("relative.cpp", TOPIC1)
        with pytest.raises(FileNotFoundError):
            validate_file(FIXTURE.with_name("missing.cpp").resolve(), TOPIC1)

    def test_bad_ids(self):
        for value in [0, -1, True, "1"]:
            with pytest.raises(ValueError):
                AST_validation(value)

    def test_bom_and_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.cpp"
            path.write_text("int main(){}", encoding="utf-8-sig")
            assert validate_file(path, [R.TOPIC1_NO_STD_SORT])["ast_error"]["count"] == 0
            path.write_bytes(b"\xff\xfe")
            with pytest.raises(UnicodeDecodeError):
                validate_file(path, TOPIC1)

    def test_gbk_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gbk.cpp"
            path.write_bytes("// 中文注释\nstruct Node { int value; Node *next; };\n".encode("gb18030"))
            assert validate_file(path, [R.TOPIC1_REQUIRE_SELF_LINEAR_LIST])["ast_error"]["count"] == 0
