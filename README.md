# GitCode Issue Analyzer

基于 `gc` CLI 的 GitCode issue 分析工具，使用 AI 自动识别并分类基础设施类 issue。

## 功能

- 获取指定仓库/组织最近 N 天的所有 issues
- 使用 AI 自动识别基础设施类 issue（不依赖 `infra-tooling` 标签）
- 生成分类汇总 Markdown 报告
- 支持单仓库和组织级多仓库分析

## 快速开始

```bash
# 安装 gc CLI
pip install gitcode-cli
gc auth login

# 获取 issues
python3 analyze.py <owner/repo> --days 7 -r ./issues_raw.json

# AI 分类后生成报告（自动保存到 docs/ 目录）
python3 analyze.py --load-raw ./issues_raw.json --classify ./classification.json

# 或指定输出路径
python3 analyze.py --load-raw ./issues_raw.json --classify ./classification.json -o ./my_report.md
```

## 目录结构

```
├── analyze.py         # CLI 入口
├── gc_wrapper.py      # gc 命令封装
├── fetcher.py         # issue 获取编排
├── classifier.py      # AI 分类
├── reporter.py        # 报告生成
├── requirements.txt   # 依赖（仅 Python 标准库）
├── SKILL.md           # Skill 定义
└── docs/              # 生成的报告
    └── <target>_<timestamp>.md
```

## 报告示例

报告包含：
- **汇总统计**：总数、基础设施数量、子分类分布、仓库分布
- **详情表格**：仓库 | Issue # | 标题 | 子分类 | 理由 | 标签 | 状态 | 创建时间

## 基础设施分类标准

**属于基础设施：**
- CI/CD 流水线、构建系统、自动化
- 开发环境搭建、工具链配置
- 测试框架、测试基础设施
- 部署、容器化、Kubernetes、Docker
- 监控、日志、告警、可观测性
- 代码质量工具（lint、format、static analysis）
- 开发辅助工具、脚本、自动化

**不属于基础设施：**
- 业务功能、UI/UX、产品需求
- 文档反馈
- 常规算子/模型/runtime bug 修复
- CVE/依赖安全漏洞
- API 一致性分析
- 新功能 RFC
