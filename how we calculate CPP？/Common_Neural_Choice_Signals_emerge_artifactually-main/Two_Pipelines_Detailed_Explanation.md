# 两条分析管线详细解释

## 概述

这个研究使用了**两条并行的分析管线**来处理EEG数据，目的是揭示CPP（Centroparietal Positivity）信号的真实性质。这两条管线代表了传统方法和创新方法的对比。

---

## 管线1: Mass-Univariate Analysis（质量单变量分析）

### 一、什么是Mass-Univariate Analysis？

**Mass-Univariate**是一种对EEG数据进行大规模单变量统计分析的方法。它的核心思想是：
- 对**每个电极**、**每个时间点**分别进行回归分析
- 不做任何先验假设（如特定电极或时间窗口）
- 通过统计检验找出显著的时空模式

### 二、具体计算过程

#### 步骤1: 构建回归模型

```matlab
% 对每个被试、每个电极、每个时间点

for subj = 1:n_subjects
    for channel = 1:61  % 61个电极
        for t = timesToLookAt  % 每个时间点
            
            % 提取该电极该时间点的EEG信号（跨试次）
            Y = squeeze(downSampData(channel, t, :));  
            % Y是一个向量，长度=该被试的试次数
            
            % 构建预测变量矩阵
            xMat = [ones(n_trials, 1),         % 截距
                    bSubData.Liking/5,          % 喜好度
                    bSubData.Anxious/5,         % 焦虑度
                    bSubData.Confident/5];      % 信心度
            % 中心化处理
            xMat = meanCentX(xMat);
            
            % 执行回归
            [coeffs, CIs] = regress(Y, xMat);
            % coeffs: 回归系数 [β0, β1, β2, β3]
            % CIs: 置信区间
            
        end
    end
end
```

**数学表达**：

对于电极 c 在时间点 t：

```
EEG(c,t,trial) = β0 + β1·Liking(trial) + β2·Anxiety(trial) + β3·Confidence(trial) + ε
```

#### 步骤2: 收集回归系数

```matlab
% 结果存储为4维矩阵
sbasicCoeffs.data  % [61 electrodes × n_timepoints × n_predictors × n_subjects]
rbasicCoeffs.data  % 反应锁定的结果
prbasicCoeffs.data % 反应后的结果

% 例如：
% sbasicCoeffs.data(50, 100, 2, 15) = 0.5
% 表示：第15个被试，第50个电极，第100个时间点，第2个预测变量(Liking)的β系数是0.5
```

#### 步骤3: 统计检验（Cluster-based Permutation Test）

**为什么需要这个检验？**
- 我们有 61个电极 × 数百个时间点 = 数万个统计检验
- 如果不做校正，会有大量假阳性
- Cluster-based方法考虑了时间和空间上的连续性

**具体计算**：

```matlab
% 1. 计算t统计量图
for predictor = 1:n_predictors
    % 提取所有被试的beta系数
    beta_values = sbasicCoeffs.data(:, :, predictor, :);  
    % [electrodes × timepoints × subjects]
    
    % 单样本t检验（检验beta是否显著不为0）
    t_map = t_test(beta_values);  % [electrodes × timepoints]
end

% 2. 识别群集（clusters）
% 群集定义：相邻的电极和时间点，且t值超过阈值
threshold = 0.001;  % p < 0.001

% 正向群集
pos_clusters = find_clusters(t_map > threshold, connection_matrix);
% 负向群集  
neg_clusters = find_clusters(t_map < -threshold, connection_matrix);

% 3. 计算群集统计量
for each cluster:
    cluster_size = number of electrode-time pairs
    cluster_mass = sum(|t-values|)  % 更常用
end

% 4. 置换检验（构建零分布）
for perm = 1:1000
    % 随机翻转被试的符号
    sign_flip = random_signs(n_subjects);
    beta_permuted = beta_values .* sign_flip;
    
    % 重新计算t_map和cluster statistics
    t_map_perm = t_test(beta_permuted);
    clusters_perm = find_clusters(t_map_perm, threshold);
    
    % 记录最大的cluster mass
    max_cluster_mass(perm) = max(clusters_perm.mass);
end

% 5. 确定显著性阈值
threshold_975 = percentile(max_cluster_mass, 97.5);

% 6. 识别显著群集
significant_clusters = clusters where mass > threshold_975;
```

### 三、管线1的问题

**关键问题**：这个方法混淆了不同来源的信号！

```
问题场景：
┌────────────────────────────────────────────────────────────┐
│ 试次1: 刺激 → ... → 反应 (RT=500ms)                        │
│        |──────────────|                                    │
│           刺激锁定成分                                     │
│                                                             │
│ 试次2: 刺激 → ... → 反应 (RT=1500ms)                       │
│        |──────────────────────────────|                    │
│           刺激锁定成分（持续时间更长！）                    │
│                                                             │
│ 问题：反应锁定分析时                                        │
│ - 试次1: 反应前500ms的数据                                  │
│ - 试次2: 反应前1500ms的数据                                 │
│ - 不同RT试次包含的刺激锁定成分不同！                        │
└────────────────────────────────────────────────────────────┘
```

