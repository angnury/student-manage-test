# student-manage-test

![api-test](https://github.com/angnury/student-manage-test/actions/workflows/api-test.yml/badge.svg)

对个人项目 [student-manage-web](https://github.com/angnury/student-manage-web) 的**接口自动化 + UI 自动化测试工程**。

被测系统是一套前后端分离的学生综合信息管理系统（Spring Boot 3 + Vue 3 + MySQL），本仓库只做测试，不含业务代码。

**在线测试报告**：https://angnury.github.io/student-manage-test/ （每次推送与每日定时回归自动更新）

## 技术栈

| 层 | 选型 |
|---|---|
| 测试框架 | pytest 8 |
| 接口测试 | requests + YAML 数据驱动 |
| UI 测试 | Selenium 4 + Page Object |
| 数据校验 | pymysql（直连库核对落库结果） |
| 报告 | Allure 2 |
| 持续集成 | GitHub Actions（每日定时回归，报告发布 GitHub Pages） |
| 性能 | JMeter 阶梯加压 |

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 复制并修改配置
cp config/config.example.yaml config/config.yaml

# 3. 运行接口用例
pytest testcases/api -v

# 4. 生成并查看报告
allure serve allure-results
```

> 被测系统需先启动在 `http://localhost:8080`，或把 `config/config.yaml` 里的 `base_url` 指向已部署环境。

## 目录结构

```
api/          接口封装层，每个模块一个类
data/         YAML 数据驱动用例数据
pages/        UI 自动化 Page Object
testcases/    用例本体（api / ui 两类）
utils/        数据库、断言、日志等工具
config/       多环境配置（真实配置不入库）
docs/         用例库、测试报告、缺陷清单
```

## 测试范围

覆盖 6 个模块：登录鉴权、学生管理 CRUD、分页查询、成绩录入、统计报表、角色权限。

用例设计方法：等价类划分、边界值分析、场景法、错误推测法、正交组合。

## 用例概览

共 38 条。当前执行结果：**38 passed**（第二轮修复后全绿，首轮为 31 passed / 7 xfailed）。

| 文件 | 覆盖点 | 用例数 |
|---|---|---|
| `test_login.py` | 正常/密码错/用户不存在/字段缺失、token 可用性 | 6 |
| `test_student_crud.py` | 增删改查、重复学号、删除带成绩的学生、学籍与账号双向一致性 | 7 |
| `test_pagination.py` | 分页生效性、page/size 边界、模糊查询、参数类型异常 | 9 |
| `test_permission.py` | 无 token / 伪造 token / 三种角色越权矩阵 | 8 |
| `test_score.py` | 总分计算、防改分、必填校验、分数越界 | 5 |
| `test_statistics.py` | 概览、分数分布、班级平均分 | 3 |

## 测试执行结论

详见 [`docs/缺陷清单.md`](docs/缺陷清单.md)。首轮共发现 5 个缺陷，其中 2 个严重，**均已修复并回归验证（38 passed）**：

- **D-001** 分页插件未注册，列表接口忽略 `page/size` 返回全表，`total` 恒为 0；
- **D-002** 有成绩的学生无法删除（`score` 表外键未级联），接口返回 500 系统异常。



## 用例执行报告

**https://angnury.github.io/student-manage-test/**

最近一次 CI 运行：**38 条用例 / 35 passed / 3 skipped / 0 failed**

> 3 条 skipped 是依赖数据库直连的落库校验——线上库的 3306 未对外开放，CI 环境无法连接，本地运行时这 3 条会正常执行。

## 说明

被测系统为本人独立开发的学习项目，本仓库用于练习完整的测试工程流程：用例设计 → 自动化实现 → 缺陷管理 → 测试报告 → CI 流水线。
