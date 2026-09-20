#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd -- "${REPOSITORY_ROOT}/../.." && pwd)"
SOURCE_DIR="${WORKSPACE_ROOT}/src"
MTC_DIR="${SOURCE_DIR}/moveit_task_constructor"
MTC_REVISION="f16c557cb3ec9acffa0579f8d7345c26b1491e95"

for command_name in vcs git rosdep; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "错误：找不到 ${command_name}，请先安装 README 中列出的依赖。" >&2
    exit 1
  fi
done

mkdir -p "${SOURCE_DIR}"

echo "导入固定版本的 MoveIt Task Constructor..."
if [[ ! -e "${MTC_DIR}" ]]; then
  vcs import "${SOURCE_DIR}" < "${REPOSITORY_ROOT}/mycobot_jazzy.repos"
fi

if ! git -C "${MTC_DIR}" rev-parse --git-dir >/dev/null 2>&1; then
  echo "错误：MTC 未正确导入到 ${MTC_DIR}。" >&2
  exit 1
fi

CURRENT_MTC_REVISION="$(git -C "${MTC_DIR}" rev-parse HEAD)"
if [[ "${CURRENT_MTC_REVISION}" != "${MTC_REVISION}" ]]; then
  echo "错误：现有 MTC 版本为 ${CURRENT_MTC_REVISION}。" >&2
  echo "本项目要求 ${MTC_REVISION}；请备份本地改动后重新导入依赖。" >&2
  exit 1
fi

echo "初始化 MTC 的 pybind11 和 scope_guard 子模块..."
git -C "${MTC_DIR}" submodule sync --recursive
git -C "${MTC_DIR}" submodule update --init --recursive

echo "安装 rosdep 依赖..."
rosdep install --from-paths "${SOURCE_DIR}" --ignore-src -r -y

echo "依赖准备完成。现在可以在 ${WORKSPACE_ROOT} 中运行 colcon build。"
