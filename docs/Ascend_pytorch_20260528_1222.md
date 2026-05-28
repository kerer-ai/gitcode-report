# GitCode Issue 分析报告

| 项目 | 内容 |
|------|------|
| 查询目标 | **Ascend/pytorch** |
| 查询天数 | 最近 **7** 天 |
| Issue 时间范围 | 2026-05-22 ~ 2026-05-28 |
| 报告生成时间 | 2026-05-28 12:22 UTC |
| 获取 Issue 总数 | **103** |

## 汇总

- 总 issues (获取): **103**
- 基础设施类: **31**

### 按子分类统计

- testing-infra: 13
- toolchain: 8
- ci/cd: 6
- dev-environment: 3
- build: 1

### 按仓库统计

- Ascend/pytorch: 31

## 详情

| 仓库             | Issue # | 标题                             | 子分类             | 理由                            | 原始标签                           | 状态     | 创建时间       |
|----------------|---------|--------------------------------|-----------------|-------------------------------|--------------------------------|--------|------------|
| Ascend/pytorch | 2072    | [Bug]:fix aclgraph testcase    | testing-infra   | 修复aclgraph测试用例                | bug, resolved                  | closed | 2026-05-22 |
| Ascend/pytorch | 2074    | [Bug]: torch2.12 dynamo支持了re.. | toolchain       | dynamo record_stream patch清理  | bug, resolved                  | closed | 2026-05-22 |
| Ascend/pytorch | 2078    | 其他版本有patch文件，但是2.12并没有，同样需要对.. | toolchain       | v2.12缺少patch文件需补齐适配           | event: api-consistency, reso.. | closed | 2026-05-23 |
| Ascend/pytorch | 2079    | 仓库没有8.5.0 cann版本吗？             | dev-environment | 缺少CANN 8.5.0版本编译支持            |                                | closed | 2026-05-24 |
| Ascend/pytorch | 2081    | test目录下torch.jit.ScriptModul.. | testing-infra   | ScriptModule API测试用例缺失        |                                | open   | 2026-05-24 |
| Ascend/pytorch | 2086    | [Doc]: master和v2.12.0分支的Dock.. | dev-environment | Docker文件夹改为小写docker规范         | document                       | open   | 2026-05-25 |
| Ascend/pytorch | 2087    | feat(ci): 重命名 trigger workfl.. | ci/cd           | 重命名trigger workflow调整定时策略     | infra-tooling, resolved        | closed | 2026-05-25 |
| Ascend/pytorch | 2089    | [Usage]: torch.fx.Tracer.cre.. | testing-infra   | create_node NPU适配patch补充      | usage, event: api-consistency  | open   | 2026-05-25 |
| Ascend/pytorch | 2090    | [Test]: CI流水线将ARM_A2用例拆分成npu.. | ci/cd           | CI流水线ARM_A2用例拆分优化             | resolved                       | closed | 2026-05-25 |
| Ascend/pytorch | 2091    | [Feature]: TORCH_NPU_USE_COM.. | toolchain       | COMPATIBLE_IMPL SoC自动检测       | feature, resolved              | closed | 2026-05-25 |
| Ascend/pytorch | 2095    | [Usage]: torch.fx.replace_pa.. | testing-infra   | replace_pattern测试NPU适配patch缺失 | usage                          | open   | 2026-05-25 |
| Ascend/pytorch | 2098    | [Bug]: 增加Torch.jit.ScriptMod.. | testing-infra   | 增加ScriptModule.cpu测试用例        | bug                            | open   | 2026-05-26 |
| Ascend/pytorch | 2101    | [Feature]: 安装torch_npu时需安装Tr.. | toolchain       | 安装torch_npu需捆绑Triton-Ascend   | feature                        | closed | 2026-05-26 |
| Ascend/pytorch | 2106    | [Usage]: pytorch社区用例缺少对torch.. | testing-infra   | 补齐create_proxy测试用例            | usage                          | open   | 2026-05-26 |
| Ascend/pytorch | 2107    | [Bug]: [inductor] torchbench.. | toolchain       | inductor精度工具torchbench报错      | bug, resolved                  | closed | 2026-05-26 |
| Ascend/pytorch | 2113    | [Installation]: 构建易用性提升        | dev-environment | 提供Dockerfile保证独立构建PTA         | installation                   | open   | 2026-05-26 |
| Ascend/pytorch | 2114    | [Bug]: [inductor][v2.9.0] in.. | toolchain       | inductor精度工具更新未同步             | bug                            | open   | 2026-05-26 |
| Ascend/pytorch | 2115    | [Feature]: 测试用例移植              | testing-infra   | 测试用例移植                        | feature, resolved              | closed | 2026-05-27 |
| Ascend/pytorch | 2117    | [Feature]: 测试用例同步              | testing-infra   | 测试用例同步                        | feature                        | open   | 2026-05-27 |
| Ascend/pytorch | 2123    | 门禁用例未跑到x86机器，后续在x86上跑失败        | ci/cd           | 门禁未覆盖x86机器导致CI漏测              | resolved                       | closed | 2026-05-27 |
| Ascend/pytorch | 2130    | [Usage]: torch.distributed.e.. | testing-infra   | elastic agent测试用例补齐           | usage                          | open   | 2026-05-27 |
| Ascend/pytorch | 2132    | [Doc]: AKG对接PTA新增环境变量          | toolchain       | AKG新增环境变量对接PTA                | resolved, document             | closed | 2026-05-27 |
| Ascend/pytorch | 2133    | add pass ut                    | testing-infra   | 添加pass单元测试                    |                                | open   | 2026-05-27 |
| Ascend/pytorch | 2136    | enhance(ci): 替换工作流引用为 Ascend.. | ci/cd           | 替换CI工作流引用精简setup动作            | infra-tooling                  | open   | 2026-05-28 |
| Ascend/pytorch | 2137    | [Bug]: CI 环境找不到 ACL 头文件导致JIT.. | ci/cd           | CI环境缺少ACL头文件JIT编译失败           | bug, resolved                  | closed | 2026-05-28 |
| Ascend/pytorch | 2138    | [Usage]: to_sparse 梯度用例 fast.. | testing-infra   | to_sparse梯度fast gradcheck测试   | usage                          | open   | 2026-05-28 |
| Ascend/pytorch | 2141    | 【分布式】社区2.10.0版本特性和修复验证         | testing-infra   | 社区版本特性与bugfix验证               | resolved                       | closed | 2026-05-28 |
| Ascend/pytorch | 2145    | bump version to 26.0.0 post .. | build           | 版本号bump到26.0.0                |                                | open   | 2026-05-28 |
| Ascend/pytorch | 2147    | [Bug]: 在op-plugin中新增对齐torch原.. | ci/cd           | op-plugin流水线编译报错              | bug                            | open   | 2026-05-28 |
| Ascend/pytorch | 2149    | [Bug]: INDUCTOR_ASCEND_CHECK.. | toolchain       | INDUCTOR环境变量解析正则错误            | bug                            | open   | 2026-05-28 |
| Ascend/pytorch | 2152    | [Usage]: pytorch社区用例缺少对torch.. | testing-infra   | 补齐get_fresh_qualname测试用例      | usage                          | open   | 2026-05-28 |
