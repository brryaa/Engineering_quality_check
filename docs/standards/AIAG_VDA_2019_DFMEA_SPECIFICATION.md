# AIAG & VDA 2019 DFMEA 行动优先级 (Action Priority) 权威标准规范

## 1. 标准来源与出处声明

* **标准全称**：AIAG & VDA FMEA Handbook (Failure Mode and Effects Analysis), 1st Edition
* **发布机构**：
  * **AIAG** (Automotive Industry Action Group, 北美汽车工业行动小组)
  * **VDA** (Verband der Automobilindustrie, 德国汽车工业协会质量管理中心)
* **发布时间**：2019 年 10 月正式生效
* **章节出处**：Chapter 5: Design FMEA (DFMEA), Section 5.5: Risk Analysis, **Table DFMEA AP (Table B)**
* **基准数据表文件**：[`docs/standards/AIAG_VDA_2019_DFMEA_TABLE_B.json`](file:///home/brrr/agy/Engineering_quality_check/docs/standards/AIAG_VDA_2019_DFMEA_TABLE_B.json)

---

## 2. 替代传统 RPN 的行业背景与数学机理

传统汽车 QS-9000 / AIAG 第 4 版 FMEA 采用单纯乘积法：
$$\text{RPN} = \text{Severity} \times \text{Occurrence} \times \text{Detection} \quad (\in [1, 1000])$$

该公式存在严重工程缺陷：
1. **风险不对等性**：$S=10, O=2, D=2 \implies \text{RPN}=40$；而 $S=2, O=5, D=4 \implies \text{RPN}=40$。前者涉及严重人身安全与法规违规，后者仅为次要异响微瑕，乘积法导致资源配置失当。
2. **掩盖高严重度**：团队可通过调高探测度手段（如增加人工检验）人为降低 RPN 至 100 阈值以下，忽视根本设计缺陷。

**2019 版 AP (Action Priority) 查表法**：
建立三维非对称决策空间，严格遵循优先级法则：
$$\text{Severity (S)} \gg \text{Occurrence (O)} \gg \text{Detection (D)}$$
- **High (H - 红色)**：强制必须采取改进对策，否则无法通过质量评审与 PPAP。
- **Medium (M - 黄色)**：建议采取改进措施，若不实施必须书面提供充分技术合理性解释。
- **Low (L - 绿色)**：风险可接受，通常无需强制改进。

---

## 3. 权威 Table B 组合离散分布空间

全离散组合空间大小为 $10 \times 10 \times 10 = 1,000$ 个单元格，标准严格划分如下：

| 严重度区间 (Severity) | 频度区间 (Occurrence) | 探测度判定 (Detection) | 行动优先级 (AP) | 单元格总数 |
| :--- | :--- | :--- | :---: | :---: |
| **S = 9 ~ 10** (法规/安全失效) | O = 8 ~ 10 (极高频) | D = 1 ~ 10 | **High (H)** | 60 |
| | O = 6 ~ 7 (高频) | D = 1 ~ 10 | **High (H)** | 40 |
| | O = 4 ~ 5 (中频) | D = 7 ~ 10 <br> D = 2 ~ 6 <br> D = 1 | **High (H)** <br> **Medium (M)** <br> **Low (L)** | 16 <br> 20 <br> 4 |
| | O = 2 ~ 3 (低频) | D = 5 ~ 10 <br> D = 1 ~ 4 | **Medium (M)** <br> **Low (L)** | 24 <br> 16 |
| | O = 1 (极低频) | D = 1 ~ 10 | **Low (L)** | 20 |
| **S = 7 ~ 8** (主要功能丧失) | O = 8 ~ 10 | D = 1 ~ 10 | **High (H)** | 60 |
| | O = 6 ~ 7 | D = 5 ~ 10 <br> D = 1 ~ 4 | **High (H)** <br> **Medium (M)** | 24 <br> 16 |
| | O = 4 ~ 5 | D = 7 ~ 10 <br> D = 2 ~ 6 <br> D = 1 | **High (H)** <br> **Medium (M)** <br> **Low (L)** | 16 <br> 20 <br> 4 |
| | O = 2 ~ 3 | D = 7 ~ 10 <br> D = 1 ~ 6 | **Medium (M)** <br> **Low (L)** | 16 <br> 24 |
| | O = 1 | D = 1 ~ 10 | **Low (L)** | 20 |
| **S = 4 ~ 6** (次要功能降级) | O = 8 ~ 10 | D = 7 ~ 10 <br> D = 1 ~ 6 | **High (H)** <br> **Medium (M)** | 36 <br> 54 |
| | O = 6 ~ 7 | D = 5 ~ 10 <br> D = 1 ~ 4 | **Medium (M)** <br> **Low (L)** | 36 <br> 24 |
| | O = 4 ~ 5 | D = 7 ~ 10 <br> D = 1 ~ 6 | **Medium (M)** <br> **Low (L)** | 24 <br> 36 |
| | O = 2 ~ 3 | D = 1 ~ 10 | **Low (L)** | 60 |
| | O = 1 | D = 1 ~ 10 | **Low (L)** | 30 |
| **S = 2 ~ 3** (微瑕疵/感官不良) | O = 8 ~ 10 | D = 7 ~ 10 <br> D = 1 ~ 6 | **Medium (M)** <br> **Low (L)** | 24 <br> 36 |
| | O = 1 ~ 7 | D = 1 ~ 10 | **Low (L)** | 140 |
| **S = 1** (无感知影响) | O = 1 ~ 10 | D = 1 ~ 10 | **Low (L)** | 100 |

### 权威基准总计：
* **High (高优先级)**：$116 + 100 + 36 + 0 + 0 = \mathbf{252}$ 种
* **Medium (中优先级)**：$44 + 52 + 114 + 24 + 0 = \mathbf{234}$ 种
* **Low (低优先级)**：$40 + 48 + 150 + 176 + 100 = \mathbf{514}$ 种
* **总体组合总计**：$252 + 234 + 514 = \mathbf{1,000}$ 种

---

## 4. 自动化测试对齐验证

测试文件 [`backend/tests/test_dfmea_1000_combinations.py`](file:///home/brrr/agy/Engineering_quality_check/backend/tests/test_dfmea_1000_combinations.py) 直接读取 [`AIAG_VDA_2019_DFMEA_TABLE_B.json`](file:///home/brrr/agy/Engineering_quality_check/docs/standards/AIAG_VDA_2019_DFMEA_TABLE_B.json) 基准表，对引擎输出进行非自证、非自指的绝对等值断言：
```python
assert calculate_action_priority(s, o, d) == ground_truth["lookup_cells"][f"{s},{o},{d}"]
```
确保系统输出与 AIAG & VDA 2019 手册 Table B 100% 毫无偏差。
