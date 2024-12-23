/*
 * @Author: xmqsvip
 * @Date: 2024-12-15
 * @go version:1.23.4

 */

package main

import (
	"archive/zip"
	"bytes"
	"embed"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"unsafe"
	"windows"
)

//go:embed soeasypack.zip
var embedZip embed.FS
var onefile bool = false
var packmode int = 0
var mainPyCode string = `main_pycode`

func MessageBox(title, message string) {
	user32, _ := windows.LoadDLL("user32.dll")

	defer user32.Release()

	proc := user32.MustFindProc("MessageBoxW")

	titlePtr, _ := windows.UTF16PtrFromString(title)

	messagePtr, _ := windows.UTF16PtrFromString(message)

	proc.Call(0, uintptr(unsafe.Pointer(messagePtr)), uintptr(unsafe.Pointer(titlePtr)), 0x10)
}

func fileExists(filename string) bool {
	_, err := os.Stat(filename)
	if err != nil {
		if os.IsNotExist(err) {
			return false
		}
		return false
	}
	return true
}
func createSharedMemory() (windows.Handle, uintptr) {
	zipData, err := embedZip.ReadFile("soeasypack.zip")
	if err != nil {
		MessageBox("错误", "找不到zipData:"+err.Error())
		return 0, 0
	}

	memSize := len(zipData)
	name := "MySharedMemory"

	securityAttrs := &windows.SecurityAttributes{
		Length:        uint32(unsafe.Sizeof(windows.SecurityAttributes{})),
		InheritHandle: 1,
	}

	namePtr, err := windows.UTF16PtrFromString(name)
	if err != nil {
		MessageBox("错误", "UTF16PtrFromString 错误: "+err.Error())
		return 0, 0
	}

	handle, err := windows.CreateFileMapping(windows.InvalidHandle, securityAttrs, windows.PAGE_READWRITE, 0, uint32(memSize), namePtr)
	if err != nil {
		MessageBox("错误", "创建共享内存失败:"+err.Error())
		return 0, 0
	}

	addr, err := windows.MapViewOfFile(handle, windows.FILE_MAP_WRITE, 0, 0, uintptr(memSize))
	if err != nil {
		windows.CloseHandle(handle)
		MessageBox("错误", "映射共享内存到当前进程的地址空间失败:"+err.Error())
		return 0, 0
	}

	copy((*[1 << 30]byte)(unsafe.Pointer(addr))[:memSize], zipData)
	return handle, addr
}

// / extractZip 解压zip文件到指定目录
func extractZip(zipReader io.ReaderAt, size int64, dest string) error {
	zipR, err := zip.NewReader(zipReader, size)
	if err != nil {
		return err
	}

	for _, f := range zipR.File {
		// 构建文件应该写入的路径
		fpath := filepath.Join(dest, f.Name)

		// 检查文件是否需要解压
		if f.FileInfo().IsDir() {
			os.MkdirAll(fpath, os.ModePerm)
			continue
		}

		// 创建文件所在的目录
		if err = os.MkdirAll(filepath.Dir(fpath), os.ModePerm); err != nil {
			return err
		}

		// 创建文件
		outFile, err := os.OpenFile(fpath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, f.Mode())
		if err != nil {
			return err
		}
		defer outFile.Close()

		rc, err := f.Open()
		if err != nil {
			return err
		}
		defer rc.Close()

		// 复制文件内容
		if _, err = io.Copy(outFile, rc); err != nil {
			return err
		}
	}
	return nil
}

type stderrCapturer struct {
	buf *bytes.Buffer
}

