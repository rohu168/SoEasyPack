/*
 * @Author: xmqsvip
 * @Date: 2024-12-07
 * @LastEditTime: 2024-12-15 22:38:08
 */

package main

import (
	"archive/zip"
	"bytes"
	"embed"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"syscall"
	"time"
	"unsafe"
)

//go:embed soeasypack.zip
var embedZip embed.FS
var onefile bool = false
var mainPyCode string = `main_pycode`

func MessageBox(title, message string) {
	msgBox := syscall.MustLoadDLL("user32.dll")
	defer msgBox.Release()
	proc := msgBox.MustFindProc("MessageBoxW")

	// 处理 UTF16PtrFromString 的返回值
	titlePtr, _ := syscall.UTF16PtrFromString(title)
	messagePtr, _ := syscall.UTF16PtrFromString(message)

	proc.Call(
		0,
		uintptr(unsafe.Pointer(messagePtr)),
		uintptr(unsafe.Pointer(titlePtr)),
		0,
	)
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
func createSharedMemory() (syscall.Handle, uintptr) {

	zipData, err := embedZip.ReadFile("soeasypack.zip")
	if err != nil {
		MessageBox("错误", "找不到zipData:"+err.Error())
		return 0, 0
	}

	// 共享内存的大小根据数据大小动态设置
	memSize := len(zipData)
	name := "MySharedMemory"

	// 创建安全属性并允许继承句柄
	securityAttrs := &syscall.SecurityAttributes{
		Length:        uint32(unsafe.Sizeof(syscall.SecurityAttributes{})),
		InheritHandle: 1, // 允许子进程继承句柄
	}

	// 创建共享内存区域，大小为数据的大小
	namePtr, _ := syscall.UTF16PtrFromString(name)
	handle, err := syscall.CreateFileMapping(syscall.InvalidHandle, securityAttrs, syscall.PAGE_READWRITE, 0, uint32(memSize), namePtr)
	if err != nil {
		MessageBox("错误", "创建共享内存失败:"+err.Error())
		return 0, 0
	}
	// defer syscall.CloseHandle(handle)

	// 映射共享内存到当前进程的地址空间
	addr, err := syscall.MapViewOfFile(handle, syscall.FILE_MAP_WRITE, 0, 0, uintptr(memSize))
	if err != nil {
		MessageBox("错误", "映射共享内存到当前进程的地址空间失败:"+err.Error())
		return 0, 0
	}
	// defer syscall.UnmapViewOfFile(addr)

	// 将嵌入的数据写入共享内存
	// 通过切片直接访问共享内存的缓冲区，避免 1024 字节的硬编码
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
			// 创建目录
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
func main() {
	cDir, _ := os.Getwd()
	var currentDir string
	if onefile {
		// 创建临时目录
		var err error
		currentDir, err = os.MkdirTemp("", "soeasypack")
		if err != nil {
			return
		}
		defer os.RemoveAll(currentDir) // 程序退出时删除临时目录

		// 读取嵌入的zip文件内容
		zipData, err := embedZip.ReadFile("rundep.zip")
		if err != nil {
			MessageBox("错误", "读取压缩包数据失败: "+err.Error())
			return
		}

		// 使用bytes.Reader包装zip数据，以提供io.ReaderAt接口
		zipReader := bytes.NewReader(zipData)

		// 解压zip文件到临时目录
		if err := extractZip(zipReader, int64(len(zipData)), currentDir); err != nil {
			MessageBox("错误", "解压数据失败: "+err.Error())
			return
		}
	} else {
		currentDir, _ = os.Getwd()
		currentDir = currentDir + "\\rundep"
	}

	handle, addr := createSharedMemory()
	defer syscall.CloseHandle(handle)
	defer syscall.UnmapViewOfFile(addr)

	os.Setenv("PYTHONHOME", currentDir)
	// 切换当前工作目录
	os.Chdir(currentDir + "\\AppData")

	pyCode := fmt.Sprintf(`
import sys
import marshal
import multiprocessing.shared_memory as shm
import importlib.abc
import importlib.util
import zipfile
from io import BytesIO, BufferedReader
import time

class ZipMemoryLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
	def __init__(self, zip_data):
		self.zip_data = zip_data
		self.zip_file = zipfile.ZipFile(BytesIO(zip_data), 'r')
		self.zip_file_namelist = self.zip_file.namelist()
	
	def find_spec(self, fullname, path, target=None):   
		parts = fullname.split('.')
		base_name = parts[0]
		is_package = False

		# 查找 .pyc 文件或包目录中的 __init__.pyc 文件
		possible_paths = [
			f"{base_name}.pyc",
			f"{base_name}/__init__.pyc"
		]

		if len(parts) > 1:
			# 如果是子模块或子包，构造完整路径
			package_path = '/'.join(parts)
			possible_paths.extend([
				f"{package_path}.pyc",
				f"{package_path}/__init__.pyc"
			])
			is_package = any(p.endswith('/__init__.pyc') for p in possible_paths)

		for path in possible_paths:
			if path in self.zip_file_namelist:
				spec = importlib.util.spec_from_loader(fullname, self, origin=path)
				# 如果是包，则设置 submodule_search_locations
				spec.submodule_search_locations = [f"{base_name}/"] if is_package else None
				return spec

		return None

	def create_module(self, spec):
		# 使用默认行为创建模块
		return None  

	def exec_module(self, module):
		spec = module.__spec__
		origin = spec.origin
		if origin is not None:
			with self.zip_file.open(origin) as source_file:            
				source_file.seek(16)
				code = marshal.load(BufferedReader(source_file))
				exec(code, module.__dict__)

shared_mem = shm.SharedMemory(name="MySharedMemory")
zip_data = shared_mem.buf.tobytes()

# 关闭共享内存
shared_mem.close()
loader = ZipMemoryLoader(zip_data)
sys.meta_path.insert(0, loader)

globals_  = {'__file__': 'main', '__name__': '__main__'}
globals_ = globals().update(globals_ )
# 将十六进制字符串转换回字节序列
pyc_data = bytes.fromhex("%s")
compiled_code = marshal.loads(pyc_data[16:])
exec(compiled_code, globals_)
`, mainPyCode)

	// 加载 python3.dll
	pythonDll, err := syscall.LoadDLL(currentDir + "\\python38.dll")
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
		arg_, _ := syscall.UTF16PtrFromString(arg)
		cArgs = append(cArgs, uintptr(unsafe.Pointer(arg_)))
	}

	// 调用 Py_Main 函数执行 Python 脚本
	argc := len(args)
	argv := uintptr(unsafe.Pointer(&cArgs[0]))
	ret, _, _ := pyMainProc.Call(uintptr(argc), argv)
	if ret != 0 {
		MessageBox("错误", "执行失败,cmd运行run.bat查看报错信息")
	}

	// 确保 Python 环境被正确清理
	finalize, err := pythonDll.FindProc("Py_Finalize")
	if err != nil {
		fmt.Println("失败", err)
	} else {
		finalize.Call()
	}

	// 等待一段时间以确保所有资源被释放
	time.Sleep(time.Second * 3)
	os.Chdir(cDir)
	// 如果是单文件模式，尝试删除临时目录
	pythonDll.Release()
	syscall.CloseHandle(handle)
	syscall.UnmapViewOfFile(addr)
	time.Sleep(time.Second * 3)
	if onefile {
		err = os.RemoveAll(currentDir)
		if err != nil {
			fmt.Println("删除失败", err)
		} else {
			fmt.Println("成功删除临时文件夹")
		}
	}
}
