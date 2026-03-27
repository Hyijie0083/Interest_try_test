# Cluster-based Permutation Test 详解

## 一、为什么需要这个方法？

### 问题：多重比较

假设你做了一个EEG实验，分析64个电极在1000个时间点的数据：

```
总共有多少次比较？
64个电极 × 1000个时间点 = 64,000次统计检验

如果显著性水平 α = 0.05：
即使没有任何真实效应，也会有 64,000 × 0.05 = 3,200 个假阳性！

这就像：
- 扔64,000次硬币
- 即使硬币是公平的，也会有约32,000次正面
- 你不能说"看！有32,000次正面，这硬币有问题！"
```

### 传统校正方法的问题

#### 方法1: Bonferroni校正

```python
# 最严格的校正
alpha_corrected = 0.05 / 64000  # = 0.00000078

# 问题：太严格了！
# 真实的效应也可能被剔除
```

#### 方法2: FDR (False Discovery Rate)

```python
# 控制假阳性比例
# 问题：没有考虑数据的时空结构
```

### Cluster-based的优势

**核心思想**：真实的效应应该在时间和空间上**连续**！

```
假阳性（噪声）：
时间:  0   100  200  300  400  500  600  700  800
Pz:   [0] [0] [1] [0] [0] [0] [1] [0] [0]
      ↑                   ↑
      孤立的点            孤立的点
      (随机噪声)

真实效应：
时间:  0   100  200  300  400  500  600  700  800
Pz:   [0] [0] [0.2][0.8][1.0][0.9][0.3][0] [0]
              └─────────────────────┘
                   连续的cluster！
              (真实的神经活动)
```

---

## 二、核心原理

### 三个关键概念

#### 1. Cluster（群集）

```
定义：相邻的、显著的数据点组成的集合

相邻的定义：
- 时间相邻：时间点t和t+1
- 空间相邻：电极A和电极B在头皮上距离<40mm
- 时空相邻：同时满足时间和空间相邻
```

#### 2. Cluster Mass（群集质量）

```
Cluster Mass = Σ |t-values|  (对所有cluster内的点求和)

为什么用mass而不是size？
- Mass考虑了效应的强度
- 一个小但很强的cluster可能比一个大但很弱的cluster更重要
```

#### 3. Permutation（置换）

```
通过随机打乱数据构建"零分布"
- 在零假设下（没有真实效应），数据标签可以随机打乱
- 打乱后重新计算统计量
- 重复很多次，得到统计量的分布
```

---

## 三、详细步骤

### 步骤概览

```
步骤1: 计算真实数据的t统计量图
步骤2: 设定阈值，找到显著的点
步骤3: 将相邻的显著点组成cluster
步骤4: 计算每个cluster的mass
步骤5: 置换检验（构建零分布）
步骤6: 确定显著性阈值
步骤7: 判断哪些cluster是显著的
```

### 步骤详解

#### 步骤1: 计算t统计量图

```python
import numpy as np
from scipy import stats

# 假设数据维度
# data: [n_subjects, n_electrodes, n_timepoints, n_conditions]

# 对每个电极-时间点做t检验
n_electrodes = 64
n_timepoints = 1000
n_subjects = 20

# 真实数据
condition_A = np.random.randn(n_subjects, n_electrodes, n_timepoints)  # 条件A
condition_B = np.random.randn(n_subjects, n_electrodes, n_timepoints)  # 条件B

# 计算t统计量
t_map = np.zeros((n_electrodes, n_timepoints))
p_map = np.zeros((n_electrodes, n_timepoints))

for elec in range(n_electrodes):
    for t in range(n_timepoints):
        # 提取该电极该时间点的所有被试数据
        data_A = condition_A[:, elec, t]
        data_B = condition_B[:, elec, t]
        
        # 配对t检验
        t_stat, p_val = stats.ttest_rel(data_A, data_B)
        t_map[elec, t] = t_stat
        p_map[elec, t] = p_val
```