**具体例子**：

假设我们分析CPP（反应前700-200ms）：

```matlab
% 试次1: RT = 600ms
% 反应前700-200ms → 刺激后 -100 到 400ms
% 包含早期ERP成分（N1, P2等）

% 试次2: RT = 1500ms  
% 反应前700-200ms → 刺激后 800 到 1300ms
% 包含晚期ERP成分（P3, LPP等）

% 问题：这两个时间窗口包含完全不同的认知过程！
% 但传统方法把它们当作"相同的CPP"来分析
```

---

## 管线2: Unfold Deconvolution Analysis（解卷积分析）

### 一、什么是Deconvolution？

**Deconvolution（解卷积）**的核心思想是：
- EEG信号是多个事件相关成分的叠加
- 不同事件（刺激、反应）锁定的成分相互重叠
- 通过数学方法将这些成分分离

**类比理解**：

```
传统方法：
录音 = 人声 + 背景音乐 + 噪音
（混在一起，难以分离）

解卷积方法：
录音 = 人声(t) + 背景音乐(t) + 噪声(t)
通过已知的时间信息，分离出各个成分
```

### 二、具体计算过程

#### 步骤1: 构建设计矩阵（Design Matrix）

```matlab
% 定义事件类型
event_types = {'S 10', 'S 20'};  % S 10: 刺激, S 20: 反应

% 定义模型公式
formula = {'y ~ 1 + Appraisal + Choice',    % 刺激锁定的模型
           'y ~ 1 + Appraisal + Choice'};   % 反应锁定的模型

% 构建设计矩阵
EEG = uf_designmat(EEG, cfgDesign);
```

**设计矩阵的结构**：

```
时间点  刺激发生  反应发生  Appraisal刺激  Choice刺激  Appraisal反应  Choice反应
  1       0         0         0             0            0             0
  2       1         0        2.5           -1.2          0             0
  3       1         0        2.5           -1.2          0             0
  ...
  500     1         1        2.5           -1.2         2.5          -1.2
  ...
  1000    0         1        0              0           2.5          -1.2
```

#### 步骤2: 时间展开（Time Expansion）

```matlab
% 为每个事件类型定义时间窗口
timelimits = [-2, 2];  % 事件前后2秒

% 使用Fourier基函数展开
method = 'fourier';
timeshiftparam = 20;  % 20个基函数

EEG = uf_timeexpandDesignmat(EEG, cfgTimeexpand);
```

**为什么需要时间展开？**

```
传统回归假设：
Y(t) = β·X(t)  % 瞬时效应

但ERP有时间过程：
Y(t) = β(t-τ)·X(τ)  % τ时刻的事件影响t时刻的信号

时间展开将每个预测变量扩展为时间序列：
X → [X(t-2s), X(t-1.9s), ..., X(t+2s)]
```

**数学表达**：

```
EEG(t) = Σ β_stim(τ)·X_stim(t-τ) + Σ β_resp(τ)·X_resp(t-τ) + ε
         τ=-2s→2s                    τ=-2s→2s

其中：
- β_stim(τ): 刺激锁定成分在时刻τ的幅度
- β_resp(τ): 反应锁定成分在时刻τ的幅度
- X_stim, X_resp: 指示函数（事件是否发生）
```

#### 步骤3: 解卷积拟合

```matlab
% 拟合GLM模型
EEG = uf_glmfit(EEG);

% 这会估计每个事件类型的每个预测变量的时间序列
% 结果：beta系数 [electrodes × timepoints × predictors × event_types]
```

**拟合过程**：

```
最小化误差：
min ||EEG_observed - EEG_predicted||²

其中：
EEG_predicted = DesignMatrix × Beta

解：
Beta = (X'X)^(-1) X' Y
```

#### 步骤4: 提取分离的成分

```matlab
% 提取刺激锁定的beta系数
beta_stim = ufresult.beta(:, :, 1:3);  
% [electrodes × timepoints × 3 predictors]
% 时间窗口: -200ms 到 1500ms (相对于刺激)

% 提取反应锁定的beta系数  
beta_resp = ufresult.beta(:, :, 4:6);
% [electrodes × timepoints × 3 predictors]
% 时间窗口: -1500ms 到 200ms (相对于反应)
```

### 三、Unfold的关键优势

#### 优势1: 分离重叠成分

```
传统方法看到的：
┌─────────────────────────────────────┐
│ 反应锁定数据 = 刺激成分 + 反应成分  │
│ （混在一起，无法区分）              │
└─────────────────────────────────────┘

Unfold分离后：
┌─────────────────────────────────────┐
│ 刺激锁定成分: N1, P2, P3, ...       │
│ 反应锁定成分: CPP, RP, ...          │
│ （清晰分离）                        │
└─────────────────────────────────────┘
```

#### 优势2: 控制RT的影响

