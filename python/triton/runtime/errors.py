import os
import subprocess
import atexit
import time


class OutOfResources(Exception):
    def __init__(self, required, limit, name):
        self.message = f'out of resource: {name}, '\
                       f'Required: {required}, '\
                       f'Hardware limit: {limit}'
        self.message += '. Reducing block sizes or `num_stages` may help.'
        self.required = required
        self.limit = limit
        self.name = name
        super().__init__(self.message)

    def __reduce__(self):
        # this is necessary to make CompilationError picklable
        return (type(self), (self.required, self.limit, self.name))


def _rename_cuda_core(core_file_path: str):
    # append pid
    core_file_path = core_file_path + "." + str(os.getpid())
    # append timestamp
    core_file_path = core_file_path + "." + str(int(time.time()))
    return core_file_path


def _analyze_illegal_memory_access():
    if os.environ.get("CUDA_ENABLE_COREDUMP_ON_EXCEPTION", "0") == "1":
        if (core_file_path := os.environ["CUDA_COREDUMP_FILE"]) != "" and os.path.exists(core_file_path):
            # Use cuda-gdb to open the core file and print the exception line number
            cmd = f"cuda-gdb -ex 'target cudacore {core_file_path}' -ex 'quit'"
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")
            # Output anything after "CUDA Exception:"
            output = output.split("CUDA Exception:")[-1]
            print(output)


def enable_illegal_memory_analysis(core_file_path: str):
    os.environ["CUDA_ENABLE_COREDUMP_ON_EXCEPTION"] = "1"
    # convert core_file_path to absolute path
    core_file_path = os.path.abspath(_rename_cuda_core(core_file_path))
    os.environ["CUDA_COREDUMP_FILE"] = core_file_path
    # register the atexit hook
    atexit.register(_analyze_illegal_memory_access)


def disable_exception_analysis():
    atexit.unregister(_analyze_illegal_memory_access)