#### 步骤2: 设定阈值

```python
# 群集形成阈值（cluster-forming threshold）
alpha_cluster = 0.001  # p < 0.001

# 找到显著的点
significant_mask = p_map < alpha_cluster

# 或者用t值阈值
t_threshold = stats.t.ppf(1 - alpha_cluster/2, df=n_subjects-1)
significant_mask_pos = t_map > t_threshold   # 正向显著
significant_mask_neg = t_map < -t_threshold  # 负向显著
```

#### 步骤3: 找cluster

```python
from scipy.ndimage import label

# 定义连接结构（哪些点算"相邻"）
# 对于时间序列：每个点与前后相邻
# 对于电极：需要根据电极位置定义

# 简化版：只考虑时间相邻
structure = np.array([[0, 1, 0],
                      [1, 1, 1],
                      [0, 1, 0]])  # 上下左右相邻

# 找到正向cluster
labeled_pos, n_clusters_pos = label(significant_mask_pos, structure=structure)

# 找到负向cluster
labeled_neg, n_clusters_neg = label(significant_mask_neg, structure=structure)

print(f"找到 {n_clusters_pos} 个正向cluster")
print(f"找到 {n_clusters_neg} 个负向cluster")
```

#### 步骤4: 计算cluster mass

```python
def compute_cluster_mass(labeled_map, t_map, n_clusters):
    """
    计算每个cluster的mass
    
    参数:
        labeled_map: 标记了cluster ID的图
        t_map: t统计量图
        n_clusters: cluster数量
    
    返回:
        cluster_masses: 每个cluster的mass
        cluster_info: 每个cluster的详细信息
    """
    cluster_masses = []
    cluster_info = []
    
    for cluster_id in range(1, n_clusters + 1):
        # 找到属于该cluster的所有点
        cluster_mask = labeled_map == cluster_id
        
        # 计算mass = sum(|t|)
        mass = np.sum(np.abs(t_map[cluster_mask]))
        
        # 记录信息
        electrodes, timepoints = np.where(cluster_mask)
        info = {
            'id': cluster_id,
            'mass': mass,
            'size': np.sum(cluster_mask),
            'electrodes': electrodes,
            'timepoints': timepoints,
            'peak_t': np.max(np.abs(t_map[cluster_mask]))
        }
        
        cluster_masses.append(mass)
        cluster_info.append(info)
    
    return cluster_masses, cluster_info

# 计算正向cluster的mass
pos_masses, pos_info = compute_cluster_mass(labeled_pos, t_map, n_clusters_pos)

# 计算负向cluster的mass
neg_masses, neg_info = compute_cluster_mass(labeled_neg, t_map, n_clusters_neg)
```

#### 步骤5: 置换检验

