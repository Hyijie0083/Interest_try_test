# Mass-Univariate Analysis 通俗解释

## 一、从最简单的例子开始

### 场景设定

想象你在做一个简单的实验：

- 给被试看不同**亮度**的图片
- 记录他们看图片时的EEG信号
- 你想知道：**亮度是否影响大脑活动？**

### 传统方法：选择特定电极和时间

```matlab
% 传统做法：你提前决定分析哪个电极、哪个时间点
electrode = 'Pz';        % 顶叶电极
time_window = [300:500]; % 刺激后300-500ms (P3成分)

% 提取这个电极在这个时间窗口的平均信号
signal = mean(EEG(Pz, 300:500, :), 2);  % 所有试次的平均

% 与亮度做相关
correlation = corr(signal, brightness);
```

**问题**：

- 你怎么知道Pz就是正确的电极？
- 你怎么知道300-500ms就是正确的时间窗口？
- 如果真正的效应在Oz电极、200-400ms呢？
- 这就是**确认偏误**（confirmation bias）

***

## 二、Mass-Univariate的解决方案

### 核心思想：不预设，全部分析

```
传统方法：
"我觉得效应应该在Pz电极、300-500ms"
→ 只分析这一个点
→ 可能错过真正的效应

Mass-Univariate：
"我不知道效应在哪里，让我全部检查一遍"
→ 分析所有电极 × 所有时间点
→ 让数据告诉你答案
```

### 具体做法——***所有试次在这个时间点和这个电极上和刺激相关，说明这个电极这个时间点和刺激有关系***

```matlab
% 假设你有：
% - 64个电极
% - 1000个时间点（-200ms到1800ms）
% - 100个试次

% Mass-Univariate的做法：
for electrode = 1:64           % 对每个电极
    for timepoint = 1:1000     % 对每个时间点
        
        % 提取该电极该时间点的所有试次数据
        Y = EEG(electrode, timepoint, :);  % 100个试次的信号值
        
        % 与亮度做回归
        X = brightness;  % 100个试次的亮度值
        
        beta(electrode, timepoint) = regress(Y, X);
        
    end
end

% 结果：得到一个 64×1000 的beta矩阵
```

***

## 三、用真实数据举例

### 数据结构

```
EEG数据维度：
- 64个电极 (Fp1, Fp2, Fz, Cz, Pz, Oz, ...)
- 1000个时间点 (-200ms 到 1800ms，采样率500Hz)
- 100个试次

行为数据：
- 每个试次的亮度评分 (1-7分)
```

### 第一步：选择一个电极和一个时间点

```
假设我们看 Pz电极，时间点 = 400ms

数据：
试次1: EEG(Pz, 400ms) = 2.3 μV, 亮度 = 5
试次2: EEG(Pz, 400ms) = 1.8 μV, 亮度 = 3
试次3: EEG(Pz, 400ms) = 3.1 μV, 亮度 = 7
...
试次100: EEG(Pz, 400ms) = 2.5 μV, 亮度 = 4

散点图：
    EEG (μV)
    4 |              *
    3 |          *
    2 |      *
    1 |  *
    0 +----------------
      1   3   5   7  亮度

回归分析：
EEG = β₀ + β₁ × 亮度 + ε

结果：
β₁ = 0.35  (亮度每增加1分，EEG增加0.35μV)
p = 0.02   (统计显著)
```

### 第二步：对所有电极和时间点重复

```
现在我们把这个分析重复 64×1000 = 64,000 次！

结果矩阵 beta(64, 1000)：

时间 (ms)
     -200  0   200  400  600  800  1000 1200 1400 1600 1800
电 ┌────────────────────────────────────────────────────────┐
极 │ 0.01 0.02 0.05 0.12 0.15 0.08 0.03 0.02 0.01 0.00 0.01│ Fp1
   │ 0.02 0.03 0.08 0.18 0.22 0.12 0.05 0.03 0.02 0.01 0.02│ Fz
   │ 0.01 0.02 0.06 0.15 0.20 0.10 0.04 0.02 0.01 0.01 0.01│ Cz
   │ 0.00 0.01 0.10 0.45 0.52 0.28 0.08 0.03 0.01 0.00 0.00│ Pz  ← 这里最大！
   │ 0.01 0.02 0.08 0.38 0.48 0.25 0.07 0.02 0.01 0.01 0.01│ POz
   │ 0.00 0.01 0.05 0.25 0.30 0.15 0.04 0.02 0.01 0.00 0.00│ Oz
   └────────────────────────────────────────────────────────┘

可视化：
- 颜色深浅代表beta值大小
- 可以看到Pz电极在400-600ms有最强的效应
```

***

## 四、统计检验的问题

### 多重比较问题

```
问题：我们做了64,000次统计检验！

如果显著性水平 α = 0.05：
- 即使没有真实效应，也会有 64,000 × 0.05 = 3,200 个假阳性！

类比：
如果你扔64,000次硬币，即使硬币是公平的，
也会有大约32,000次正面朝上。
你不能因为看到32,000次正面就说硬币有问题。
```

### 解决方案：Cluster-based Permutation Test