// 实现 io.Writer 的 Write 方法
func (c *stderrCapturer) Write(p []byte) (n int, err error) {
	return c.buf.Write(p)
}
func main() {
	var pyDllPath string
	SEPHOME := os.Getenv("SEPHOME")
	if SEPHOME == "" {
		originDir, _ := os.Getwd()
		os.Setenv("originDir", originDir)
		if onefile {
			// 创建临时目录
			var err error
			currentDir, err := os.MkdirTemp("", "soeasypack")
			if err != nil {
				return
			}
			// 读取嵌入的zip文件内容
			zipData, err := embedZip.ReadFile("rundep.zip")
			if err != nil {
				MessageBox("错误", "读取压缩包数据失败: "+err.Error())
				return
			}

			// 使用bytes.Reader包装zip数据，以提供io.ReaderAt接口
			zipReader := bytes.NewReader(zipData)
			rundepDir := currentDir + "\\rundep"
			// 解压zip文件到临时目录
			if err := extractZip(zipReader, int64(len(zipData)), rundepDir); err != nil {
				MessageBox("错误", "解压数据到临时目录失败: "+err.Error())
				return
			}
			SEPHOME = currentDir
			os.Setenv("SEPHOME", currentDir)
			os.Setenv("PYTHONHOME", SEPHOME+"\\rundep")
			// os.Setenv("ONEFILE", "1")
			pyDllPath = SEPHOME + "\\rundep\\python3.dll"
			os.Setenv("pyDllPath", pyDllPath)
			handle, addr := createSharedMemory()
			defer windows.CloseHandle(handle)
			defer windows.UnmapViewOfFile(addr)
			executable, _ := os.Executable()
			cmd := exec.Command(executable)
			cmd.Stdout = os.Stdout
			cmd.Stderr = os.Stderr
			if err := cmd.Run(); err != nil {
				MessageBox("错误", "启动失败: "+err.Error())
			}
			os.RemoveAll(currentDir) // 程序退出时删除临时目录
			return
		} else {
			currentDir, _ := os.Getwd()
			SEPHOME = currentDir
			os.Setenv("SEPHOME", currentDir)
			os.Setenv("PYTHONHOME", SEPHOME+"\\rundep")
			pyDllPath = SEPHOME + "\\rundep\\python3.dll"
			os.Chdir(SEPHOME + "\\rundep")
			// 轻量打包模式
			if packmode == 2 {
				isExist := fileExists("compiled_pip.txt")
				if !isExist {
					MessageBox("提示", "依赖包不全，将准备自动下载依赖包")
					cmd := exec.Command("cmd", "/c", "python.exe -m ensurepip --upgrade")

					cmd.Stdout = os.Stdout
					cmd.Stderr = os.Stderr
					err := cmd.Run()
					if err != nil {
						MessageBox("提示", "自动下载依赖包失败:"+err.Error())
						os.Exit(1)
					} else {
						cmd := exec.Command("cmd", "/c", "python.exe -m pip install -r AppData\\requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
						cmd.Stdout = os.Stdout
						cmd.Stderr = os.Stderr

						err := cmd.Run()
						if err != nil {
							MessageBox("提示", "安装依赖包失败:"+err.Error())
							os.Exit(1)
						} else {
							f, _ := os.Create("compiled_pip.txt")
							f.Close()
						}
					}

				}

			}
			os.Setenv("pyDllPath", pyDllPath)
			handle, addr := createSharedMemory()
			defer windows.CloseHandle(handle)
			defer windows.UnmapViewOfFile(addr)
		}

	} else {
		pyDllPath = os.Getenv("pyDllPath")
		os.Setenv("isSubProcess", "1")
	}

	pyCode := fmt.Sprintf(`
import sys
import marshal
import zipfile
import importlib.abc
import importlib.util
from io import BytesIO, BufferedReader
from multiprocessing import shared_memory as shm


class ZipMemoryLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def __init__(self, zip_data):
        self.zip_data = zip_data
        self.zip_file = zipfile.ZipFile(BytesIO(zip_data), 'r')
        self.zip_file_namelist = self.zip_file.namelist()

    def find_spec(self, fullname, path, target=None):
        """
        查找模块的规格。支持单模块和嵌套包。
        """
        parts = fullname.split('.')
        package_path = '/'.join(parts)

        # 可能的路径：模块或包的字节码文件
        possible_paths = [
            f"{package_path}.pyc",
            f"{package_path}/__init__.pyc"
        ]

        # 判断是否为包
        is_package = any(p.endswith('/__init__.pyc') for p in possible_paths)

        # 查找模块的路径是否存在于 ZIP 文件中
        for path in possible_paths:
            if path in self.zip_file_namelist:
                spec = importlib.util.spec_from_loader(fullname, self, origin=path)
                if is_package:
                    # 如果是包，设置子模块搜索路径
                    spec.submodule_search_locations = [package_path + '/']
                return spec

        return None

    def create_module(self, spec):
        """
        使用默认行为创建模块。
        """
        return None  # 返回 None，表示使用默认模块创建逻辑

    def exec_module(self, module):
        """
        执行模块代码，将其加载到模块的命名空间中。
        """
        spec = module.__spec__
        origin = spec.origin
        if origin:
            with self.zip_file.open(origin) as source_file:
                # 跳过 pyc 文件头部
                source_file.seek(16)
                code = marshal.load(BufferedReader(source_file))

                # 如果是包，设置 __package__ 和 __path__
                module.__package__ = spec.name if spec.submodule_search_locations else spec.parent
                if spec.submodule_search_locations:
                    module.__path__ = spec.submodule_search_locations

                # 执行模块代码
                exec(code, module.__dict__)


shared_mem = shm.SharedMemory(name="MySharedMemory")
zip_data = shared_mem.buf.tobytes()

shared_mem.close()
loader = ZipMemoryLoader(zip_data)
sys.meta_path.insert(0, loader)
sys.frozen = True
globals_ = {'__file__': 'main', '__name__': '__main__'}
globals_ = globals().update(globals_)
# 将十六进制字符串转换回字节序列
pyc_data = bytes.fromhex("%s")
compiled_code = marshal.loads(pyc_data[16:])
try:
    exec(compiled_code, globals_)
except Exception:
    import ctypes
    import traceback
    e = traceback.format_exc()
    ctypes.windll.user32.MessageBoxW(0, e, "错误", 0x10)
`, mainPyCode)
	// 切换工作目录
	os.Chdir(SEPHOME + "\\rundep\\AppData")
	// 加载 pythonxx.dll
	pythonDll, err := windows.LoadDLL(pyDllPath)
	if err != nil {
		MessageBox("错误", "无法加载 python3.dll: "+err.Error())
		return
	}
	defer pythonDll.Release()

	// 获取 Py_Main 函数的地址
	pyMainProc, err := pythonDll.FindProc("Py_Main")
	if err != nil {
		MessageBox("错误", "无法找到 Py_Main 函数: "+err.Error())
		return
	}

	args := []string{"python", "-c", pyCode}
	args = append(args, os.Args[1:]...)

	// 将命令行参数转换为 C 字符串
	var cArgs []uintptr
	for _, arg := range args {
		arg_, _ := windows.UTF16PtrFromString(arg)
		cArgs = append(cArgs, uintptr(unsafe.Pointer(arg_)))
	}

	// 调用 Py_Main 函数执行 Python 脚本
	argc := len(args)
	argv := uintptr(unsafe.Pointer(&cArgs[0]))
	ret, _, _ := pyMainProc.Call(uintptr(argc), argv)
	if ret != 0 {
		MessageBox("错误", "执行失败, cmd 运行 run.bat 查看报错信息,\n或设置hide_cmd为False重新编译然后控制台运行")
	}
	// 确保 Python 环境被正确清理
	finalize, _ := pythonDll.FindProc("Py_FinalizeEx")
	finalize.Call()
	originDir := os.Getenv("originDir")
	os.Chdir(originDir)
	pythonDll.Release()

	kernel32 := windows.NewLazySystemDLL("kernel32.dll")
	procFreeLibrary := kernel32.NewProc("FreeLibrary")
	procFreeLibrary.Call(uintptr(pythonDll.Handle))
}