```python
def permutation_test(condition_A, condition_B, n_permutations=1000, 
                     alpha_cluster=0.001):
    """
    置换检验构建零分布
    
    参数:
        condition_A: 条件A数据 [n_subjects, n_electrodes, n_timepoints]
        condition_B: 条件B数据 [n_subjects, n_electrodes, n_timepoints]
        n_permutations: 置换次数
        alpha_cluster: 群集形成阈值
    
    返回:
        null_distribution: 零分布（最大cluster mass的分布）
    """
    n_subjects = condition_A.shape[0]
    n_electrodes = condition_A.shape[1]
    n_timepoints = condition_A.shape[2]
    
    # t值阈值
    t_threshold = stats.t.ppf(1 - alpha_cluster/2, df=n_subjects-1)
    
    # 存储每次置换的最大cluster mass
    max_masses = []
    
    for perm in range(n_permutations):
        if perm % 100 == 0:
            print(f"置换 {perm}/{n_permutations}")
        
        # 随机打乱条件标签
        # 对每个被试，随机决定是否交换A和B
        swap_mask = np.random.rand(n_subjects) > 0.5
        
        # 创建打乱后的数据
        perm_A = condition_A.copy()
        perm_B = condition_B.copy()
        
        perm_A[swap_mask] = condition_B[swap_mask]
        perm_B[swap_mask] = condition_A[swap_mask]
        
        # 计算t统计量
        t_map_perm = np.zeros((n_electrodes, n_timepoints))
        for elec in range(n_electrodes):
            for t in range(n_timepoints):
                t_stat, _ = stats.ttest_rel(perm_A[:, elec, t], perm_B[:, elec, t])
                t_map_perm[elec, t] = t_stat
        
        # 找cluster
        significant_pos = t_map_perm > t_threshold
        labeled_perm, n_clusters_perm = label(significant_pos)
        
        # 计算每个cluster的mass
        if n_clusters_perm > 0:
            masses = []
            for cluster_id in range(1, n_clusters_perm + 1):
                cluster_mask = labeled_perm == cluster_id
                mass = np.sum(np.abs(t_map_perm[cluster_mask]))
                masses.append(mass)
            
            # 记录最大的mass
            max_masses.append(np.max(masses))
        else:
            max_masses.append(0)
    
    return np.array(max_masses)

# 执行置换检验
null_distribution = permutation_test(condition_A, condition_B, 
                                     n_permutations=1000, 
                                     alpha_cluster=0.001)
```

#### 步骤6: 确定显著性阈值

```python
# 计算第97.5百分位数（双尾检验，α=0.05）
significance_threshold = np.percentile(null_distribution, 97.5)

print(f"显著性阈值: {significance_threshold:.2f}")

# 可视化零分布
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.hist(null_distribution, bins=50, alpha=0.7, edgecolor='black')
plt.axvline(significance_threshold, color='red', linestyle='--', 
            linewidth=2, label=f'Threshold (97.5%): {significance_threshold:.2f}')
plt.xlabel('Maximum Cluster Mass')
plt.ylabel('Frequency')
plt.title('Null Distribution from Permutation Test')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('null_distribution.png', dpi=300, bbox_inches='tight')
plt.show()
```

#### 步骤7: 判断显著cluster

```python
# 判断哪些cluster是显著的
significant_clusters_pos = []
for i, (mass, info) in enumerate(zip(pos_masses, pos_info)):
    if mass > significance_threshold:
        info['p_value'] = np.mean(null_distribution >= mass)
        significant_clusters_pos.append(info)
        print(f"\n显著的正向Cluster #{info['id']}:")
        print(f"  Mass: {mass:.2f}")
        print(f"  Size: {info['size']} points")
        print(f"  Peak t-value: {info['peak_t']:.2f}")
        print(f"  p-value: {info['p_value']:.3f}")

significant_clusters_neg = []
for i, (mass, info) in enumerate(zip(neg_masses, neg_info)):
    if mass > significance_threshold:
        info['p_value'] = np.mean(null_distribution >= mass)
        significant_clusters_neg.append(info)
        print(f"\n显著的负向Cluster #{info['id']}:")
        print(f"  Mass: {mass:.2f}")
        print(f"  Size: {info['size']} points")
        print(f"  Peak t-value: {info['peak_t']:.2f}")
        print(f"  p-value: {info['p_value']:.3f}")
```

---

## 四、完整Python实现

### 示例：模拟EEG数据

