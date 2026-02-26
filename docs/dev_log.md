# day1
项目目标：构建一个基于本地大模型 (LM Studio) 的、具备错误自愈能力的文档提取引擎。
技术栈：Python, LlamaIndex, LM Studio (Local LLM), Docker。
今日任务：
 初始化项目仓库。
 连通 Python 代码与 LM Studio。
 跑通第一个 "Hello World" (让模型回答一句话)。

# day2:
数据结构 (Schema)：
我们需要一个 Invoice 类，包含 invoice_number (str), date (str), total_amount (float), items (List)。
核心函数 (Core Function)：
需要一个函数 extract_from_text(text, schema_class) -> json。
LlamaIndex 的用法：
查阅文档，发现 LlamaIndex 有 StructuredLLM 或 PydanticProgram。决定使用 LlamaIndex 的 program 模块，因为它专门做这个。


引入fastapi
脚本转服务
1.规划 API 接口
我们需要一个简单的 POST 接口：

Endpoint: POST /extract
Input: JSON Body {"text": "你的OCR文本..."}
Output: JSON {"status": "success", "data": { ...invoice_json... }}
2.创建主程序文件
在项目根目录下新建 main.py（这是 FastAPI 的标准入口文件）。
3.运行你的第一个微服务
4.体验 Swagger UI (FastAPI 的杀手锏)

5.尝试重启机制

6.尝试自愈机制

7.置信度评分与人工介入

8.**架构重构 (Week 3 Kickoff)**
- **Schema 变更**: 将单一的 `Invoice` 模型封装进 `ExtractionResult`，增加了 `confidence_score` (float) 和 `notes` (str)。
- **Extractor 升级**: 修改 `extract_invoice` 函数，使其 output_cls 指向新的包装类。更新 Prompt 指令，要求模型评估提取质量。
- **API 逻辑更新**: 
    - 引入阈值逻辑 (`CONFIDENCE_THRESHOLD = 0.8`)。
    - 返回状态现在包含 `review_needed`，标志着 Human-in-the-loop 流程的入口已打通。
- **测试计划**: 下一步需要找一些模糊或缺角的文本进行测试，看模型是否会诚实地给出低分。

9.Prompt（指令）与 Schema（规则）之间的逻辑冲突
打补丁 (Schema)：允许模型在绝望时返回“空值”或“默认值”，防止死循环。
强引导 (Extractor)：在重试时，授权模型进行“合理猜测”（比如缺年份就填当前年份）。
兜底 (Main)：捕获最后一次失败，返回 status: failed 而不是让服务器报 500 错误。

10.**前端可视化 (Human-in-the-loop Dashboard)**
- **工具**: 使用 Streamlit 构建了交互式工作台。
- **功能**:
    - 集成了 API 调用。
    - 实现了状态可视化：高置信度显示绿色 ✅，低置信度显示黄色 ⚠️。
    - 模拟了人工审核流程：展示 AI 修正后的数据，允许人工二次确认。
- **里程碑**: 完成了“从 PDF 到 结构化数据 到 人工审核”的完整闭环 MVP。

11.:
**全链路联调成功**
- **问题解决**: 解决了 Streamlit 在特定浏览器下的白屏问题 (Switch to Chrome)，解决了 API Method Not Allowed 问题。
- **验证通过**: 
    - 前端 Dashboard 能够正确触发后端 API。
    - 后端能够正确调用本地 Gemma-2 模型。
    - "残缺小票"测试用例触发了 Review Needed 状态，证明置信度逻辑生效。
    - "完美发票"测试用例直接通过，证明 Happy Path 生效。
- **状态**: Week 3 目标达成。系统已具备演示能力。


