from enum import Enum


class SandboxExecutionStatus(str, Enum):
    COMPILE_FAILED = "compile_failed"          
    # 编译失败
    RUNTIME_ERROR = "runtime_error"           
    # 运行崩溃/非零退出
    TIMEOUT = "timeout"                        
    # 超时被杀
    RESOURCE_EXCEEDED = "resource_exceeded"    
    # 内存/CPU/输出超限
    OUTPUT_MISMATCH = "output_mismatch"        
    # 输出与预期不一致
    PASSED = "passed"                          
    # 通过