**核心思想**：真实的效应应该在时间和空间上连续

```
假阳性（噪声）：
时间:  0   100  200  300  400  500  600  700  800
Pz:   [0] [0] [1] [0] [0] [0] [1] [0] [0]  ← 零散分布
      ↑                   ↑
      假阳性              假阳性

真实效应：
时间:  0   100  200  300  400  500  600  700  800
Pz:   [0] [0] [0.2][0.8][1.0][0.9][0.3][0] [0]  ← 连续分布
              └─────────────────────┘
                   真实的cluster
```

### 具体步骤

```matlab
% 步骤1: 找到显著的电极-时间点
threshold = p < 0.001;  % 严格的阈值
significant_points = t_map > threshold;

% 步骤2: 将相邻的显著点组成cluster
clusters = find_clusters(significant_points, connection_matrix);

% 例如：
Cluster 1:
  - 电极: Pz, POz, Oz
  - 时间: 350-650ms
  - 大小: 3个电极 × 300ms × 500Hz = 450个点
  - 质量: sum(|t-values|) = 125.6

% 步骤3: 置换检验（构建零分布）
for i = 1:1000
    % 随机打乱被试标签
    shuffled_labels = shuffle(subject_labels);
    
    % 重新计算t_map
    t_map_shuffled = compute_t_map(data, shuffled_labels);
    
    % 找到最大的cluster
    clusters_shuffled = find_clusters(t_map_shuffled);
    max_cluster_mass(i) = max(clusters_shuffled.mass);
end

% 步骤4: 确定显著性阈值
threshold = percentile(max_cluster_mass, 97.5);

% 步骤5: 判断哪些cluster是显著的
if cluster.mass > threshold
    这个cluster是统计显著的
end
```

***

## 五、完整例子：亮度实验

### 实验设计

```
被试: 20人
试次: 每人100试次
刺激: 不同亮度的图片 (1-7分)
EEG: 64电极，记录-200到1800ms
```

### Mass-Univariate分析流程

#### 步骤1: 数据准备

```matlab
% EEG数据结构
EEG = [64 electrodes × 1000 timepoints × 2000 trials];
% trials = 20 subjects × 100 trials/subject

% 行为数据
brightness = [2000 × 1];  % 每个试次的亮度评分
subject_id = [2000 × 1];  % 每个试次的被试ID
```

#### 步骤2: 对每个电极-时间点回归

```matlab
for electrode = 1:64
    for timepoint = 1:1000
        
        % 提取数据
        Y = squeeze(EEG(electrode, timepoint, :));  % [2000 × 1]
        
        % 构建设计矩阵
        X = [ones(2000,1), brightness, subject_dummies];
        % 包含截距、亮度、被试哑变量（控制被试间差异）
        
        % 回归
        [beta, ~, ~, ~, stats] = regress(Y, X);
        
        % 保存结果
        beta_map(electrode, timepoint) = beta(2);  % 亮度的系数
        t_map(electrode, timepoint) = stats.tstat(2);
        p_map(electrode, timepoint) = stats.pval(2);
        
    end
end
```

#### 步骤3: 可视化结果

```matlab
% 热图：电极 × 时间
figure;
imagesc(timepoints, 1:64, t_map);
colorbar;
xlabel('Time (ms)');
ylabel('Electrode');
title('T-values for Brightness Effect');

% 拓扑图：某个时间点
figure;
timepoint = 450;  % 450ms
topoplot(t_map(:, timepoint), chanlocs);
title('Topography at 450ms');
```

#### 步骤4: Cluster-based检验

```matlab
% 找cluster
threshold = 0.001;  % p < 0.001
clusters = find_clusters(t_map, threshold, connection_matrix);

% 置换检验
n_perm = 1000;
for perm = 1:n_perm
    % 打乱亮度标签（在被试内）
    brightness_shuffled = shuffle_within_subject(brightness, subject_id);
    
    % 重新计算t_map
    t_map_perm = compute_t_map(EEG, brightness_shuffled);
    
    % 找最大cluster
    clusters_perm = find_clusters(t_map_perm, threshold);
    max_mass(perm) = max([clusters_perm.mass]);
end

% 确定阈值
significance_threshold = prctile(max_mass, 97.5);

% 识别显著cluster
significant_clusters = clusters([clusters.mass] > significance_threshold);
```

#### 步骤5: 报告结果

```
结果：
发现1个显著的cluster：
- 电极: Pz, POz, Oz, P1, P2 (5个电极)
- 时间窗口: 380-620ms (240ms)
- 峰值: Pz电极, 450ms
- 统计量: cluster mass = 156.2, p = 0.003

解释：
亮度显著影响顶叶电极在380-620ms的EEG活动，
峰值在Pz电极450ms，这可能是P3成分。
```

***

## 六、为什么叫"Mass-Univariate"？

### 名称解析

```
Mass (大规模):
- 分析成千上万个数据点
- 64电极 × 1000时间点 = 64,000个分析
- "大规模"指的是分析的数量

Univariate (单变量):
- 每次分析只看一个数据点
- 每个电极-时间点独立分析
- 不考虑它们之间的关系

对比：
Multivariate (多变量):
- 同时考虑多个电极和时间点
- 例如PCA、机器学习等
- 更复杂，但可能更强大
```

