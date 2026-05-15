# 求职 AI Copilot 使用模板

本文档提供每个功能的示例填写内容，用于测试和演示系统功能。

---

## 功能一：首页

无需填写，点击功能卡片进入对应页面即可。

---

## 功能二：JD 解析

### 输入字段模板

| 字段 | 示例填写内容 |
|------|-------------|
| **公司** | 阿里巴巴 |
| **岗位** | Java 后端开发工程师 |
| **JD 文本** | 见下方 JD 示例文本 |

### JD 示例文本（可复制粘贴）

```
【阿里巴巴】Java 后端开发工程师

岗位职责：
1. 负责电商核心系统的架构设计与开发
2. 参与高并发、高可用系统的设计与优化
3. 编写高质量代码，进行代码评审
4. 解决系统性能瓶颈，保障系统稳定性

任职要求：
1. 本科及以上学历，计算机相关专业
2. 3年以上 Java 开发经验，精通 Spring Boot、Spring Cloud
3. 熟悉 MySQL、Redis、Elasticsearch
4. 熟悉分布式系统原理，有微服务架构经验
5. 熟悉 Linux 系统，能编写 Shell 脚本
6. 有电商或互联网大厂经验优先

薪资范围：25K-40K·16薪
工作地点：杭州/深圳
```

### 异步开关
- **关闭**：同步解析，等待时间约 1-3 秒
- **开启**：异步解析，返回任务 ID，需查询任务状态获取结果

---

## 功能三：简历匹配

### 输入字段模板

| 字段 | 示例填写内容 |
|------|-------------|
| **JD ID** | （从 JD 解析结果自动带入，或选择已解析的 JD） |
| **简历文本** | 见下方简历示例文本 |
| **用户邮箱** | test@example.com |

### 简历示例文本（可复制粘贴）

```
张三
手机：138-0000-0000
邮箱：zhangsan@email.com

教育背景：
本科 | 计算机科学与技术 | 浙江大学 | 2018-2022

工作经历：
字节跳动 | Java 开发工程师 | 2022.07-至今
- 负责抖音电商订单系统开发
- 使用 Spring Boot + MySQL + Redis 技术栈
- 参与系统性能优化，QPS 提升 50%

专业技能：
- 精通 Java，熟悉 JVM 原理
- 熟练使用 Spring Boot、Spring Cloud
- 熟悉 MySQL、Redis、Kafka
- 了解分布式系统原理

项目经验：
订单系统重构项目
- 负责订单核心模块开发
- 使用 Redis 缓存优化查询性能
- 引入消息队列处理异步任务
```

### 预期输出结果

```json
{
  "match_score": 78,
  "matched_skills": ["Java", "Spring Boot", "MySQL", "Redis"],
  "missing_skills": ["Elasticsearch", "Shell 脚本", "微服务架构经验"],
  "gap_analysis": {
    "优势": "有电商系统开发经验，熟悉高并发场景",
    "不足": "缺少 Elasticsearch 经验，微服务架构经验不足"
  },
  "rewrite_suggestions": [
    "建议补充 Elasticsearch 相关项目经验",
    "强调微服务拆分经验，如参与过服务拆分项目"
  ]
}
```

---

## 功能四：模拟面试

### 创建面试会话

| 字段 | 示例填写内容 |
|------|-------------|
| **JD ID** | （从 JD 解析结果带入） |
| **用户邮箱** | test@example.com |

### 预期生成题目示例

```
题目 1（技术）：
请简述 Spring Boot 自动配置原理，并举例说明如何自定义 starter。

题目 2（技术）：
在高并发场景下，如何保证数据库和缓存的数据一致性？

题目 3（行为）：
描述一次你解决过的最复杂的技术问题，以及你的思考过程。

题目 4（技术）：
Redis 有哪些数据类型？分别在什么场景下使用？
```

### 作答示例（文本作答）

**题目 1 作答：**

```
Spring Boot 自动配置基于 Starter 机制和条件注解实现。

主要原理：
1. @EnableAutoConfiguration 注解触发自动配置
2. Spring Boot 扫描 META-INF/spring.factories 文件
3. 根据条件注解（@ConditionalOnClass、@ConditionalOnProperty 等）判断是否加载配置
4. 加载后注入相应的 Bean

自定义 starter 步骤：
1. 创建 autoconfigure 模块，编写配置类
2. 使用 @ConditionalOnClass 等条件注解控制加载
3. 创建 starter 模块，引入 autoconfigure 依赖
4. 在 META-INF/spring.factories 中注册配置类
5. 发布到 Maven 仓库即可使用
```

### 预期评分反馈示例