# day3:
项目转型（基础->通用，简易->广泛）
对话：
等一下，在week4的工作之前，是否有必要完善与拓展后端内容，然后继续完善前端dashboard，我个人从主观上感觉，目前项目在规定功能范围内确实通畅，但是功能缺乏泛化能力，目前只满足票据格式，然而对于一个自愈式智能数据提取流水线（又名Resilient Doc Parser）来说，仅仅只是一个票据提取，还是很片面化，可能票据功能深度与细节还是可以的，同时还有一个问题，目前的后端还是体现在本地，并没有连接数据库，但是你刚刚又说到使用Docker， Docker Desktop 确实自带数据库包装，可以弥补现在的数据库层面的数据问题，所以现在的项目缺陷可能是项目功能广度不够，毕竟实际生化中不只有票据格式的信息，可能还有办公上的PDF、Word、Excel格式、以及开发、笔记等领域常用的markdown格式、机器学习常用的csv、txt文本格式（也可以按如下分类：文档类型覆盖
结构化文档：PDF表格、Excel、CSV等

半结构化文档：发票、收据、合同、报告等

非结构化文档：扫描图片、手写体、邮件正文等

混合文档：包含表格和自由文本的复杂文档，如markdown等），现在这些还只是普通文档层面，还没有细分到其他数据类型情况，而且就单一的票据功能，也会细分好多种票据格式，甚至还能根据地域的不同再度细分，但是这些细分情况暂时不做考虑，先考虑功能的广度，毕竟我们的项目是Resilient Doc Parser，本质上还是针对文档类，而针对自愈式智能数据提取流水线这个名字中数据这两个字所带来的那种无穷无尽的数据功能细分，我们可以就当是噱头而不做过多考虑

实际数据可能情况：
对于一个**自愈式智能数据提取流水线**，数据覆盖面应该非常全面，涵盖整个数据生命周期的各个阶段。以下是我列举的详细数据覆盖面：

## 一、**输入数据层覆盖面**

### 1. **文档类型覆盖**
- **结构化文档**：PDF表格、Excel、CSV
- **半结构化文档**：发票、收据、合同、报告
- **非结构化文档**：扫描图片、手写体、邮件正文
- **混合文档**：包含表格和自由文本的复杂文档

### 2. **图像质量情况**
- **理想质量**：高清扫描、数字生成PDF
- **常见问题**：模糊、倾斜、阴影、褶皱
- **极端情况**：低分辨率、光照不均、部分遮挡
- **OCR挑战**：手写体、特殊字体、多语言混排

### 3. **数据格式多样性**
- 不同模板的发票（增值税发票、普通发票、电子发票）
- 各国票据格式（中国、美国、欧盟等）
- 行业特定格式（医疗账单、物流运单、财务报表）

## 二、**处理过程数据覆盖面**

### 4. **OCR原始输出数据**
- 识别置信度分布
- 字符/单词/行级别的原始坐标
- 版面分析结果（段落、表格、图片区域）
- 识别错误的统计分布

### 5. **特征工程数据**
- **文本特征**：关键词频率、正则匹配结果、命名实体
- **结构特征**：表格行数列数、对齐方式、间距
- **上下文特征**：前后文关系、位置信息、字体大小
- **语义特征**：领域术语、实体关系、意图识别

### 6. **提取结果数据**
- 成功提取的字段和值
- 提取置信度评分
- 多个候选结果（当AI不确定时）
- 提取逻辑的溯源信息

## 三、**质量评估数据覆盖面**

### 7. **置信度评估数据**
- **字段级置信度**：每个提取字段的独立置信度
- **文档级置信度**：整体文档的可靠性评分
- **模型自评**：AI对自己的判断有多确定
- **一致性检查**：逻辑一致性、数值合理性

### 8. **验证规则数据**
- **格式验证**：日期格式、金额格式、编号格式
- **逻辑验证**：总额=单价×数量、税率计算
- **业务规则**：公司特定规则、行业标准
- **历史对比**：与历史数据的偏差度

### 9. **异常检测数据**
- 字段缺失或异常的频率
- 异常值的统计分布
- 模式偏离检测结果
- 欺诈风险指标

