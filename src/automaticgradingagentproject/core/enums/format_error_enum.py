from enum import Enum


class DocFormatCheck(str, Enum):
    """
    Word 报告格式检查项（解析器能力枚举，教师不可增删，只能启用/禁用并配置扣分）
    """

    LINE_SPACING = "line_spacing"
    # 行间距是否为 1.25 倍

    PAGE_NUMBER_FORMAT = "page_number_format"
    # 页码是否为小五号、Times New Roman、靠右

    FILE_NAMING = "file_naming"
    # 文档文件名是否符合“学号-姓名”命名规则，源码文件名是否符合任务书要求

 