```json
{
  "score": 85,
  "feedback": "回答结构清晰，原理阐述准确",
  "strengths": [
    "准确描述了自动配置核心原理",
    "条件注解解释到位",
    "自定义 starter 步骤完整"
  ],
  "weaknesses": [
    "可补充 spring.factories 加载机制的细节",
    "建议举例说明具体使用场景"
  ]
}
```

### 语音作答（可选）

- 上传音频文件（MP3/WAV 格式）
- 系统自动转写为文本
- 基于转写文本进行评分

---

## 功能五：训练计划

### 生成计划输入

| 字段 | 示例填写内容 |
|------|-------------|
| **报告 ID** | （从简历匹配结果带入） |
| **用户邮箱** | test@example.com |

### 预期生成 7 天计划示例

```json
{
  "start_date": "2024-01-15",
  "days": [
    {
      "day": 1,
      "focus": "Elasticsearch 基础入门",
      "tasks": [
        "学习 Elasticsearch 核心概念（索引、文档、映射、分片）",
        "完成官方 Quick Start 教程",
        "本地安装 ES 并创建第一个索引"
      ],
      "resources": [
        "https://www.elastic.co/guide/en/elasticsearch/reference/current/getting-started.html",
        "B站：Elasticsearch 入门教程（某 UP 主）"
      ]
    },
    {
      "day": 2,
      "focus": "Spring Boot 集成 ES",
      "tasks": [
        "学习 Spring Data Elasticsearch 使用",
        "实现基本的 CRUD 操作",
        "练习复杂查询构建"
      ],
      "resources": [
        "Spring Data Elasticsearch 官方文档",
        "GitHub 示例项目"
      ]
    },
    {
      "day": 3,
      "focus": "微服务架构理论",
      "tasks": [
        "学习微服务拆分原则",
        "理解服务注册与发现",
        "阅读 2-3 篇大厂微服务实践文章"
      ],
      "resources": [
        "《微服务设计》书籍第 1-3 章",
        "掘金：微服务架构实践系列"
      ]
    },
    {
      "day": 4,
      "focus": "Spring Cloud 基础",
      "tasks": [
        "搭建 Eureka 服务注册中心",
        "实现服务提供者和服务消费者",
        "配置 Ribbon 负载均衡"
      ],
      "resources": [
        "Spring Cloud 官方文档",
        "某教程网站 Spring Cloud 系列"
      ]
    },
    {
      "day": 5,
      "focus": "微服务实践项目",
      "tasks": [
        "将现有项目拆分为 2-3 个微服务",
        "实现服务间调用",
        "编写 Dockerfile 容器化部署"
      ],
      "resources": [
        "Docker 官方文档",
        "个人项目代码"
      ]
    },
    {
      "day": 6,
      "focus": "Linux Shell 脚本",
      "tasks": [
        "学习常用 Shell 命令",
        "编写 3-5 个实用脚本",
        "练习日志分析和文本处理"
      ],
      "resources": [
        "《鸟哥的 Linux 私房菜》",
        "Linux 命令行实践"
      ]
    },
    {
      "day": 7,
      "focus": "综合复习与总结",
      "tasks": [
        "整理本周学习内容",
        "更新简历补充新技能",
        "模拟面试练习"
      ],
      "resources": [
        "个人笔记",
        "模拟面试系统"
      ]
    }
  ]
}
```

---

## 快速测试流程

按以下顺序测试，数据可连贯使用：

1. **JD 解析**
   - 填写：阿里巴巴 / Java 后端开发工程师 / JD 文本
   - 获取：jd_id（后续使用）

2. **简历匹配**
   - 选择：上一步的 jd_id
   - 填写：张三简历文本 / test@example.com
   - 获取：report_id（后续使用）

3. **模拟面试**
   - 选择：JD 解析的 jd_id
   - 创建面试会话，获取 session_id
   - 回答题目，获取评分
   - 查看面试报告

4. **训练计划**
   - 选择：简历匹配的 report_id
   - 生成 7 天计划
   - 查看每日任务

---

## 测试数据速查表

| 功能 | 关键输入 | 示例值 |
|------|---------|--------|
| JD 解析 | 公司 | 阿里巴巴 |
| | 岗位 | Java 后端开发工程师 |
| 简历匹配 | 用户邮箱 | test@example.com |
| 模拟面试 | 用户邮箱 | test@example.com |
| 训练计划 | 用户邮箱 | test@example.com |

---

## 注意事项

1. **邮箱格式**：必须使用有效的邮箱格式（如 test@example.com）
2. **JD 长度**：JD 文本建议不少于 100 字，内容越详细解析效果越好
3. **简历长度**：简历建议 200-1000 字，包含教育、工作、技能、项目经历
4. **异步模式**：大量文本解析建议使用异步模式
5. **语音作答**：仅支持 MP3、WAV 格式，大小不超过 10MB