## 四、**自愈机制数据覆盖面**

### 10. **错误类型分类**
- **OCR错误**：识别错误、版面解析错误
- **提取错误**：字段映射错误、上下文理解错误
- **逻辑错误**：计算错误、规则应用错误
- **系统错误**：超时、内存溢出、依赖服务失败

### 11. **修复策略数据**
- **自动修复历史**：成功/失败的修复尝试
- **策略选择逻辑**：不同错误类型对应的修复策略
- **修复效果评估**：修复后置信度提升情况
- **学习进化数据**：系统从错误中学习的记录

### 12. **人工反馈数据**
- 人工审核记录（通过/拒绝）
- 人工修正的字段值
- 审核员的反馈意见
- 审核时长和效率数据

## 五、**机器学习数据覆盖面**

### 13. **训练数据**
- 标注数据集（文档+正确提取结果）
- 数据增强生成的样本
- 难例挖掘的挑战性样本
- 持续学习的新数据流

### 14. **模型性能数据**
- 各模型的准确率、召回率、F1分数
- 不同文档类型的性能差异
- 推理时间统计
- 内存和计算资源使用情况

### 15. **AB测试数据**
- 新旧模型对比结果
- 不同策略的效果比较
- 用户满意度指标
- 业务影响评估

## 六、**监控与可观测性数据**

### 16. **系统健康数据**
- API响应时间、成功率、错误率
- 队列长度和处理延迟
- 资源使用率（CPU、内存、GPU）
- 依赖服务状态

### 17. **业务指标数据**
- **吞吐量**：每日处理文档数
- **准确率**：自动通过率 vs 人工审核率
- **效率提升**：节省的人工审核时间
- **成本效益**：处理成本 vs 人工成本

### 18. **用户行为数据**
- 用户最常处理的文档类型
- 人工干预的常见原因
- 用户对AI建议的接受率
- 用户自定义规则的创建情况

## 七、**安全与合规数据覆盖面**

### 19. **数据安全数据**
- 敏感信息检测（PII、PCI）
- 数据脱敏/加密记录
- 访问日志和审计轨迹
- 数据保留和删除记录

### 20. **合规性数据**
- 数据源的可追溯性
- 处理过程的合规性检查
- 行业标准符合性（如GDPR、HIPAA）
- 认证和审计数据

## 八、**知识库与元数据覆盖面**

### 21. **领域知识数据**
- 行业术语库和词典
- 公司/供应商名称数据库
- 产品/服务分类体系
- 地理信息数据库

### 22. **模板库数据**
- 常见文档模板特征
- 模板匹配规则
- 模板变化趋势
- 新模板的学习记录

### 23. **规则库数据**
- 验证规则及其权重
- 业务规则的历史演变
- 规则冲突解决记录
- 规则效果评估数据

## 九、**端到端流水线数据流**

### 24. **全链路追踪数据**
- 每个文档的唯一追踪ID
- 在各个处理阶段的时间戳
- 处理结果的版本历史
- 数据血缘关系

### 25. **状态机数据**
- 文档状态流转记录
- 重试次数和原因
- 最终状态分布
- 异常终止的根因分析

### 26. **依赖关系数据**
- 服务间调用关系
- 数据依赖图
- 故障传播分析
- 瓶颈识别数据

## 十、**反馈循环与优化数据**

### 27. **持续改进数据**
- 错误模式的变化趋势
- 系统性能的进化曲线
- 新功能的效果评估
- 用户反馈的聚类分析

### 28. **实验数据**
- A/B测试配置和结果
- 特征工程的实验记录
- 超参数调优历史
- 模型架构对比数据

### 29. **商业价值数据**
- 自动化率的提升趋势
- 人力成本的节省计算
- 处理速度的改进数据
- 客户满意度指标

---

## **数据覆盖的关键原则**

