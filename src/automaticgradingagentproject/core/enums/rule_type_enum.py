from enum import Enum


class RuleTypeEnum(str,Enum):
    """
    规则类型枚举项，尽可能可以用一个标识来表示一类错误，在于错误的重构性
    """

    #-----word文档模块-----
    FORMAT_ERROR="format_error"
    #格式校验，标识所有格式校验项
    CHAPTER_MISSING="chapter_missing"
    #章节缺失，文档中明显缺失一块必要章节
    REPORT_CODE_MATCH = "report_code_match"
    # 报告中粘贴的核心代码片段，与上传源代码文件中的代码是否一致




    #-----AST模块-----
    AST_ERROR="ast_error"
    # AST静态检查时出现规则标准未达成


    
    #-----沙盒模块-----
    RUNNING_NO_RESULT="running_no_result"
    # 沙箱运行无法得到结果（包含编译错误，超时，运行崩溃等沙盒非passed状态）
    RUNNING_RESULT_ERROR="running_result_ERROR"
    # 沙箱运行结果出错