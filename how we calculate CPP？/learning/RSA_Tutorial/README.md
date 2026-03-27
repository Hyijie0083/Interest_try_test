# EEG表征相似性分析(RSA)教程

## 📚 教程概述

本教程详细介绍EEG数据处理中的**表征相似性分析(Representational Similarity Analysis, RSA)**，并提供完整的Python/MNE实现代码。

## 📁 文件结构

```
RSA_Tutorial/
├── README.md                                          # 本文件
├── Representational_Similarity_Analysis_Tutorial.md   # 详细理论教程
└── eeg_rsa_mne_demo.py                               # Python代码示例
```

## 🎯 学习目标

完成本教程后，你将能够：

1. ✅ 理解RSA的基本原理和核心概念
2. ✅ 计算表征不相似性矩阵(RDM)
3. ✅ 实现时间分辨RSA
4. ✅ 实现空间分辨RSA
5. ✅ 比较EEG RDM与模型RDM
6. ✅ 进行统计检验（置换检验、组水平分析）
7. ✅ 可视化RSA结果

## 📖 教程内容

### 1. 理论部分 (`Representational_Similarity_Analysis_Tutorial.md`)

- **第一部分**: RSA基本概念
  - 什么是RSA？
  - 为什么需要RSA？
  - 核心思想：从直接比较到相似性比较

- **第二部分**: RSA核心组件
  - 表征不相似性矩阵(RDM)
  - 不相似度的度量方法
  - RDM可视化

- **第三部分**: EEG-RSA的特殊应用
  - 时间分辨RSA
  - 空间分辨RSA
  - 时空RSA

- **第四部分**: RSA分析流程
  - 数据准备
  - RDM计算
  - RDM比较
  - 可视化

- **第五部分**: 统计检验
  - 置换检验
  - 跨被试分析
  - 多重比较校正

- **第六部分**: 高级应用
  - 搜索光分析
  - 动态RSA
  - 与深度学习模型比较

### 2. 实践部分 (`eeg_rsa_mne_demo.py`)

完整的Python代码示例，包含：

#### 第一部分: 模拟EEG数据
- 模拟10个被试的数据
- 6个视觉类别（人脸、房子、椅子、汽车、动物、工具）
- 包含典型ERP成分（P1, N1, P3）

#### 第二部分: RSA核心函数
- `compute_rdm()`: 计算RDM
- `compare_rdms()`: 比较两个RDM
- `create_model_rdm()`: 创建模型RDM

#### 第三部分: 时间分辨RSA
- 对每个时间点计算RDM
- 得到RDM的时间序列

#### 第四部分: 可视化
- ERP波形图
- RDM热图（不同时间点）
- MDS降维可视化

#### 第五部分: 与模型RDM比较
- 创建理论模型RDM
- 计算RSA相关性随时间的变化

#### 第六部分: 组水平分析
- 对多个被试进行RSA分析
- 统计检验和FDR校正

#### 第七部分: 空间分辨RSA
- 对每个电极计算RSA
- 绘制RSA拓扑图

#### 第八部分: 置换检验
- 随机打乱条件标签
- 构建零分布
- 计算p值

## 🚀 快速开始

### 环境要求

```bash
# Python版本
Python >= 3.7

# 必需的库
numpy
scipy
mne
matplotlib
seaborn
scikit-learn
```

### 安装依赖

```bash
pip install numpy scipy mne matplotlib seaborn scikit-learn
```

### 运行代码

```bash
cd learning/RSA_Tutorial
python eeg_rsa_mne_demo.py
```

### 预期输出

运行代码后，将生成以下图片：

1. **erp_waveforms.png** - 6个类别的ERP波形
2. **rdm_time_heatmaps.png** - 10个时间点的RDM热图
3. **rdm_mds.png** - MDS降维可视化（4个关键时间点）
4. **rsa_model_comparison.png** - EEG RDM与模型RDM的比较
5. **group_rsa.png** - 组水平RSA结果
6. **spatial_rsa_topomap.png** - 空间RSA拓扑图
7. **rsa_permutation_test.png** - 置换检验结果

## 📊 关键概念速查

### RDM (Representational Dissimilarity Matrix)

```
定义：N×N的对称矩阵，表示N个条件两两之间的不相似度

计算方法：
  RDM[i,j] = 1 - correlation(pattern_i, pattern_j)

特点：
  - 对角线为0（自己和自己完全相似）
  - 值越小 = 越相似
  - 值越大 = 越不相似
```

### RSA分析流程

```
1. 提取各条件的脑活动模式
   ↓
2. 计算RDM（条件两两比较）
   ↓
3. 与模型RDM比较（或与其他RDM比较）
   ↓
4. 统计检验
   ↓
5. 可视化结果
```

### 时间分辨RSA vs 空间分辨RSA