### 与其他方法的对比

```
1. ROI分析 (Region of Interest)
   - 只分析预先选择的电极/时间
   - 优点：简单，统计检验少
   - 缺点：可能错过效应，有偏倚

2. Mass-Univariate
   - 分析所有电极/时间
   - 优点：无偏，可以发现意外效应
   - 缺点：需要多重比较校正

3. Multivariate
   - 同时分析所有数据
   - 优点：可以考虑时空关系
   - 缺点：复杂，难以解释
```

***

## 七、实际应用场景

### 适合用Mass-Univariate的情况

```
1. 探索性研究
   - 不知道效应在哪里
   - 想发现新的ERP成分

2. 验证性研究
   - 复制前人发现
   - 但不预设精确的时空位置

3. 全脑/全头分析
   - 不想遗漏任何可能的效应
   - 需要完整的时空图
```

### 不适合的情况

```
1. 有明确假设
   - 已知效应在Pz, 300-500ms
   - 直接用ROI分析更高效

2. 试次太少
   - Mass-Univariate需要大量试次
   - 至少每个被试30-50试次

3. 需要精细时间分辨率
   - Mass-Univariate假设效应持续一段时间
   - 瞬时效应可能被平滑掉
```

***

## 八、总结

### Mass-Univariate的本质

```
传统方法：
"我猜效应在这里" → 只分析一个点 → 可能错过真相

Mass-Univariate：
"我不知道效应在哪里" → 分析所有点 → 让数据说话
```

### 核心步骤

```
1. 对每个电极-时间点做回归
   → 得到64,000个beta值

2. 找到显著的时空cluster
   → 利用时空连续性

3. 置换检验校正
   → 控制多重比较

4. 报告显著cluster
   → 电极范围、时间窗口、统计量
```

### 优缺点

```
优点：
✓ 无偏探索
✓ 可以发现意外效应
✓ 提供完整时空图
✓ 统计严谨（cluster校正）

缺点：
✗ 计算量大
✗ 需要大量试次
✗ 可能错过瞬时效应
✗ 结果解释需要谨慎
```

### 在CPP研究中的应用

```
这个研究用Mass-Univariate：
1. 分析所有电极 × 所有时间点
2. 找到与决策变量相关的cluster
3. 发现传统方法会得到"CPP与决策相关"的结果
4. 但这个结果可能是RT混淆导致的！

这就是为什么需要第二条管线（Unfold）来验证。
```

***

## 九、代码示例（完整可运行）

```matlab
%% 模拟数据
n_electrodes = 64;
n_timepoints = 1000;
n_subjects = 20;
n_trials_per_subject = 100;
n_total_trials = n_subjects * n_trials_per_subject;

% 生成模拟EEG数据
EEG = randn(n_electrodes, n_timepoints, n_total_trials);

% 添加真实效应（Pz电极，400-600ms）
Pz = 50;  % Pz是第50个电极
time_effect = 400:600;
for trial = 1:n_total_trials
    brightness = rand() * 6 + 1;  % 1-7分
    EEG(Pz, time_effect, trial) = EEG(Pz, time_effect, trial) + brightness * 0.5;
end

% 行为数据
brightness_values = rand(n_total_trials, 1) * 6 + 1;
subject_ids = repmat(1:n_subjects, n_trials_per_subject, 1);
subject_ids = subject_ids(:);

%% Mass-Univariate分析
beta_map = zeros(n_electrodes, n_timepoints);
t_map = zeros(n_electrodes, n_timepoints);

for elec = 1:n_electrodes
    for time = 1:n_timepoints
        Y = squeeze(EEG(elec, time, :));
        X = [ones(n_total_trials, 1), brightness_values];
        
        [b, bint, r, rint, stats] = regress(Y, X);
        
        beta_map(elec, time) = b(2);
        t_map(elec, time) = stats(3);
    end
end

%% 可视化
figure;
subplot(2,1,1);
imagesc(-200:2:1798, 1:64, t_map);
colorbar;
xlabel('Time (ms)');
ylabel('Electrode');
title('T-map');

subplot(2,1,2);
plot(-200:2:1798, t_map(Pz, :), 'LineWidth', 2);
xlabel('Time (ms)');
ylabel('T-value');
title('Pz Electrode');
```

***

## 十、关键要点

1. **Mass-Univariate = 对每个数据点独立分析**
   - 不是复杂的多变量方法
   - 就是简单的回归，重复很多次
2. **目的 = 无偏探索**
   - 不预设效应在哪里
   - 让数据告诉你答案
3. **挑战 = 多重比较**
   - 需要cluster-based校正
   - 利用时空连续性
4. **结果 = 显著的时空cluster**
   - 报告电极范围
   - 报告时间窗口
   - 报告统计量
5. **在CPP研究中 = 传统方法**
   - 会发现CPP与决策变量相关
   - 但可能是RT混淆
   - 需要Unfold验证

