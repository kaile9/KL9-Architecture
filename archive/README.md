# KL9-RHIZOME 版本归档 · Version Archive

命名规则：9R-{major}.{minor} = 开了玖(9) + RHIZOME(R) + 版本号

## 归档目录

```
archive/
  v1/
    9R-1.9/          ← 1.x 系列最终版本
      kl9_core/
      kl9_skillbook/
      skillbooks/
      README.md
```

## 归档触发条件

当大版本升级时（如 1.x -> 2.0），将上一大版本的最新小版本归档：
- 1.9 -> 归档到 `archive/v1/9R-1.9/`
- 2.3 -> 归档到 `archive/v2/9R-2.3/`

## 如何归档

```bash
./scripts/archive_version.sh 1.9.0
```

这将：
1. 创建 `archive/v1/9R-1.9/` 目录
2. 复制当前代码到归档目录
3. 打 Git 标签 `v1.9.0-final`
