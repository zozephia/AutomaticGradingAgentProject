"""按 C++ 字段声明枚举成员，保留逗号声明中每个成员自己的指针/数组修饰。"""
from ..parser import nodes, text


def members(root):
    for record in nodes(root, "class_specifier", "struct_specifier"):
        body = record.child_by_field_name("body")
        if body is None:
            continue
        fields = {}
        for field in body.named_children:
            if field.type != "field_declaration":
                continue
            typ = text(field.child_by_field_name("type"))
            for decl in field.children_by_field_name("declarator"):
                ident = decl
                while ident is not None and ident.type != "field_identifier":
                    if ident.type == "function_declarator":
                        break
                    ident = ident.child_by_field_name("declarator")
                if ident is not None and ident.type == "field_identifier":
                    fields[text(ident).lower()] = (typ, decl)
        yield text(record.child_by_field_name("name")), fields