```python
import numpy as np
from scipy import stats
from scipy.ndimage import label
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

# ============================================
# 1. 模拟数据
# ============================================

np.random.seed(42)

# 参数
n_subjects = 20
n_electrodes = 64
n_timepoints = 500  # -200ms to 800ms
sampling_rate = 500  # Hz
time = np.linspace(-200, 800, n_timepoints)

# 生成基础数据（噪声）
condition_A = np.random.randn(n_subjects, n_electrodes, n_timepoints) * 2
condition_B = np.random.randn(n_subjects, n_electrodes, n_timepoints) * 2

# 添加真实效应
# 假设在Pz电极（第50个电极），300-500ms有差异
Pz_electrode = 50
effect_onset = np.where(time >= 300)[0][0]
effect_offset = np.where(time <= 500)[0][-1]

# 添加效应：条件B比条件A有更强的活动
effect_amplitude = 3.0  # μV
for subj in range(n_subjects):
    effect_shape = np.exp(-((time[effect_onset:effect_offset+1] - 400)**2) / (2 * 50**2))
    condition_B[subj, Pz_electrode, effect_onset:effect_offset+1] += effect_amplitude * effect_shape

# 也影响相邻电极
for elec_offset in [-1, 1]:  # P1和P2
    if 0 <= Pz_electrode + elec_offset < n_electrodes:
        for subj in range(n_subjects):
            effect_shape = np.exp(-((time[effect_onset:effect_offset+1] - 400)**2) / (2 * 50**2))
            condition_B[subj, Pz_electrode + elec_offset, effect_onset:effect_offset+1] += effect_amplitude * 0.7 * effect_shape

print("数据模拟完成")
print(f"条件A shape: {condition_A.shape}")
print(f"条件B shape: {condition_B.shape}")

# ============================================
# 2. 计算真实数据的t统计量
# ============================================

t_map = np.zeros((n_electrodes, n_timepoints))
p_map = np.zeros((n_electrodes, n_timepoints))

for elec in range(n_electrodes):
    for t in range(n_timepoints):
        t_stat, p_val = stats.ttest_rel(condition_B[:, elec, t], 
                                        condition_A[:, elec, t])
        t_map[elec, t] = t_stat
        p_map[elec, t] = p_val

print(f"\nt统计量计算完成")
print(f"最大t值: {np.max(t_map):.2f}")
print(f"最小t值: {np.min(t_map):.2f}")

# ============================================
# 3. 找cluster
# ============================================

# 群集形成阈值
alpha_cluster = 0.001
t_threshold = stats.t.ppf(1 - alpha_cluster/2, df=n_subjects-1)
print(f"\nt阈值 (p<{alpha_cluster}): ±{t_threshold:.2f}")

# 找显著点
significant_pos = t_map > t_threshold
significant_neg = t_map < -t_threshold

# 定义连接结构（电极×时间）
# 简化：只考虑时间相邻
structure_time = np.zeros((3, 3))
structure_time[1, :] = 1  # 中间行全连接（时间相邻）

# 找cluster
labeled_pos, n_clusters_pos = label(significant_pos, structure=structure_time)
labeled_neg, n_clusters_neg = label(significant_neg, structure=structure_time)

print(f"\n找到 {n_clusters_pos} 个正向cluster")
print(f"找到 {n_clusters_neg} 个负向cluster")

# ============================================
# 4. 计算cluster mass
# ============================================

def compute_cluster_properties(labeled_map, t_map, n_clusters):
    """计算每个cluster的属性"""
    clusters = []
    
    for cluster_id in range(1, n_clusters + 1):
        cluster_mask = labeled_map == cluster_id
        
        # 基本属性
        mass = np.sum(np.abs(t_map[cluster_mask]))
        size = np.sum(cluster_mask)
        
        # 找到cluster的电极和时间范围
        electrodes, timepoints = np.where(cluster_mask)
        
        # 找峰值
        cluster_t_values = np.abs(t_map[cluster_mask])
        peak_idx = np.argmax(cluster_t_values)
        peak_electrode = electrodes[peak_idx]
        peak_timepoint = timepoints[peak_idx]
        peak_t = t_map[cluster_mask][peak_idx]
        
        clusters.append({
            'id': cluster_id,
            'mass': mass,
            'size': size,
            'electrodes': electrodes,
            'timepoints': timepoints,
            'electrode_range': (electrodes.min(), electrodes.max()),
            'time_range': (time[timepoints.min()], time[timepoints.max()]),
            'peak_electrode': peak_electrode,
            'peak_time': time[peak_timepoint],
            'peak_t': peak_t
        })
    
    return clusters

clusters_pos = compute_cluster_properties(labeled_pos, t_map, n_clusters_pos)
clusters_neg = compute_cluster_properties(labeled_neg, t_map, n_clusters_neg)

print("\n正向Cluster信息:")
for c in clusters_pos[:5]:  # 只显示前5个
    print(f"  Cluster {c['id']}: mass={c['mass']:.2f}, "
          f"size={c['size']}, "
          f"time={c['time_range'][0]:.0f}-{c['time_range'][1]:.0f}ms, "
          f"peak at electrode {c['peak_electrode']}, {c['peak_time']:.0f}ms")

# ============================================
# 5. 置换检验
# ============================================

def permutation_test_cluster(condition_A, condition_B, n_permutations=1000, 
                             alpha_cluster=0.001):
    """置换检验"""
    n_subjects = condition_A.shape[0]
    n_electrodes = condition_A.shape[1]
    n_timepoints = condition_A.shape[2]
    
    t_threshold = stats.t.ppf(1 - alpha_cluster/2, df=n_subjects-1)
    structure_time = np.zeros((3, 3))
    structure_time[1, :] = 1
    
    max_masses = []
    
    print(f"\n开始置换检验 ({n_permutations} 次)...")
    
    for perm in range(n_permutations):
        if perm % 100 == 0:
            print(f"  进度: {perm}/{n_permutations}")
        
        # 随机打乱标签
        swap_mask = np.random.rand(n_subjects) > 0.5
        
        perm_A = condition_A.copy()
        perm_B = condition_B.copy()
        perm_A[swap_mask] = condition_B[swap_mask]
        perm_B[swap_mask] = condition_A[swap_mask]
        
        # 计算t统计量
        t_map_perm = np.zeros((n_electrodes, n_timepoints))
        for elec in range(n_electrodes):
            for t in range(n_timepoints):
                t_stat, _ = stats.ttest_rel(perm_B[:, elec, t], perm_A[:, elec, t])
                t_map_perm[elec, t] = t_stat
        
        # 找cluster
        significant_perm = np.abs(t_map_perm) > t_threshold
        labeled_perm, n_clusters_perm = label(significant_perm, structure=structure_time)
        
        # 计算最大mass
        if n_clusters_perm > 0:
            masses = []
            for cluster_id in range(1, n_clusters_perm + 1):
                cluster_mask = labeled_perm == cluster_id
                mass = np.sum(np.abs(t_map_perm[cluster_mask]))
                masses.append(mass)
            max_masses.append(np.max(masses))
        else:
            max_masses.append(0)
    
    print("置换检验完成")
    return np.array(max_masses)

# 执行置换检验
null_distribution = permutation_test_cluster(condition_A, condition_B, 
                                             n_permutations=1000, 
                                             alpha_cluster=0.001)

# ============================================
# 6. 确定显著性阈值
# ============================================

significance_threshold = np.percentile(null_distribution, 97.5)
print(f"\n显著性阈值 (97.5%): {significance_threshold:.2f}")

# ============================================
# 7. 判断显著cluster
# ============================================

print("\n" + "="*60)
print("显著的正向Cluster:")
print("="*60)

significant_clusters = []
for c in clusters_pos:
    if c['mass'] > significance_threshold:
        # 计算p值
        p_value = np.mean(null_distribution >= c['mass'])
        c['p_value'] = p_value
        significant_clusters.append(c)
        
        print(f"\nCluster {c['id']}:")
        print(f"  Mass: {c['mass']:.2f}")
        print(f"  Size: {c['size']} points")
        print(f"  电极范围: {c['electrode_range'][0]}-{c['electrode_range'][1]}")
        print(f"  时间范围: {c['time_range'][0]:.0f}-{c['time_range'][1]:.0f} ms")
        print(f"  峰值: 电极{c['peak_electrode']}, {c['peak_time']:.0f}ms, t={c['peak_t']:.2f}")
        print(f"  p-value: {p_value:.3f}")

# ============================================
# 8. 可视化
# ============================================

# 图1: 零分布
fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(null_distribution, bins=50, alpha=0.7, edgecolor='black', color='steelblue')
ax.axvline(significance_threshold, color='red', linestyle='--', 
           linewidth=2, label=f'Threshold (97.5%): {significance_threshold:.2f}')

# 标记显著cluster
for c in significant_clusters:
    ax.axvline(c['mass'], color='green', linestyle='-', 
               linewidth=2, alpha=0.7, 
               label=f'Cluster {c["id"]} (p={c["p_value"]:.3f})')

ax.set_xlabel('Cluster Mass', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.set_title('Null Distribution and Significant Clusters', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('cluster_permutation_null_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# 图2: t统计量热图
fig, ax = plt.subplots(figsize=(14, 8))

# 绘制热图
im = ax.imshow(t_map, aspect='auto', cmap='RdBu_r', 
               extent=[time[0], time[-1], n_electrodes, 0],
               vmin=-5, vmax=5)

# 标记显著cluster
for c in significant_clusters:
    # 画框
    time_idx_min = np.where(time >= c['time_range'][0])[0][0]
    time_idx_max = np.where(time <= c['time_range'][1])[0][-1]
    
    rect = plt.Rectangle((c['time_range'][0], c['electrode_range'][1]),
                         c['time_range'][1] - c['time_range'][0],
                         c['electrode_range'][1] - c['electrode_range'][0] + 1,
                         fill=False, edgecolor='green', linewidth=2)
    ax.add_patch(rect)
    
    # 标注
    ax.annotate(f'Cluster {c["id"]}\np={c["p_value"]:.3f}',
               xy=(c['peak_time'], c['peak_electrode']),
               xytext=(c['peak_time'] + 50, c['peak_electrode'] - 5),
               fontsize=10, color='green',
               arrowprops=dict(arrowstyle='->', color='green'))

# 添加颜色条
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="3%", pad=0.1)
cbar = plt.colorbar(im, cax=cax)
cbar.set_label('t-value', fontsize=12)

ax.set_xlabel('Time (ms)', fontsize=12)
ax.set_ylabel('Electrode', fontsize=12)
ax.set_title('t-statistic Map with Significant Clusters', fontsize=14)
ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax.grid(True, alpha=0.3, axis='x')

plt.tight_layout()
plt.savefig('cluster_permutation_tmap.png', dpi=300, bbox_inches='tight')
plt.show()

# 图3: Pz电极的时间序列
fig, ax = plt.subplots(figsize=(12, 6))

# 平均信号
mean_A = np.mean(condition_A[:, Pz_electrode, :], axis=0)
mean_B = np.mean(condition_B[:, Pz_electrode, :], axis=0)
sem_A = stats.sem(condition_A[:, Pz_electrode, :], axis=0)
sem_B = stats.sem(condition_B[:, Pz_electrode, :], axis=0)

ax.plot(time, mean_A, 'b-', linewidth=2, label='Condition A')
ax.fill_between(time, mean_A - sem_A, mean_A + sem_A, alpha=0.3, color='blue')

ax.plot(time, mean_B, 'r-', linewidth=2, label='Condition B')
ax.fill_between(time, mean_B - sem_B, mean_B + sem_B, alpha=0.3, color='red')

# 标记显著时间窗口
for c in significant_clusters:
    if Pz_electrode >= c['electrode_range'][0] and Pz_electrode <= c['electrode_range'][1]:
        ax.axvspan(c['time_range'][0], c['time_range'][1], 
                  alpha=0.2, color='green', 
                  label=f'Significant (p={c["p_value"]:.3f})')

ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
ax.axvline(0, color='black', linestyle='--', linewidth=1, alpha=0.5)

ax.set_xlabel('Time (ms)', fontsize=12)
ax.set_ylabel('Amplitude (μV)', fontsize=12)
ax.set_title(f'ERP at Pz Electrode (Electrode {Pz_electrode})', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cluster_permutation_erp.png', dpi=300, bbox_inches='tight')
plt.show()

print("\n分析完成！结果已保存为图片。")
```

