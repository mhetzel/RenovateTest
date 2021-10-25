# pylint: disable=import-outside-toplevel,invalid-sequence-index,no-member

import os
import sys

from conans import ConanFile, CMake
from conans.model.requires import Requirement
from conans.model.version import Version
from conans.model.ref import ConanFileReference

import BuildScripts.ProjectConstants as Constants

Failed to look up dependency tinyspline

class Pkg(ConanFile):
    name = Constants.conanPackageName
    description = Constants.projectName

    keep_imports = True

    settings = 'os', 'arch', 'build_type', 'compiler'

    generators = 'cmake', 'cmake_paths'
    build_policy = 'missing'

    exports_sources = ['BuildScripts/*',
                       'cmake/*',
                       "Assets/*",
                       "Applications/*",
                       'UnitTests/*',
                       'CMakeLists.txt',
                       ]
    exports = 'version', 'conanfile.txt', 'BuildScripts/ProjectConstants.py'

    options = {'verbose': [True, False],
               'yukon_type': ['Bronze', 'Copper'],
               'platform_name': ['Linux', 'Yukon'],
               'config': ['Release', 'Debug'],
               'run_tests': [True, False],
               'build_tests': [True, False]}

    # Manages versioning and bsp selection
    python_requires = 'commsbase/2.1@isg-mtg/dev'
    python_requires_extend = 'commsbase.ConfigBase'
      
    python_requires = "pybind11/0.1"  # recipe to reuse code from
    build_requires = "toml11/[>3.0 <3.6 loose=False, include_prerelease=True]", 'libsass/0.2'
    requires = 'tl-function-ref/1.0', "zulu-openjdk/2.1"

    requires = [("optional-lite/0.1"),
               ('wayland/2.1', "private")]

    requires = (("libuv/1.15.0@bincrafters/stable", "private"), )
    requires = ('ninja/1.0', ("snappy/0.2", "override"))
    requires = "c-ares/[>1.0 <1.8 loose=False]"


    def requirements(self):
       if self.options.myoption:
           self.requires('c-blosc/[~=1.17 include_prerelease=True]')
       else:
           self.requires("dbus/1.2@", private=True, override=False)


    def build_requirements(self):
       if self.settings.os == "Windows":
            self.build_requires("faketool/0.1@user/stable")

    def configure(self):
        if self.settings.os != 'Linux':
            raise Exception('Only supported on Linux OS')

        if self.options.verbose == None:
            self.options.verbose = False
        if self.options.yukon_type == None:
            self.options.yukon_type = os.getenv('YUKON_TYPE', 'Bronze')
        if self.options.platform_name == None:
            self.options.platform_name = os.getenv('PLATFORM_NAME', 'Yukon')
        if self.options.config == None:
            self.options.config = 'Debug' if self.settings.build_type == 'Debug' else 'Release'
        if self.options.build_tests == None:
            self.options.build_tests = self.options.config == 'Debug'
        else:
            self.options.build_tests = self.options.build_tests and self.options.config == 'Debug'
        if self.options.run_tests == None:
            self.options.run_tests = self.options.build_tests

    def build(self):
        cmake = CMake(self)
        cmake.verbose = self.options.verbose
        cmake.definitions['YUKON_TYPE'] = self.options.yukon_type
        cmake.definitions['PLATFORM_NAME'] = self.options.platform_name
        cmake.definitions['CONFIGURATION'] = self.options.config
        cmake.definitions['PROJECT_SELECTION'] = 'All'
        cmake.definitions['BUILD_TESTS'] = str(self.options.build_tests)
        cmake.configure()
        cmake.build()

        if 'TEST_COVERAGE' in os.environ:
            os.chdir(os.path.join(self.build_folder, '../../'))
            os.system('lcov -c -i -d . -o coverage_base.info')
            os.chdir(self.build_folder)

        if self.options.run_tests:
            scriptPath = os.path.join(self.source_folder, 'BuildScripts')
            sys.path.append(scriptPath)
            import SharedUtils.UnitTestRunner as UnitTestRunner
            from SharedUtils import BuildUtils
            from SharedUtils import BuildConfig
            buildUtils = BuildUtils.createUtils()
            buildUtils.setYukonType(self.options.yukon_type)
            build_config = BuildConfig.BuildConfig(self.options.platform_name, self.options.config)
            testRunner = UnitTestRunner.createTestRunner(
                buildUtils, build_config, 'UnitTests')
            failureCount = testRunner.run()
            if failureCount:
                self.output.error('Failure running unit tests')
                sys.exit(1)
            sys.path.remove(scriptPath)

            if 'TEST_COVERAGE' in os.environ:
                os.chdir(os.path.join(self.build_folder, '../../'))
                # Create test coverage data file
                os.system('lcov -c -d . -o coverage_test.info')
                # Combine baseline and test coverage data
                os.system('lcov -a coverage_base.info -a coverage_test.info -o coverage_total.info')
                # Remove unwanted test coverage data
                os.system("lcov -o coverage.info -r coverage_total.info '/opt/Deere/*' '/usr/include/*' '*Test*'")
                # Generate HTML view for overall test coverage
                os.system('genhtml coverage.info -o coverage')
                os.system('tar zcpf coverage.tar.gz coverage')
                # Convert test coverage data to Cobertura's XML report format for Jenkins
                os.system('python3 /lcov_cobertura.py coverage.info --demangle')
                os.chdir(self.build_folder)

    def package(self):
        utilPath = self.deps_env_info[sysroot].UTIL_PATH
        scriptPath = os.path.join(self.source_folder, 'BuildScripts')
        sys.path.append(scriptPath)
        import ProjectBundle
        from SharedUtils import BuildUtils
        buildUtils = BuildUtils.createUtils()
        buildUtils.setYukonType(str(self.options.yukon_type))
        if self.options.platform_name == 'Yukon':
            appsPath = buildUtils.getSolutionPath('Applications', str(
                self.options.platform_name), str(self.options.config))
            buildUtils.stripDebugSymbols(appsPath, path=utilPath)

        bundler = ProjectBundle.createBundler(buildUtils)
        bundler.bundleFiles(str(self.options.platform_name), str(
            self.options.config), self.version)

        self.copy("*", src="BuildArtifacts/{}".format(self.description), 
                  dst=self.package_folder)
        sys.path.remove(scriptPath)

