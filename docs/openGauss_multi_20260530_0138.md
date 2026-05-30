# GitCode Issue 分析报告

| 项目 | 内容 |
|------|------|
| 查询目标 | **openGauss/CM, openGauss/Plugin, openGauss/QA, openGauss/blog, openGauss/community, openGauss/debezium, openGauss/docs, openGauss/oGMemory, openGauss/oGRAC, openGauss/openGauss-connector-python-psycopg2, openGauss/openGauss-connector-python-pyog, openGauss/openGauss-embedded, openGauss/openGauss-migration-portal, openGauss/openGauss-server, openGauss/openGauss-third_party, openGauss/openGauss-tools-chameleon, openGauss/openGauss-tools-datachecker-performance, openGauss/openGauss-tools-sql-translator, openGauss/openGauss-workbench, openGauss/ora-migration-tool, openGauss/website** |
| 查询天数 | 最近 **7** 天 |
| Issue 时间范围 | 2026-05-23 ~ 2026-05-29 |
| 报告生成时间 | 2026-05-30 01:38 UTC |
| 获取 Issue 总数 | **63** |

## 汇总

- 总 issues (获取): **63**
- 基础设施类: **7**

### 按子分类统计

- 构建系统: 3
- 开发体验: 2
- 代码质量工具: 1
- 容器化: 1

### 按仓库统计

- [openGauss/openGauss-server](https://gitcode.com/openGauss/openGauss-server/pulls): 2
- [openGauss/openGauss-embedded](https://gitcode.com/openGauss/openGauss-embedded/pulls): 2
- [openGauss/oGMemory](https://gitcode.com/openGauss/oGMemory/pulls): 1
- [openGauss/oGRAC](https://gitcode.com/openGauss/oGRAC/pulls): 1
- [openGauss/docs](https://gitcode.com/openGauss/docs/pulls): 1

## 详情

| 仓库                               | Issue #    | 标题                                               | 子分类       | 理由                             | 原始标签                 | 状态     | 创建时间   |
|------------------------------------|------------|----------------------------------------------------|--------------|----------------------------------|--------------------------|----------|------------|
| [openGauss/docs](https://gitcode.com/openGauss/docs/pulls)                     | [#7189](https://gitcode.com/openGauss/docs/issues/7189)      | [新需求]: codespell-check：单词白名单新增专有名词  | 代码质量工具 | 拼写检查工具白名单扩展           | sig/Docs                 | open     | 2026-05-27 |
| [openGauss/oGMemory](https://gitcode.com/openGauss/oGMemory/pulls)                 | [#60](https://gitcode.com/openGauss/oGMemory/issues/60)        | [任务]: PERF 质量检测模块 修复&优化                | 开发体验     | 性能检测工具修复与优化           | sig/Community            | open     | 2026-05-29 |
| [openGauss/oGRAC](https://gitcode.com/openGauss/oGRAC/pulls)                    | [#199](https://gitcode.com/openGauss/oGRAC/issues/199)       | [任务]: 安装时锁文件路径解耦                       | 构建系统     | 安装锁文件路径解耦改进           | sig/StorageEngine        | closed   | 2026-05-23 |
| [openGauss/openGauss-embedded](https://gitcode.com/openGauss/openGauss-embedded/pulls)       | [#53](https://gitcode.com/openGauss/openGauss-embedded/issues/53)        | [Bug]: 尚未支持dockerfile方式编译IntarkDB          | 构建系统     | 缺少Dockerfile编译支持           | bug, sig/Embedded        | open     | 2026-05-25 |
| [openGauss/openGauss-embedded](https://gitcode.com/openGauss/openGauss-embedded/pulls)       | [#54](https://gitcode.com/openGauss/openGauss-embedded/issues/54)        | [Bug]: x86架构windows自带的wsl ubuntu系统 打开GC.. | 构建系统     | WSL下GCOV编译选项报错            | sig/Embedded, bug        | open     | 2026-05-29 |
| [openGauss/openGauss-server](https://gitcode.com/openGauss/openGauss-server/pulls)         | [#8165](https://gitcode.com/openGauss/openGauss-server/issues/8165)      | [特性]: 支持gsql使用多个-c参数输入命令             | 开发体验     | gsql客户端多-c参数支持           | sig/StorageEngine, sig.. | open     | 2026-05-25 |
| [openGauss/openGauss-server](https://gitcode.com/openGauss/openGauss-server/pulls)         | [#8182](https://gitcode.com/openGauss/openGauss-server/issues/8182)      | [Bug]: 官方最新docker镜像-opengauss/opengauss:la.. | 容器化       | 官方Docker镜像构建不可用         | sig/StorageEngine, sig.. | open     | 2026-05-29 |