---

## 五、关键要点总结

### 1. 为什么用Cluster-based？

```
✓ 解决多重比较问题
✓ 考虑数据的时空结构
✓ 比Bonferroni更灵敏
✓ 不需要预设ROI
```

### 2. 核心假设

```
真实效应 = 连续的时空cluster
噪声 = 孤立的点

这个假设在EEG/MEG研究中通常是合理的
```

### 3. 关键参数

```python
# 群集形成阈值
alpha_cluster = 0.001  # 或 0.005
# 越严格，cluster越少但越可靠

# 置换次数
n_permutations = 1000  # 或更多
# 越多越准确，但计算时间越长

# 显著性水平
alpha_significance = 0.05  # 最终的显著性水平
```

### 4. 结果报告

```
应该报告：
1. Cluster的电极范围
2. Cluster的时间窗口
3. Cluster的mass和size
4. 峰值位置（电极、时间）
5. p值

示例：
"我们发现一个显著的正向cluster (p=0.003)，
位于中央顶叶电极 (Pz, POz, Oz)，
时间窗口为 350-520ms，
峰值在Pz电极420ms (t=4.32)。"
```

### 5. 注意事项

```
⚠️ 置换检验计算量大
   - 可以用并行计算加速
   - 可以减少置换次数（但至少500次）

⚠️ 需要足够的被试数
   - 至少10-15个被试
   - 被试太少，统计效力不足

⚠️ Cluster定义要合理
   - 时间相邻：通常连续
   - 空间相邻：根据电极距离定义

⚠️ 结果解释要谨慎
   - Cluster不等于精确的效应位置
   - 只能说"在这个时空范围内有显著效应"
```

