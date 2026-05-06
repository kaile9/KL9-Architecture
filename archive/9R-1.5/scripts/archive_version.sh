#!/bin/bash
# archive_version.sh — 归档版本脚本
# Usage: ./scripts/archive_version.sh 1.9.0

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> (e.g., 1.9.0)"
    exit 1
fi

# 解析版本号
MAJOR=$(echo $VERSION | cut -d. -f1)
MINOR=$(echo $VERSION | cut -d. -f2)
PATCH=$(echo $VERSION | cut -d. -f3)

MARKETING="9R-${MAJOR}.${MINOR}"
ARCHIVE_DIR="archive/v${MAJOR}/${MARKETING}"

echo "Archiving version ${VERSION} (${MARKETING}) to ${ARCHIVE_DIR}..."

# 创建目录
mkdir -p "${ARCHIVE_DIR}"

# 复制核心文件
cp -r kl9_core "${ARCHIVE_DIR}/"
cp -r kl9_skillbook "${ARCHIVE_DIR}/"
cp -r skillbooks "${ARCHIVE_DIR}/"
cp -r docs "${ARCHIVE_DIR}/"
cp -r tests "${ARCHIVE_DIR}/"
cp -r examples "${ARCHIVE_DIR}/"
cp README.md "${ARCHIVE_DIR}/"
cp .gitignore "${ARCHIVE_DIR}/"

# 创建版本标记
echo "${VERSION} (${MARKETING}) archived on $(date)" > "${ARCHIVE_DIR}/VERSION"

# Git 标签
git tag "v${VERSION}-final"

echo "✓ Archived to ${ARCHIVE_DIR}"
echo "✓ Git tag: v${VERSION}-final"
