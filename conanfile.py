from conans import ConanFile, CMake, tools
import os

class MxnetConan(ConanFile):
    name = "mxnet"
    version = "1.6.0"
    license = "Apache 2.0"
    url = "https://github.com/kmaragon/conan-mxnet"
    description = "Conan package for the MXNet machine learning library"
    settings = "os", "compiler", "build_type", "arch"
    options = {
            "shared": [True, False],
            "use_cuda": [True, False],
            "use_opencv": [True, False],
            "use_cudnn": [True, False],
            "use_openmp": [True, False],
            "use_lapack": [True, False],
            "use_operator_tuning": [True, False],
            "use_gperftools": [True, False],
            "use_jemalloc": [True, False]
            }

    default_options = (
        "shared=False",
        "use_cuda=False",
        "use_opencv=False",
        "use_cudnn=False",
        "use_openmp=False",
        "use_lapack=True",
        "use_operator_tuning=False",
        "use_gperftools=False",
        "use_jemalloc=False"
    )
    generators = ("cmake", "cmake_find_package")

    def requirements(self):
        self.requires("openblas/0.3.10")
        if self.options.use_lapack:
            self.options["openblas"].build_lapack = True
        else:
            self.options["openblas"].build_lapack = False
        self.options["openblas"].shared = self.options.shared

        if self.options.use_jemalloc:
            self.requires("jemalloc/5.2.1")
            self.options["jemalloc"].shared = self.options.shared
        if self.options.use_lapack:
            self.requires("lapack/3.7.1@conan/stable")
            self.options["lapack"].shared = self.options.shared

    def source(self):
        tools.get('https://github.com/apache/incubator-mxnet/releases/download/{0}/apache-mxnet-src-{0}-incubating.tar.gz'.format(self.version))
        os.rename('apache-mxnet-src-{}-incubating'.format(self.version), 'mxnet')

        # conan will take care of this
        tools.replace_in_file(os.path.join("mxnet", "CMakeLists.txt"), "list(APPEND mxnet_LINKER_LIBS lapack)", "")

        # skip unit tests
        tools.replace_in_file(os.path.join("mxnet", "3rdparty", "dmlc-core", "CMakeLists.txt"), "add_subdirectory(test/unittest)", "")
        tools.replace_in_file(os.path.join("mxnet", "CMakeLists.txt"), 'add_subdirectory(tests)', '')

        # Please tell me mxnet 2.0's build won't be such a pile of crap
        tools.replace_in_file(os.path.join("mxnet", "CMakeLists.txt"), "set(CMAKE_MODULE_PATH ", '''
        set(CMAKE_MODULE_PATH ${CMAKE_BINARY_DIR})
        # set(CMAKE_MODULE_PATH ''')
        tools.replace_in_file(os.path.join("mxnet", "cmake", "ChooseBlas.cmake"), "include_directories(SYSTEM ${OpenBLAS_INCLUDE_DIR})", "include_directories(SYSTEM ${OpenBLAS_INCLUDE_DIR}/openblas)")
        tools.replace_in_file(os.path.join("mxnet", "cmake", "ChooseBlas.cmake"), "list(APPEND mshadow_LINKER_LIBS ${OpenBLAS_LIB})", "list(APPEND mshadow_LINKER_LIBS ${OpenBLAS_LIBRARIES})")

    def build(self):
        options = {}

        options["USE_OLDCMAKECUDA"] = "OFF"
        options["USE_MKL_IF_AVAILABLE"] = "OFF" # leave this off until intel does a better license
        options["USE_MKL_EXPERIMENTAL"] = "OFF" # "
        options["USE_MKLML_MKL"] = "OFF" # "
        options["USE_PROFILER"] = "OFF"
        options["USE_DIST_KVSTORE"] = "OFF"
        options["USE_PLUGINS_WARPCTC"] = "OFF"
        options["USE_CPP_PACKAGE"] = "ON"
        options["BUILD_CPP_EXAMPLES"] = "OFF"
        options["DO_NOT_BUILD_EXAMPLES"] = "ON"

        options["USE_CUDA"] = "ON" if self.options.use_cuda else "OFF"
        options["USE_CUDNN"] = "ON" if self.options.use_cudnn else "OFF"
        options["USE_OPENCV"] = "ON" if self.options.use_opencv else "OFF"
        options["USE_OPENMP"] = "ON" if self.options.use_openmp else "OFF"
        options["USE_LAPACK"] = "ON" if self.options.use_lapack else "OFF"
        options["USE_OPERATOR_TUNING"] = "ON" if self.options.use_operator_tuning else "OFF"
        options["USE_GPERFTOOLS"] = "ON" if self.options.use_gperftools else "OFF"
        options["USE_JEMALLOC"] = "ON" if self.options.use_jemalloc else "OFF"

        cmake = CMake(self)
        cmake.definitions = options
        cmake.configure(source_folder = os.path.join(self.source_folder, 'mxnet'))
        if self.options.shared:
            cmake.build(target='mxnet')
        else:
            cmake.build(target='mxnet_static')
        cmake.build(target='cpp_package_op_h')

    def package(self):
        if self.settings.compiler == "Visual Studio":
            cmake = CMake(self)
            cmake.install()
        else:
            self.copy(pattern="*.h", dst="include", src="mxnet/include")

            # cpp package
            self.copy(pattern="*.h", dst="include", src="mxnet/cpp-package/include")
            self.copy(pattern="*.hpp", dst="include", src="mxnet/cpp-package/include")

            # nnvm
            self.copy(pattern="*.h", dst="include", src="mxnet/3rdparty/nnvm/include")
            self.copy(pattern="*.hpp", dst="include", src="mxnet/3rdparty/nnvm/include")

            # dmlc
            self.copy(pattern="*.h", dst="include", src="mxnet/3rdparty/dmlc-core/include")
            self.copy(pattern="*.hpp", dst="include", src="mxnet/3rdparty/dmlc-core/include")

            if self.options.shared:
                self.copy(pattern="*.dylib", dst="lib", src=".")
                self.copy(pattern="*.so", dst="lib", src="lib")
                #self.copy(pattern="*.dylib", dst="lib", src="mxnet/3rdparty/nnvm/lib")
                #self.copy(pattern="*.dylib", dst="lib", src="mxnet/3rdparty/nnvm/lib")
                #self.copy(pattern="*.so", dst="lib", src="mxnet/3rdparty/nnvm/lib")
                self.copy(pattern="*.dylib", dst="lib", src="3rdparty/dmlc-core")
                self.copy(pattern="*.so", dst="lib", src="3rdparty/dmlc-core")
            else:
                self.copy(pattern="*.a", dst="lib", src=".")
                self.copy(pattern="*.a", dst="lib", src="lib")
                #self.copy(pattern="*.a", dst="lib", src="mxnet/3rdparty/nnvm/lib")
                self.copy(pattern="*.a", dst="lib", src="3rdparty/dmlc-core")

    def package_info(self):
        self.cpp_info.libs = ["mxnet", "dmlc"]
        if self.settings.compiler != "Visual Studio":
            self.cpp_info.libs.append("rt")
        if not self.options.shared:
            # self.cpp_info.libs.extend(["nnvm"])
            if self.settings.os == "Macos":
                self.cpp_info.libs.insert(0, "-Wl,-all_load")
                self.cpp_info.libs.append("-Wl,-noall_load")
            elif self.settings.os != "Windows":
                self.cpp_info.libs.insert(0, "-Wl,--whole-archive")
                self.cpp_info.libs.append("-Wl,--no-whole-archive")

        if self.settings.os != "Windows":
            self.cpp_info.libs.append("dl")

        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]
