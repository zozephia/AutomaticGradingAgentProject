import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from automaticgradingagentproject.core.ast_validation import (
    AST_validation, AstRuleEnum as R, validate_file, validate_source,
)
from automaticgradingagentproject.core.ast_validation.parser import SourceParseError

FIXTURE = Path(__file__).parent / "fixtures" / "topic1.cpp"
TOPIC1 = [r for r in R if r.value.startswith("topic1.")]


def count(source, rule):
    return validate_source(source, [rule])["ast_error"][rule.value]["count"]


class ValidationTests(unittest.TestCase):
    def test_full_example(self):
        self.assertEqual(validate_file(FIXTURE.resolve(), TOPIC1)["ast_error"]["count"], 0)

    def test_missing_all_requirements(self):
        result = validate_source("int main(){return 0;}", TOPIC1)["ast_error"]
        self.assertEqual(result["count"], 3)
        self.assertEqual(next(iter(result)), "count")

    def test_sort_call_count(self):
        code = "void f(){std::sort(a,a+3); std::stable_sort(a,a+3); ::qsort(a,3,4,cmp); }"
        self.assertEqual(count(code, R.TOPIC1_NO_STD_SORT), 3)

    def test_comments_strings_declarations_are_not_calls(self):
        code = '''// std::sort(a,b);
        const char *s = "std::sort(a,b)";
        void quicksort(); void heapSort();'''
        self.assertEqual(count(code, R.TOPIC1_NO_STD_SORT), 0)
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT), 1)
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT), 1)

    def test_using_and_namespace_alias(self):
        for prefix, call in [("using namespace std;", "sort"),
                             ("using std::sort;", "sort"),
                             ("namespace s=std;", "s::sort"),
                             ("", "std::ranges::sort")]:
            with self.subTest(call=call, prefix=prefix):
                self.assertEqual(count(prefix + "void f(){" + call + "(a,b);}", R.TOPIC1_NO_STD_SORT), 1)

    def test_using_does_not_leak_from_other_function(self):
        self.assertEqual(count("void f(){using namespace std;} void g(){sort(a,b);}", R.TOPIC1_NO_STD_SORT), 0)

    def test_custom_sort_not_banned(self):
        self.assertEqual(count("void sort(int*a,int*b){} void f(){sort(a,b); obj.sort();}", R.TOPIC1_NO_STD_SORT), 0)

    def test_list_structures(self):
        for code in ["struct L{int a[100]; int length;};",
                     "class L{Student *data; unsigned size;};",
                     "struct N{int value; N* next;};",
                     "typedef struct N{int value; struct N* next;} Node;"]:
            with self.subTest(code=code):
                self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_LINEAR_LIST), 0)

    def test_vector_and_empty_struct_are_not_custom_list(self):
        for code in ["struct List{};", "std::vector<int> a;", "struct L{std::vector<int> a; int size;};",
                     "struct N{int v; N*left; N*right;};"]:
            with self.subTest(code=code):
                self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_LINEAR_LIST), 1)

    def test_fake_sort_names_fail(self):
        code = "void quickSort(){} void heapSort(){}"
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT), 1)
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT), 1)

    def test_iterative_quick_sort(self):
        code = FIXTURE.read_text().split("void order_a")[0] + '''
        void iterative(int a[], int n) {
            std::stack<int> s; s.push(0); s.push(n-1);
            while(!s.empty()) {
                int h=s.top(); s.pop(); int l=s.top(); s.pop();
                if(l<h) {int p=divide(a,l,h); s.push(l); s.push(p-1); s.push(p+1); s.push(h);}
            }
        }'''
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_QUICK_SORT), 0)

    def test_heap_adjust_without_sort_driver_fails(self):
        code = FIXTURE.read_text().split("void order_b")[0]
        self.assertEqual(count(code, R.TOPIC1_REQUIRE_SELF_HEAP_SORT), 1)

    def test_duplicates_names_and_values(self):
        self.assertEqual(validate_source("", [R.TOPIC1_NO_STD_SORT, "TOPIC1_NO_STD_SORT", "topic1.no_std_sort"]),
                         {"ast_error": {"count": 0, "topic1.no_std_sort": {"count": 0}}})

    def test_empty_selection(self):
        self.assertEqual(validate_source("not parsed", []), {"ast_error": {"count": 0}})

    def test_invalid_rules(self):
        for rules, error in [(None, TypeError), ("topic1.no_std_sort", TypeError),
                             (["typo"], ValueError), ([R.TOPIC2_REQUIRE_TERM_STRUCT], NotImplementedError)]:
            with self.subTest(rules=rules), self.assertRaises(error):
                validate_source("", rules)

    def test_invalid_syntax_raises_instead_of_deducting(self):
        with self.assertRaises(SourceParseError):
            validate_source("int main( {", TOPIC1)

    def test_bad_paths(self):
        with self.assertRaises(ValueError):
            validate_file("relative.cpp", TOPIC1)
        with self.assertRaises(FileNotFoundError):
            validate_file(FIXTURE.with_name("missing.cpp").resolve(), TOPIC1)

    def test_bad_ids(self):
        for value in [0, -1, True, "1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                AST_validation(value, TOPIC1)

    def test_real_database_adapter(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from automaticgradingagentproject.models.marking import Code
        with tempfile.TemporaryDirectory() as tmp:
            url = "sqlite:///" + str(Path(tmp) / "test.db").replace("\\", "/")
            engine = create_engine(url)
            try:
                Code.__table__.create(engine)
                with Session(engine) as session:
                    session.add(Code(id=1, source_code=str(FIXTURE.resolve()), content_hash="fixture", user_id="test", topic_id=1))
                    session.commit()
                with patch.dict(os.environ, {"AST_DATABASE_URL": url}):
                    self.assertEqual(AST_validation(1, TOPIC1)["ast_error"]["count"], 0)
                    with self.assertRaises(ValueError):
                        AST_validation(2, TOPIC1)
            finally:
                engine.dispose()

    def test_bom_and_invalid_encoding(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.cpp"
            path.write_text("int main(){}", encoding="utf-8-sig")
            self.assertEqual(validate_file(path, [R.TOPIC1_NO_STD_SORT])["ast_error"]["count"], 0)
            path.write_bytes(b"\xff\xfe")
            with self.assertRaises(UnicodeDecodeError):
                validate_file(path, TOPIC1)


if __name__ == "__main__":
    unittest.main()
