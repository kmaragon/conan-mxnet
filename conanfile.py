from conans import ConanFile, CMake, tools
import os

class MxnetConan(ConanFile):
    name = "mxnet"
    version = "1.1.0"
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
    generators = ("cmake", "virtualbuildenv", "virtualrunenv")

    def requirements(self):
        if self.options.use_openmp:
            self.options["openblas"].USE_OPENMP = True
        self.options["openblas"].NO_LAPACKE = True

        if self.options.use_jemalloc:
            self.requires("jemalloc/5.0.1@ess-dmsc/stable")
        if self.options.use_lapack:
            self.requires("lapack/3.7.1@conan/stable")

        self.requires("openblas/0.2.20@cognitiv/stable")

    def source(self):
        self.run("git clone --recursive --branch v{} https://github.com/apache/incubator-mxnet mxnet".format(self.version))

        tools.replace_in_file("mxnet/CMakeLists.txt", "mxnet_option(USE_OPENCV", '''include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
mxnet_option(USE_OPENCV''')

        tools.replace_in_file("mxnet/Makefile", "CFLAGS = ", "CFLAGS := -I$(BLAS_INCLUDE_PATH) $(CPPFLAGS) $(CFLAGS) ")
        tools.replace_in_file("mxnet/Makefile", "LDFLAGS = ", "LDFLAGS += $(LIBS) ")

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

        options["USE_CUDA"] = "ON" if self.options.use_cuda else "OFF"
        options["USE_CUDNN"] = "ON" if self.options.use_cudnn else "OFF"
        options["USE_OPENCV"] = "ON" if self.options.use_opencv else "OFF"
        options["USE_OPENMP"] = "ON" if self.options.use_openmp else "OFF"
        options["USE_LAPACK"] = "ON" if self.options.use_lapack else "OFF"
        options["USE_OPERATOR_TUNING"] = "ON" if self.options.use_operator_tuning else "OFF"
        options["USE_GPERFTOOLS"] = "ON" if self.options.use_gperftools else "OFF"
        options["USE_JEMALLOC"] = "ON" if self.options.use_jemalloc else "OFF"

        if self.settings.compiler == "Visual Studio":
            cmake = CMake(self)
            cmake.definitions = options
            cmake.configure(source_dir='%s/mxnet' % self.source_folder)
            cmake.build()
        else:
            opts = " ".join(["{0}={1}".format(k, "1" if options[k] == "ON" else "0") for k in options])
            print("Using options '%s'" % opts)
            self.run('. ./activate_build.sh && . ./activate_run.sh && cd mxnet && make -j{0} {1} BLAS_INCLUDE_PATH="{2}" PREFIX="{3} USE_BLAS=openblas"'.format(
                tools.cpu_count() + 2,
                opts,
                os.path.join(self.deps_cpp_info["openblas"].rootpath, "include"),
                self.package_folder))

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
            self.copy(pattern="*.h", dst="include", src="mxnet/nnvm/include")
            self.copy(pattern="*.hpp", dst="include", src="mxnet/nnvm/include")

            # dmlc
            self.copy(pattern="*.h", dst="include", src="mxnet/dmlc-core/include")
            self.copy(pattern="*.hpp", dst="include", src="mxnet/dmlc-core/include")

            if self.options.shared:
                self.copy(pattern="*.dylib", dst="lib", src="mxnet/lib")
                self.copy(pattern="*.so", dst="lib", src="mxnet/lib")
                self.copy(pattern="*.dylib", dst="lib", src="mxnet/nnvm/lib")
                self.copy(pattern="*.so", dst="lib", src="mxnet/nnvm/lib")
                self.copy(pattern="*.dylib", dst="lib", src="mxnet/dmlc-core")
                self.copy(pattern="*.so", dst="lib", src="mxnet/dmlc-core")
            else:
                self.copy(pattern="*.a", dst="lib", src="mxnet/lib")
                self.copy(pattern="*.a", dst="lib", src="mxnet/nnvm/lib")
                self.copy(pattern="*.a", dst="lib", src="mxnet/dmlc-core")

    def package_info(self):
        self.cpp_info.libs = ["mxnet"]
        if self.settings.compiler != "Visual Studio":
            self.cpp_info.libs.append("rt")
        if not self.options.shared:
            self.cpp_info.libs.extend(["nnvm", "dmlc"])
            if self.settings.os == "Macos":
                self.cpp_info.libs.insert(0, "-Wl,-all_load")
                self.cpp_info.libs.append("-Wl,-noall_load")
            elif self.settings.os != "Windows":
                self.cpp_info.libs.insert(0, "-Wl,--whole-archive")
                self.cpp_info.libs.append("-Wl,--no-whole-archive")

        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]