---

## 六、与Mass-Univariate的关系

```
Mass-Univariate:
  ↓ 对每个电极-时间点做回归
  ↓ 得到64,000个统计量
  
Cluster-based Permutation Test:
  ↓ 找到连续的显著区域
  ↓ 通过置换检验判断显著性
  
两者结合 = 完整的分析流程
```

---

## 七、实际应用建议

### 1. 数据准备

```python
# 确保数据质量
# - 预处理充分
# - 伪迹剔除干净
# - 试次数足够（每个条件至少30试次）
```

### 2. 参数选择

```python
# 推荐参数
alpha_cluster = 0.001  # 群集形成阈值
n_permutations = 1000  # 置换次数
alpha_final = 0.05     # 最终显著性水平
```

### 3. 结果验证

```python
# 1. 检查cluster是否合理
#    - 时间窗口是否在预期范围内
#    - 电极分布是否符合解剖学

# 2. 检查效应量
#    - 不仅看显著性，还要看效应大小

# 3. 可视化检查
#    - 画出ERP波形
#    - 画出拓扑图
```

---

## 八、扩展阅读

### 相关方法

1. **TFCE (Threshold-Free Cluster Enhancement)**
   - 不需要设定cluster阈值
   - 更灵敏，但计算量更大

2. **FDR (False Discovery Rate)**
   - 不考虑时空结构
   - 更保守

3. **NBS (Network-Based Statistic)**
   - 用于连接性分析
   - 类似的思想

### 参考文献

```
Maris, E., & Oostenveld, R. (2007). 
Nonparametric statistical testing of EEG- and MEG-data. 
Journal of Neuroscience Methods, 164(1), 177-190.

这是Cluster-based Permutation Test的经典文献
```

---

## 总结

**Cluster-based Permutation Test = 聪明的多重比较校正**

- 利用真实效应的时空连续性
- 通过置换检验构建零分布
- 既控制假阳性，又保持灵敏度
- 是EEG/MEG研究的标准方法