```matlab
% 传统方法的问题
for trial = 1:n_trials
    RT = reaction_time(trial);
    % 反应前700-200ms的窗口
    window = [-700:-200] + RT;  % 相对于刺激的时间
    
    % 不同RT试次，这个窗口包含不同的刺激锁定成分！
    if RT < 700
        % 窗口在刺激前或刺激早期
        % 包含基线或早期ERP
    else
        % 窗口在刺激晚期
        % 包含P3等晚期成分
    end
end

% Unfold的解决方案
% 在拟合时同时考虑刺激和反应事件
% 自动分离它们的贡献
beta_stim = 纯净的刺激锁定成分
beta_resp = 纯净的反应锁定成分（已去除刺激成分的污染）
```

#### 优势3: 处理连续变量

```matlab
% 传统方法：需要将连续变量分箱
RT_bins = discretize(RT, [0, 500, 1000, 1500, 2000]);

% Unfold：可以直接使用连续变量
% 甚至可以包含多个连续变量的交互作用
formula = 'y ~ 1 + Appraisal + Choice + RT + Appraisal:RT';
```

---

## 两者的对比

### 计算复杂度对比

```
管线1 (Mass-Univariate):
- 计算量: O(n_electrodes × n_timepoints × n_subjects)
- 每个电极×时间点独立回归
- 相对简单，计算快

管线2 (Unfold):
- 计算量: O(n_timepoints × n_events × n_basis_functions)³
- 需要求解大型线性系统
- 计算量大，需要优化算法
```

### 结果解释对比

```
管线1结果:
- beta(electrode, time, predictor)
- 代表该电极该时间点与预测变量的关系
- 但混淆了刺激和反应成分

管线2结果:
- beta_stim(electrode, time, predictor)  % 纯刺激锁定
- beta_resp(electrode, time, predictor)  % 纯反应锁定
- 清晰分离，可独立解释
```

### 对CPP研究的影响

```
管线1的发现:
"CPP与决策变量显著相关"
- 但这个关系可能是虚假的
- 因为混淆了RT的影响

管线2的发现:
"控制RT和刺激成分后，CPP与决策变量的关系消失"
- 揭示了CPP信号的真实性质
- CPP可能主要反映RT相关的伪迹，而非决策累积
```

---

## 为什么需要两条管线？

### 科学严谨性

```
┌────────────────────────────────────────────────────────┐
│ 1. 复制传统分析                                        │
│    - 证明我们能够得到与前人相同的结果                  │
│    - 确认我们的数据和基本分析是正确的                  │
│                                                         │
│ 2. 应用新方法                                          │
│    - 使用Unfold重新分析                                │
│    - 发现传统方法的局限性                              │
│                                                         │
│ 3. 对比结果                                            │
│    - 传统方法: CPP与决策变量相关                       │
│    - 新方法: 控制混淆后关系消失                        │
│    - 强有力的证据证明之前的发现是伪迹                  │
└────────────────────────────────────────────────────────┘
```

### 方法论贡献

```
这篇论文的核心贡献不仅是发现CPP可能是伪迹
更重要的是展示了如何正确分析反应锁定的EEG数据

传统方法的问题：
- 反应锁定 ≠ 纯净的决策信号
- 需要考虑刺激成分的混叠
- 需要控制RT的影响

正确方法：
- 使用解卷积分离成分
- 同时建模刺激和反应事件
- 控制RT等混淆变量
```

---

## 具体例子：CPP分析

### 传统方法（管线1）

```matlab
% 1. 提取反应锁定数据
data = DATR2;  % [61 electrodes × 2800 timepoints × n_trials]

% 2. 选择时间窗口和电极
time_window = [-700:-200];  % 反应前700-200ms
electrodes = [Pz];  % Pz电极

% 3. 计算平均幅度
CPP_signal = mean(data(electrodes, time_window, :), 2);

% 4. 与行为变量回归
model = regress(CPP_signal, [ones, ValueDifference, RT]);

% 5. 结果：CPP与ValueDifference显著相关
% 但这可能是因为RT的混淆！
```

### Unfold方法（管线2）

```matlab
% 1. 构建包含刺激和反应事件的模型
formula = {'y ~ 1 + VD + RT',    % 刺激事件
           'y ~ 1 + VD + RT'};   % 反应事件

% 2. 解卷积拟合
beta = uf_glmfit(EEG, formula);

% 3. 提取纯净的反应锁定成分
beta_resp_pure = beta(:, :, 'response', 'VD');

% 4. 结果：控制RT后，CPP与ValueDifference的关系不显著
% 证明之前的发现是RT混淆导致的
```

---

## 总结

### 管线1: Mass-Univariate
- **目的**: 传统分析，复制前人结果
- **方法**: 对每个电极×时间点独立回归
- **问题**: 混淆刺激和反应成分，受RT影响
- **结果**: 发现CPP与决策变量相关（可能是伪迹）

### 管线2: Unfold Deconvolution
- **目的**: 正确分析，分离混淆因素
- **方法**: 解卷积分离刺激和反应锁定的成分
- **优势**: 控制RT，获得纯净的信号
- **结果**: 揭示CPP可能主要反映RT相关的伪迹

### 关键启示
**两条管线的对比**强有力地证明了：
1. 传统方法可能产生误导性结果
2. 反应锁定分析需要考虑刺激成分的混叠
3. RT是一个重要的混淆变量
4. 解卷积是分析决策相关EEG信号的正确方法