```
时间分辨RSA:
  - 对每个时间点计算RDM
  - 研究表征何时出现
  - 揭示认知过程的时序动态

空间分辨RSA:
  - 对每个电极计算RDM
  - 研究表征在哪里
  - 揭示表征的大脑位置
```

## 🔬 实际应用场景

### 1. 视觉物体识别
- 研究不同物体类别的表征
- 比较类别模型和脑活动

### 2. 语言处理
- 研究单词的语义表征
- 比较词向量模型和脑活动

### 3. 决策过程
- 研究价值表征
- 揭示决策证据累积

### 4. 记忆过程
- 研究记忆编码和提取
- 比较不同记忆状态

## 📚 推荐阅读

### 经典文献

1. **Kriegeskorte, N., Mur, M., & Bandettini, P. (2008).**
   Representational similarity analysis - connecting the branches of systems neuroscience.
   *Frontiers in Systems Neuroscience*, 2, 4.
   - RSA的开创性论文

2. **Kriegeskorte, N., & Kievit, R. A. (2013).**
   Representational geometry: An integrative framework for population codes.
   *Trends in Cognitive Sciences*, 17(10), 483-486.
   - 表征几何的理论框架

### EEG-RSA文献

3. **Cichy, R. M., Pantazis, D., & Oliva, A. (2014).**
   Resolving human object recognition in space and time.
   *Nature Neuroscience*, 17(3), 455-462.
   - EEG-fMRI融合的RSA研究

4. **Wardle, S. G., et al. (2016).**
   Perceptual similarity of visual patterns in dynamic brain activation.
   *Journal of Neuroscience*, 36(44), 11193-11202.
   - 时间分辨RSA

## 🛠️ 常用工具

### Python库

```python
# 核心库
import numpy as np
import scipy
import mne

# 可视化
import matplotlib.pyplot as plt
import seaborn as sns

# RSA专用库
from rsatoolbox import rdm, model, eval
from pyrsa import datasets, model, rdm

# 机器学习
from sklearn.manifold import MDS, TSNE
from sklearn.decomposition import PCA
```

### MATLAB工具

- **RSA Toolbox**: https://github.com/rsagroup/rsatoolbox
- **FieldTrip**: 支持RSA分析
- **BrainStorm**: 包含RSA插件

## ⚠️ 注意事项

### 数据质量
- ✅ 确保预处理充分
- ✅ 每个条件至少30试次
- ✅ 信噪比足够高

### RDM计算
- ✅ 选择合适的不相似度度量
- ✅ 考虑数据维度和归一化
- ✅ 避免过拟合

### 统计检验
- ✅ 多重比较校正
- ✅ 跨被试分析
- ✅ 报告效应量

### 结果解释
- ✅ RDM相似 ≠ 表征相同
- ✅ 注意EEG的空间分辨率限制
- ✅ RSA只能揭示相关性，不能证明因果关系

## 🎓 学习路径

### 初学者
1. 阅读 `Representational_Similarity_Analysis_Tutorial.md` 的第一、二部分
2. 运行 `eeg_rsa_mne_demo.py` 的前四部分
3. 理解RDM的概念和计算方法

### 中级
1. 完成整个教程
2. 尝试修改参数（如时间窗口、不相似度度量）
3. 应用到自己的数据

### 高级
1. 实现搜索光RSA
2. 与深度学习模型比较
3. 开发新的分析方法

## 📞 常见问题

### Q1: RDM应该用什么度量？
```
A: 取决于研究问题：
   - 相关距离：对整体幅度不敏感，适合比较模式形状
   - 余弦距离：考虑方向和幅度
   - 欧氏距离：简单直观
   推荐从相关距离开始
```

### Q2: 需要多少试次？
```
A: 建议：
   - 最少：每个条件20试次
   - 推荐：每个条件30-50试次
   - 试次太少会导致RDM不稳定
```

### Q3: 如何选择时间窗口？
```
A: 两种策略：
   1. 理论驱动：根据已知的ERP成分（如N170, P300）
   2. 数据驱动：时间分辨RSA找到峰值时间
```

### Q4: 如何解释RSA相关性？
```
A: RSA相关性表示：
   - 脑活动的表征结构与模型预测的表征结构的相似程度
   - 高相关性 = 脑活动模式符合模型预测
   - 但不能证明因果关系
```

## 🔄 更新日志

- **2024-03-27**: 初始版本发布
  - 完整的理论教程
  - Python代码示例
  - 可视化函数

## 📧 反馈与贡献

如有问题或建议，欢迎：
- 提交Issue
- 发送邮件
- 贡献代码

## 📄 许可证

本教程采用 MIT 许可证。

---

**祝你学习愉快！🎉**

如果你觉得这个教程有帮助，请给一个⭐️Star！
