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
            "use_jemalloc": [True, False],
            "use_cpppackage": [True, False]
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
        "use_jemalloc=False",
        "use_cpppackage=True"
    )
    requires = "openblas/0.2.20@cognitiv/stable"
    generators = "cmake"

    def configure(self):
        if self.options.use_openmp:
            self.options["openblas"].USE_OPENMP = True
        self.options["openblas"].NO_LAPACKE = True

        if self.options.use_jemalloc:
            self.requires("jemalloc/5.0.1@ess-dmsc/stable")
        if self.options.use_lapack:
            self.requires("lapack/3.7.1@conan/stable")


    def source(self):
        self.run("git clone --recursive --branch v{} https://github.com/apache/incubator-mxnet mxnet".format(self.version))

        tools.replace_in_file("mxnet/CMakeLists.txt", "mxnet_option(USE_OPENCV", '''include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
mxnet_option(USE_OPENCV''')

    def build(self):
        cmake = CMake(self)
        cmake.definitions["USE_OLDCMAKECUDA"] = "OFF"
        cmake.definitions["USE_MKL_IF_AVAILABLE"] = "OFF" # leave this off until intel does a better license
        cmake.definitions["USE_MKL_EXPERIMENTAL"] = "OFF" # "
        cmake.definitions["USE_MKLML_MKL"] = "OFF" # "
        cmake.definitions["USE_PROFILER"] = "OFF"
        cmake.definitions["USE_DIST_KVSTORE"] = "OFF"
        cmake.definitions["USE_PLUGINS_WARPCTC"] = "OFF"

        cmake.definitions["USE_CUDA"] = "ON" if self.options.use_cuda else "OFF"
        cmake.definitions["USE_CUDNN"] = "ON" if self.options.use_cudnn else "OFF"
        cmake.definitions["USE_OPENCV"] = "ON" if self.options.use_opencv else "OFF"
        cmake.definitions["USE_OPENMP"] = "ON" if self.options.use_openmp else "OFF"
        cmake.definitions["USE_LAPACK"] = "ON" if self.options.use_lapack else "OFF"
        cmake.definitions["USE_OPERATOR_TUNING"] = "ON" if self.options.use_operator_tuning else "OFF"
        cmake.definitions["USE_GPERFTOOLS"] = "ON" if self.options.use_gperftools else "OFF"
        cmake.definitions["USE_JEMALLOC"] = "ON" if self.options.use_jemalloc else "OFF"
        cmake.definitions["USE_CPP_PACKAGE"] = "ON" if self.options.use_cpppackage else "OFF"

        cmake.configure(source_dir='%s/mxnet' % self.source_folder)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["mxnet"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.bindirs = ["bin"]
