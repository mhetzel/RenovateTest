from conans import ConanFile

class Pkg(ConanFile):
   python_requires = "pybind11/0.1"  # recipe to reuse code from
   build_requires = "toml/0.2@user/testing", "libsass/0.2@user/testing"
   requires = "tl-function-ref/1.0", "zulu-openjdk/2.1@otheruser/testing"

   requires = [("optional-lite/0.1@user/testing"),
               ("snappy/0.2@dummy/stable", "override"),
               ("wayland/2.1@coder/beta", "private")]

   requires = (("libuv/1.0@user/stable", "private"), )
   requires = ('ninja/1.0@user/stable', ("tinyspline/3.0@other/beta", "override"))
   requires = "c-ares/[>1.0 <1.8]@user/stable"


def requirements(self):
   if self.options.myoption:
      self.requires('c-blosc/1.2@drl/testing')
   else:
      self.requires("c-blosc/2.2@drl/stable")
      self.requires("dbus/1.2@drl/testing", private=True, override=False)


def build_requirements(self):
   if self.settings.os == "Windows":
      self.build_requires("faketool/0.1@user/stable")