1. **全链路可追溯**：从输入到输出的每个步骤都有数据记录
2. **多维度评估**：技术指标+业务指标+用户体验
3. **实时+历史**：既有实时监控也有历史趋势分析
4. **粒度可调**：支持从宏观统计到微观细节的查看
5. **关联分析**：不同数据维度之间的关联关系
6. **可解释性**：每个决策都有可解释的数据支撑
7. **隐私保护**：在收集全面数据的同时保护敏感信息

这样的数据覆盖面确保了系统不仅是"能工作"，而且是"可观察、可诊断、可优化、可信任"的。每个数据点都是系统自我修复和持续进化的"营养源"。

目前阶段：
项目解耦
src/
├── core/                  # [新增] 核心层：存放通用的基础设施
│   ├── __init__.py        # 空文件
│   ├── config.py          # 配置中心 (URL, Model Name)
│   ├── llm.py             # LLM 连接工厂
│   └── models.py          # 通用的数据外壳 (ExtractionResult)
├── parsers/               # [新增] 业务层：每种文档类型一个独立模块
│   ├── __init__.py        # 空文件
│   ├── invoice.py         # 发票相关的 Schema + 提取逻辑 + 自愈
│   └── contract.py        # 合同相关的 Schema + 提取逻辑
├── router.py              # [新增] 调度层：自动分类与分发
├── main.py                # [修改] API 入口
└── dashboard.py           # [修改] 前端 (适配新接口)


day5：
**多模态泛化与大文档攻坚**
- **架构升级**:
    - 引入 `Router Pattern` (路由模式)，实现了发票/合同的自动分类。
    - 引入 `Ingestion Layer` (摄取层)，支持 PDF(文本型)、Word、Markdown 的解析。
- **难点突破**:
    - 解决了大文件 (15MB PDF) 导致的 Token 溢出与超时问题 (通过截断与超时配置优化)。
    - 解决了本地模型输出 Markdown 格式导致 JSON 解析失败的问题 (通过正则清洗)。
- **UI 重构**:
    - 实现了类 ChatGPT 的沉浸式时间轴界面。
    - 修复了前端 Pydantic 数据嵌套层级不一致导致的显示 Bug。
- **状态**: 合同解析功能 MVP 通过。


IDE错误：
Unhandled exception in [ComponentManager(ApplicationImpl@1838851495), com.intellij.codeWithMe.ClientIdContextElementPrecursor@74037d22, CoroutineName(com.intellij.execution.wsl.ProductionWslIjentManager), Dispatchers.Default]

