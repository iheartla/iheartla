# Fetch the header-only C++ libraries the tests compile generated code against
# into test/third_party/ (git-ignored). base_python_test.py looks there first.
# autodiff 1.1.2 does not build with Eigen 5, so Eigen is pinned to 3.4.
set -e
cd "$(dirname "$0")"
mkdir -p third_party
[ -d third_party/eigen ] || git -c advice.detachedHead=false clone -q --depth 1 --branch 3.4.1 https://gitlab.com/libeigen/eigen.git third_party/eigen
[ -d third_party/autodiff ] || git -c advice.detachedHead=false clone -q --depth 1 --branch v1.1.2 https://github.com/autodiff/autodiff.git third_party/autodiff
[ -d third_party/LBFGSpp ] || git -c advice.detachedHead=false clone -q --depth 1 --branch v0.4.0 https://github.com/yixuan/LBFGSpp.git third_party/LBFGSpp