com.intellij.platform.ijent.IjentUnavailableException$CommunicationFailure: The process IjentId(ijent-0-wsl-Ubuntu) suddenly exited with the code -1
	at com.intellij.platform.ijent.spi.IjentSessionMediatorKt.ijentProcessExitAwaiter(IjentSessionMediator.kt:280)
	at com.intellij.platform.ijent.spi.IjentSessionMediatorKt.access$ijentProcessExitAwaiter(IjentSessionMediator.kt:1)
	at com.intellij.platform.ijent.spi.IjentSessionMediatorKt$ijentProcessExitAwaiter$1.invokeSuspend(IjentSessionMediator.kt)
	at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:33)
	at kotlinx.coroutines.DispatchedTask.run(DispatchedTask.kt:104)
	at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1144)
	at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(ThreadPoolExecutor.java:642)
	at com.intellij.platform.ijent.spi.IjentThreadPool$IjentThreadFactory$newThread$thread$1.run(IjentThreadPool.kt:67)
	Suppressed: java.lang.Throwable: Rethrown from here
		at com.intellij.platform.ijent.spi.IjentSessionMediator$Companion.create$lambda$3$lambda$2(IjentSessionMediator.kt:101)
		at kotlinx.coroutines.InvokeOnCompletion.invoke(JobSupport.kt:1382)
		at kotlinx.coroutines.JobSupport.notifyCompletion(JobSupport.kt:1492)
		at kotlinx.coroutines.JobSupport.completeStateFinalization(JobSupport.kt:322)
		at kotlinx.coroutines.JobSupport.finalizeFinishingState(JobSupport.kt:239)
		at kotlinx.coroutines.JobSupport.continueCompleting(JobSupport.kt:936)
		at kotlinx.coroutines.JobSupport.access$continueCompleting(JobSupport.kt:22)
		at kotlinx.coroutines.JobSupport$ChildCompletion.invoke(JobSupport.kt:1156)
		at kotlinx.coroutines.JobSupport.notifyCompletion(JobSupport.kt:1492)
		at kotlinx.coroutines.JobSupport.completeStateFinalization(JobSupport.kt:322)
		at kotlinx.coroutines.JobSupport.finalizeFinishingState(JobSupport.kt:239)
		at kotlinx.coroutines.JobSupport.tryMakeCompletingSlowPath(JobSupport.kt:907)
		at kotlinx.coroutines.JobSupport.tryMakeCompleting(JobSupport.kt:864)
		at kotlinx.coroutines.JobSupport.makeCompletingOnce$kotlinx_coroutines_core(JobSupport.kt:829)
		at kotlinx.coroutines.AbstractCoroutine.resumeWith(AbstractCoroutine.kt:97)
		at kotlinx.coroutines.debug.internal.DebugProbesImpl$CoroutineOwner.resumeWith(DebugProbesImpl.kt:545)
		at kotlin.coroutines.jvm.internal.BaseContinuationImpl.resumeWith(ContinuationImpl.kt:46)
		at kotlinx.coroutines.DispatchedTask.run(DispatchedTask.kt:102)
		... 3 more
	Suppressed: kotlinx.coroutines.internal.DiagnosticCoroutineContextException: [ComponentManager(ApplicationImpl@1838851495), com.intellij.codeWithMe.ClientIdContextElementPrecursor@74037d22, CoroutineName(com.intellij.execution.wsl.ProductionWslIjentManager), StandaloneCoroutine{Cancelled}@16a1d587, Dispatchers.Default]

目前阶段：
✅ 提取成功

DocType: contract | Confidence: 0.9
文档类型：contract |置信度：0.9

📜 修武县七贤镇崔庄一带历史遗留废弃矿山生态修复治理项目设计施工（EPC）总承包工程总承包合同

甲方

然自发包人（甲方）：修武
乙方

河南省地矿建设工程（集团）有限公司
风险条款摘要:

合同中规定了不可抗力、履约保函、支付保函、预付款保函等条款，并对缺陷责任保修金的暂扣与支付进行了约定。

🔍 查看原始 JSON




day6:
db+history api使用，项目持久化升级


day7:docker部署
多任务
这意味着我们的架构将从：
File Upload -> OCR (阻塞) -> LLM (阻塞) -> DB
进化为：
File Upload -> 存文件到共享卷 -> 丢任务给 Celery -> 立刻返回 ID
Worker -> 从共享卷读文件 -> OCR -> LLM -> DB -> 状态更新


基础设施：配置 docker-compose.yml 添加 Redis 和 Celery Worker。
共享存储：配置 Docker Volume，让 API 容器存文件，Worker 容器取文件。
API 改造：上传接口不再做 OCR，只存文件 + 发任务。
Worker 实现：真正的脏活累活都在这里干 (OCR + LLM)。



Phase 1: Persistence (持久化)

Task 1: SQLite 集成。把提取记录存下来。0
Task 2: 前端“编辑”功能。允许用户修改提取错误的字段并保存。0


Phase 2: Scalability (扩展性)

Task 3: Docker 化。一键部署。0
Task 4: 异步队列 (Celery)。解决大文件处理阻塞问题。0


Phase 3: Integration (集成)

Task 5: 批量处理与导出。上传 10 个文件，下载 1 个 Excel。
Task 6: API Webhook。提取完自动推送到外部系统。(这里先只开放接口，URL随个人需求而定)



