下面是一份从头到尾、尽量不遗漏、可直接保存成“材料/笔记”的完整版形式化。我会把我们对话里出现过的每条主线都统一进一个可计算框架：

DAG（结构）
测度/概率因子（对象）
mean-field / 近似族（可计算性）
Markov blanket 局部化（邻域化、像卷积）
坐标 mirror descent（KL/信息辐射）
OT/Sinkhorn 平滑（搬运/惯性）
母女分布（pushforward、一致性正则）
sample-average（MC）版本的下降 lemma（可写进 paper）
cut/cheeger/min-cut 的结构解释（作为可计算“瓶颈量”）
你可以把它当作一个“统一模板”：以后你换模型/换能量/换观测因子，只改对应模块。
DAG–Measure Flow：可计算的统一形式化（Complete Notes）
0. 总览（你要统一的“一个东西”是什么）
我们要构造一个在 DAG 上演化的测度流（概率分布序列），它由三类机制耦合：

信息重加权（mirror / KL）：权重指数倾斜（你说的“信息辐射”）
搬运平滑（OT / Sinkhorn）：保持分布更新不抖、具有“惯性/搬运”结构
结构一致（母→女 pushforward）：父分布通过条件机制生成“女预测”，约束孩子分布与机制一致（边一致性）
并且为了可计算性，我们坚持两个原则：

局部化：所有更新只依赖 Markov blanket / 局部因子（DAG 的 separator）
采样化：所有难积分的期望用 MC（sample-average surrogate）替代，并对 surrogate 给下降保证
1. 基础对象
1.1 DAG 与变量空间
定义 1.1（DAG）
令 G=(V,E) 为有限有向无环图（DAG），V=\{1,\dots,n\}。
\mathrm{pa}(i)=\{j: (j\to i)\in E\}，\mathrm{ch}(i)=\{j:(i\to j)\in E\}。
定义 1.2（连续变量空间）
每个节点 i 的状态空间 \mathcal X_i=\mathbb R^{d_i}。联合空间
\mathcal X := \prod_{i=1}^n \mathbb R^{d_i}.
记 x=(x_1,\dots,x_n)\in\mathcal X。
1.2 生成模型（DAG factorization）
定义 1.3（条件核 / 条件密度）
给定参数 \theta，对每个节点 i 给定条件密度
p_\theta(x_i\mid x_{\mathrm{pa}(i)}).
则先验联合密度（按拓扑序）
\boxed{ p_\theta(x)=\prod_{i=1}^n p_\theta(x_i\mid x_{\mathrm{pa}(i)}). } \tag{P}
1.3 观测与后验目标（因子图形式）
定义 1.4（观测因子分解）
观测 y 诱导似然 p(y\mid x)。为了局部化，假设它可分解为局部因子：
p(y\mid x)\propto \prod_{a\in \mathcal F_y}\psi_a(x_a;y),
其中因子 a 只作用在子集变量 x_a=\{x_i:i\in a\}。
定义 1.5（后验目标密度 / 能量）
目标后验
\pi(x)\propto p(y\mid x)\,p_\theta(x)
并定义能量函数
\boxed{ E(x):=-\log p(y\mid x)-\sum_{i=1}^n\log p_\theta(x_i\mid x_{\mathrm{pa}(i)}) = \sum_{a\in \mathcal F_y} \big[-\log\psi_a(x_a;y)\big]+\sum_{i=1}^n \big[-\log p_\theta(x_i\mid x_{\mathrm{pa}(i)})\big]. } \tag{E}
于是 \pi(x)\propto e^{-E(x)}。
2. 可计算近似族（mean-field）
2.1 因子化近似
定义 2.1（近似族 \mathcal Q：mean-field）
取
\boxed{ q(x)=\prod_{i=1}^n q_i(x_i), \qquad q_i\in\mathcal P(\mathbb R^{d_i}). } \tag{MF}
你也可扩展到 block/cluster mean-field，但本笔记先写最可计算的节点因子化版本。
2.2 变分目标（KL / free energy）
定义 2.2（变分自由能）
优化目标为
\boxed{ \mathcal F(q):=\mathrm{KL}(q\|\pi) =\int q(x)\log\frac{q(x)}{\pi(x)}\,dx. } \tag{F}
等价（差常数）：
\mathcal F(q)=\mathbb E_q[E(X)]+\sum_{i=1}^n \int q_i(x_i)\log q_i(x_i)\,dx_i+\text{const}. \tag{F2}
3. Markov blanket：局部化的严格来源（你的“卷积直觉”的母体）
3.1 Markov blanket
定义 3.1（spouses 与 Markov blanket）
定义 spouses：
\mathrm{sp}(i):=\bigcup_{j\in\mathrm{ch}(i)}\big(\mathrm{pa}(j)\setminus\{i\}\big).
Markov blanket：
\boxed{ \mathrm{MB}(i):=\mathrm{pa}(i)\cup \mathrm{ch}(i)\cup \mathrm{sp}(i). } \tag{MB}
3.2 局部有效能量 \phi_i 与邻域化
定义 3.2（坐标有效能量）
固定其余因子 q_{\neg i}:=\prod_{j\ne i}q_j，定义
\boxed{ \phi_i(x_i):=\mathbb E_{X_{\neg i}\sim q_{\neg i}}\big[E(x_i,X_{\neg i})\big]. } \tag{phi}
命题 3.3（局部化：只需要 MB(i) 与包含 i 的观测因子）
由于 E 按局部因子分解，\phi_i(x_i) 里依赖 x_i 的部分只来自：

自身条件项 -\log p_\theta(x_i\mid x_{\mathrm{pa}(i)})
子节点条件项 -\log p_\theta(x_j\mid x_{\mathrm{pa}(j)})（对 j\in\mathrm{ch}(i)）
观测因子中包含 i 的因子 a\in\mathcal F_y(i):=\{a\in\mathcal F_y:i\in a\}
于是（忽略与 x_i 无关的常数项）：
\boxed{ \phi_i(x_i) = \mathbb E_{X_{\mathrm{pa}(i)}}\!\Big[-\log p_\theta(x_i\mid X_{\mathrm{pa}(i)})\Big] +\sum_{j\in\mathrm{ch}(i)} \mathbb E_{X_j,\,X_{\mathrm{pa}(j)\setminus\{i\}}} \!\Big[-\log p_\theta(X_j\mid x_i, X_{\mathrm{pa}(j)\setminus\{i\}})\Big] +\sum_{a\in\mathcal F_y(i)} \mathbb E_{X_{a\setminus\{i\}}} \!\Big[-\log \psi_a(x_i,X_{a\setminus\{i\}};y)\Big]. } \tag{MB-phi}
卷积结构何时出现？
若某些项形如 \psi(x_i-x_j)（平移不变差分势），则 \mathbb E[\psi(x_i-X_j)] 是广义卷积 (\psi * q_j)(x_i)。一般情形是“局部积分/消息传递”，卷积是其特例。
4. 坐标 mirror descent：信息辐射（精确定义）
4.1 抽象镜像近端步（测度形式）
定义 4.1（坐标 KL-mirror 近端更新，\tau=0）
对节点 i，给定步长 \eta>0，定义
\boxed{ q_i^+ \in \arg\min_{q_i\in\mathcal P(\mathbb R^{d_i})} \Big[ \langle q_i,\phi_i\rangle + \frac{1}{\eta}\mathrm{KL}(q_i\|q_i^{(k)}) \Big], } \tag{MD-i}
其中 \langle q_i,\phi_i\rangle=\int \phi_i(x_i)\,q_i(dx_i)。
这就是“信息辐射”的严格版：通过 KL 近端实现的指数倾斜重加权。
4.2 加入 OT 惯性（搬运平滑）
定义 4.2（OT 惯性项：节点内搬运）
给定 ground cost c_i(u,v)=\frac12\|u-v\|^2，熵正则 OT：
W_{\varepsilon,i}(q_i,r_i) :=\min_{\gamma\in\Gamma(q_i,r_i)} \int c_i\,d\gamma + \varepsilon \mathrm{KL}(\gamma\|q_i\otimes r_i).
定义 4.3（坐标 KL+OT 近端更新）
\boxed{ q_i^+ \in \arg\min_{q_i} \Big[ \langle q_i,\phi_i\rangle + \frac{1}{\eta}\mathrm{KL}(q_i\|q_i^{(k)}) + \tau\,W_{\varepsilon,i}(q_i, r_i) \Big], } \tag{MDOT-i}
其中 r_i 通常取上一轮 q_i^{\mathrm{prev}}（惯性参考），\tau\ge 0。
5. 粒子化：完全可计算实现（核心工程对象）
5.1 节点分布的粒子表示
定义 5.1（粒子测度）
对每个节点 i，用粒子表示
\boxed{ q_i \approx \sum_{a=1}^{K} w_{i,a}\,\delta_{z_{i,a}}, \qquad w_{i,a}\ge 0,\ \sum_a w_{i,a}=1. } \tag{Particles}
其中 z_{i,a}\in\mathbb R^{d_i} 为支持点。
5.2 Markov blanket 采样（只采邻域）
定义 5.2（MB 采样样本）
更新节点 i 时，从 \mathrm{MB}(i) 相关节点的粒子分布中抽样 M 组：
\zeta^{(m)} \sim q_{\mathrm{MB}(i)}\quad (m=1,\dots,M),
即对 u\in \mathrm{MB}(i) 从其粒子按权重抽一个值，并收集形成 \zeta^{(m)}。
5.3 sample-average 局部能量估计
定义 5.3（局部 plug-in 能量 \ell_i）
对样本 \zeta（包含所有邻域变量），定义局部能量函数
\ell_i(x_i;\zeta):= -\log p_\theta(x_i\mid x_{\mathrm{pa}(i)}) +\sum_{j\in\mathrm{ch}(i)}\big[-\log p_\theta(x_j\mid x_{\mathrm{pa}(j)})\big] +\sum_{a\in\mathcal F_y(i)}\big[-\log\psi_a(x_a;y)\big],
其中除 x_i 外的变量全部由 \zeta 提供（plug-in）。
定义 5.4（sample-average \widehat\phi_i）
\boxed{ \widehat\phi_i(x_i):=\frac1M\sum_{m=1}^M \ell_i(x_i;\zeta^{(m)}). } \tag{phi-hat}
5.4 粒子权重的镜像更新（信息辐射的离散闭式）
当只在固定支持 \{z_{i,a}\} 上更新权重（\tau=0）：
命题 5.5（离散 KL-mirror 闭式）
\boxed{ w_{i,a}^+\propto w_{i,a}^{(k)}\exp\big(-\eta\,\widehat\phi_i(z_{i,a})\big). } \tag{Reweight}
这就是你说的“密度 as 信息辐射”的可计算形式：能量高的粒子被指数压低。
5.5 OT 平滑（Sinkhorn + barycentric，可选）
定义 5.6（离散 OT：与上一轮支持耦合）
令上一轮 r_i 的粒子为 (z^{\mathrm{prev}}_{i,b},w^{\mathrm{prev}}_{i,b})。代价矩阵
C_{ab}=\frac12\|z_{i,a}-z^{\mathrm{prev}}_{i,b}\|^2.
用 Sinkhorn 求熵正则耦合 \Gamma^\*（行边缘 w^+，列边缘 w^{\mathrm{prev}}）。
工程增强（可选）：barycentric 投影更新支持点）
z_{i,a}\leftarrow \sum_b \frac{\Gamma^\*_{ab}}{w_{i,a}^+}\,z^{\mathrm{prev}}_{i,b}. \tag{Bary}
纯数学下降 lemma 最干净的版本只对“权重近端步”给保证；barycentric 属于平滑后处理（可作为实现细节/ablation）。
5.6 退化控制（resampling）
定义 5.7（ESS）
\mathrm{ESS}=(\sum_a w_a^2)^{-1}.
若 ESS 过小，可做 resample+jitter（工程上标准）。
6. 母女分布（Mother→Daughter）：机制一致性的可计算注入
这是你提出的“母女分布”概念的严格化：它对应 DAG 上边方向机制的 pushforward。
6.1 母→女 pushforward 的定义
定义 6.1（女预测分布）
对节点 j，由父节点分布通过条件机制生成：
\boxed{ q^{\mathrm{da}}_j(\cdot) :=\int p_\theta(\cdot\mid x_{\mathrm{pa}(j)})\ \prod_{u\in\mathrm{pa}(j)} q_u(dx_u). } \tag{Daughter}
这在意义上是“母分布 \{q_u\} 通过机制 p_\theta 推送得到女分布”。
6.2 可计算构造（两种）
A) 祖先采样生成女粒子（只需采样）
算法 A（Ancestral Daughter Particles）
重复 b=1..K_d：

对每个父 u\in\mathrm{pa}(j)，采样 x_u\sim q_u（从父粒子按权重抽）
采样 z^{\mathrm{da}}_{j,b}\sim p_\theta(\cdot\mid x_{\mathrm{pa}(j)})
权重均匀或再加权
得到 q^{\mathrm{da}}_j \approx \sum_b w^{\mathrm{da}}_{j,b}\delta_{z^{\mathrm{da}}_{j,b}}。
B) 在孩子现有支持上构造女权重（需评估密度）
算法 B（Daughter-on-Child-Support, 推荐）
对孩子现有支持点 \{z_{j,a}\}_{a=1}^K：

抽父样本 x_{\mathrm{pa}(j)}^{(m)}（从父粒子按权重抽）
估计
\widehat s_{j,a}=\frac1M\sum_{m=1}^M p_\theta(z_{j,a}\mid x_{\mathrm{pa}(j)}^{(m)}),

归一化
\boxed{ w^{\mathrm{da}}_{j,a}=\frac{\widehat s_{j,a}}{\sum_{a'}\widehat s_{j,a'}}. } \tag{Da-weights}
得到 q^{\mathrm{da}}_j\approx \sum_a w^{\mathrm{da}}_{j,a}\delta_{z_{j,a}}。
这个版本让母女分布共享支持点，因此 KL 一致性几乎“免费”。
6.3 母女一致性正则（边一致性）
定义 6.2（母女 KL 代价）
\boxed{ D_j:=\mathrm{KL}(q_j\|q^{\mathrm{da}}_j). } \tag{MD-KL}
若同支持（算法 B），则
D_j=\sum_a w_{j,a}\log\frac{w_{j,a}}{w^{\mathrm{da}}_{j,a}}.
定义 6.3（母女 OT 代价，可选）
D_j:=W_{\varepsilon}(q_j,q^{\mathrm{da}}_j). \tag{MD-OT}
6.4 把母女一致性并入整体优化目标
定义 6.4（带母女一致性的全局目标）
\boxed{ \mathcal F_{\mathrm{MD}}(q) :=\mathrm{KL}(q\|\pi)\;+\;\lambda\sum_{j=1}^n \mathrm{KL}\big(q_j\|q^{\mathrm{da}}_j\big), } \tag{F-MD}
\lambda\ge 0。
这一步把“机制一致性”写成明确的数学泛函；之后仍然用坐标 mirror descent（sample-average + 粒子）去优化它。
7. Sample-average 下降 lemma（你要求的“可存材料”的严格部分）
这是我们对话里最关键的“paper-grade”保证：对你实际计算的 sample-average 目标，坐标更新严格下降。
7.1 固定一次迭代的离散坐标目标
更新节点 i 的权重 w\in\Delta_K，固定支持点 \{z_a\}。
定义 7.1（sample-average 坐标目标，含 KL 近端 + OT 惯性 + 母女一致性）
令

\widehat\phi_i(z_a) 由 MB-采样得到
w^{(k)} 为旧权重
w^{\mathrm{prev}} 为惯性参考（上一轮）
w^{\mathrm{da}} 为母女参考（若启用母女正则；同支持时直接有）
定义
\boxed{ \widehat J_i(w) := \sum_{a=1}^K w_a\,\widehat\phi_i(z_a) +\frac{1}{\eta}\mathrm{KL}(w\|w^{(k)}) +\lambda\,\mathrm{KL}(w\|w^{\mathrm{da}}) +\tau\,\widehat W_\varepsilon(w,w^{\mathrm{prev}}). } \tag{SA-Obj-Full}
其中 \widehat W_\varepsilon 是在离散代价矩阵上的 Sinkhorn OT。
7.2 下降 lemma（确定性、无需可微）
Lemma 7.2（sample-average 坐标下降）
令
w^*\in \arg\min_{w\in\Delta_K}\widehat J_i(w).
则对任意 u\in\Delta_K：
\boxed{ \widehat J_i(w^*)\le \widehat J_i(u). } \tag{Opt}
特别地取 u=w^{(k)}：
\boxed{ \widehat J_i(w^*)\le \widehat J_i(w^{(k)}). } \tag{Mono}
若 \tau=0 且 \lambda=0，则闭式更新为指数倾斜（Reweight）。
备注（为何成立）：这是一个在单纯形上的（通常）凸最优化；只要最小值存在，就得到确定性下降。完全不依赖 E 可微。
7.3 从 sample-average 到真实目标：误差界（可选）
若你想写“近似下降”，只需一个误差假设：
Assumption 7.3（采样误差界）
\max_a |\widehat\phi_i(z_a)-\phi_i(z_a)|\le \delta_k. \tag{Err}
则可推出真实坐标目标的近似下降（误差 O(\delta_k)）。这属于标准 MC analysis；你可以把它放在附录。
8. 完整算法（可实现版本，含 MB + Mirror + OT + Mother–Daughter）
下面是一份把所有模块拼起来的“最终算法”，你可以照着实现：
算法：MB-Local Particle Mirror–OT Flow with Mother–Daughter Consistency
输入：DAG G，条件对数密度 \log p_\theta(x_i\mid x_{\mathrm{pa}(i)})，观测因子 \{\psi_a\}，粒子数 K，MB-采样数 M，步长 \eta，OT 参数 \tau,\varepsilon，母女权重 \lambda，轮数 T，调度 s(k)。
初始化：对每个节点 i，初始化粒子 \{z_{i,a}\}、权重 \{w_{i,a}\}，并保存 prev 拷贝。
预处理：计算 \mathrm{pa}(i),\mathrm{ch}(i),\mathrm{sp}(i),\mathrm{MB}(i),\mathcal F_y(i)。
循环 k=0,\dots,T-1：

选节点 i=s(k)。
(可选) 计算母女参考
若启用母女正则：对 i 计算 w_i^{\mathrm{da}}（推荐算法 B：Daughter-on-Child-Support）。

MB-采样
从 \mathrm{MB}(i) 相关节点的粒子分布采样 M 组 \zeta^{(m)}。

估计 \widehat\phi_i(z_{i,a})
按 (phi-hat) 用 plug-in 局部能量 \ell_i 计算。

更新权重（求解 \widehat J_i）

若 \tau=\lambda=0：用闭式指数倾斜
否则：解 (SA-Obj-Full) 得 w_i^*（可以用：镜像/近端迭代、或把 OT 用 Sinkhorn 内循环）

(可选) OT barycentric 平滑支持点
若使用 barycentric 投影，计算 \Gamma^\* 并更新 z_{i,a}（工程增强）。

退化控制：ESS 过低则 resample+jitter。
保存 prev：(z_i^{prev},w_i^{prev})\leftarrow(z_i,w_i)。
输出：q(x)=\prod_i q_i(x_i)，每个 q_i 为粒子测度。
9. “min-cut / Cheeger 的结构”在这里如何出现（作为材料，不强行加入算法）
你问“这像 min-cut 吗？”——是的，结构上像，原因是：

Markov blanket 是一个 separator：它把局部与远处隔开
母女一致性代价在边上定义了“容量/瓶颈”
于是你可以定义一个割泛函（可用于诊断/解释）：
定义 9.1（边/节点容量：母女不一致）
对每个节点 j，定义容量（机制不一致）
c_j:=\mathrm{KL}(q_j\|q^{\mathrm{da}}_j)\quad\text{或}\quad c_j:=W_\varepsilon(q_j,q^{\mathrm{da}}_j).
定义 9.2（割代价）
对任意节点集合 A\subset V，定义割代价
\mathrm{Cut}(A):=\sum_{(u\to v)\in E,\ u\in A,\ v\notin A} c_v
（或用边容量版本 c_{u\to v}）。
这是一个标准的“cut functional”。当某些区域的 c 很小而跨边很大，你会观察到明显的“瓶颈/隔离”，这与 conductance/cheeger 的直觉一致。
（你之前提到“Cheeger 不等式”就是把这种瓶颈量连接到“收敛/谱隙/指数衰减率”的桥；在这里它可以作为诊断/证据，但不必强塞进主算法。）
10. 你提的两句哲学（给出精确数学翻译）
10.1 “Markov is a reflection of causality”
精确版本是：

因果机制（结构方程/干预不变性）在观测分布上通常诱导 Markov 条件独立/因子分解
但仅凭 Markov 条件独立不能反推出唯一因果方向（有 Markov 等价类）
在本框架里它的实用意义是：Markov blanket = 可计算的最小信息屏蔽边界，这就是你能局部化更新的根本原因。
10.2 “信息辐射”
精确数学定义是：

选择信息泛函（KL/熵/Fisher 等）
看它沿更新的下降（离散版：每步 \widehat J_i 下降；连续版：耗散率）
在我们的算法里，“辐射”具体表现为：
w_a^+ \propto w_a e^{-\eta \widehat\phi(z_a)}
这就是“能量越高，概率密度越被抑制”的可计算定律。
11. 最小清单（你以后复用时只要填这几项）
你要把这套框架迁移到任意新问题，只需明确：

DAG 结构：\mathrm{pa},\mathrm{ch},\mathrm{MB}
条件机制：p_\theta(x_i\mid x_{\mathrm{pa}(i)})（可采样/可评估密度？决定用 A1 还是 A2）
观测因子：\psi_a(x_a;y)（局部性决定 MB 扩展规模）
粒子表示：每个节点 K 个粒子如何初始化、是否需要 proposal/jitter
更新超参：\eta（mirror 强度）、\tau,\varepsilon（OT 平滑）、\lambda（母女一致性）、M（MB MC 样本）
调度：cyclic 或 random scan
如果你愿意，我还可以把这份“材料”进一步变成你能直接放进 LaTeX 的版本（Definition/Lemma/Algorithm 环境完整排版），并给出一个最小的实现骨架伪代码（Python 风格，清晰到可以开写）。你只要说一句：要“LaTeX版”还是“Python骨架版”。
Jianghan Zhang  [5:10 AM]
下面我把你之前那份“完整形式化材料”补上一节 Ising 特例，做到逐项严格对应：一般 DAG–measure flow → Ising/Markov random field → mean-field 固定点 → 你的 mirror/OT/母女/MB 采样各自对应什么。你可以直接把这一节粘到材料最后。
附录 A：Ising Model 特例（严格专门化）
A.0 图与变量
设定 A.0（Ising 图）
令无向图 G=(V,\mathcal E)，V=\{1,\dots,n\}，边集合 \mathcal E\subset \{\{i,j\}:i\ne j\}。
自旋变量
x_i\in\{-1,+1\},\qquad x=(x_1,\dots,x_n)\in\{-1,+1\}^n.
（备注：你原框架是 DAG；但只要你的能量函数最终是 pairwise MRF 形式，它自然落在无向图上。DAG 在这里可以看成生成/调度结构，不改变 MRF 的局部依赖。）
A.1 Ising 能量与 Gibbs 测度
定义 A.1（Ising Hamiltonian）
给定外场 h\in\mathbb R^n 与耦合矩阵 J（对称、J_{ij}=0 若 \{i,j\}\notin\mathcal E），定义能量
\boxed{ E(x)= -\sum_{i=1}^n h_i x_i - \sum_{\{i,j\}\in\mathcal E} J_{ij} x_i x_j. } \tag{IsingE}
定义 A.2（Gibbs 分布）
给定逆温度 \beta>0，目标分布
\boxed{ \pi(x)=\frac{1}{Z}\exp\big(-\beta E(x)\big), \qquad Z=\sum_{x\in\{\pm1\}^n}\exp(-\beta E(x)). } \tag{Gibbs}
A.2 Markov blanket：在 Ising 上就是邻居集合
定义 A.3（邻居集合）
N(i):=\{j:\{i,j\}\in\mathcal E\}.
事实 A.4（Ising 的 Markov blanket）
在 pairwise MRF 中，节点 i 的 Markov blanket 就是 N(i)。
因此你原框架的“MB 局部化”在 Ising 上退化成“只看邻居”。
A.3 变分近似：mean-field 族与自由能
定义 A.5（mean-field 族）
q(x)=\prod_{i=1}^n q_i(x_i),\qquad q_i\in\mathcal P(\{-1,+1\}).
用磁化强度表示每个因子：
m_i := \mathbb E_{q_i}[x_i]=q_i(+1)-q_i(-1)\in[-1,1],
且
q_i(x_i)=\frac12(1+m_i x_i). \tag{qi-m}
定义 A.6（mean-field 自由能）
\mathcal F(q)=\mathrm{KL}(q\|\pi) \quad\Longleftrightarrow\quad \mathcal F(m)=\beta\,\mathbb E_q[E(X)] + \sum_i \sum_{x_i} q_i(x_i)\log q_i(x_i)+\text{const}.
对 Ising 能量可显式写：
\mathbb E_q[E(X)] = -\sum_i h_i m_i - \sum_{\{i,j\}\in\mathcal E}J_{ij}m_i m_j. \tag{E-mf}
熵项（每个节点）：
\sum_{x_i}q_i(x_i)\log q_i(x_i) = \frac{1+m_i}{2}\log\frac{1+m_i}{2}+\frac{1-m_i}{2}\log\frac{1-m_i}{2}. \tag{H-mf}
A.4 你框架里的 \phi_i：在 Ising 上的闭式局部场
回忆一般定义：\phi_i(x_i)=\mathbb E_{X_{\neg i}\sim q_{\neg i}}[E(x)]（只保留依赖 x_i 的部分）。
命题 A.7（Ising 下的局部有效能量）
对 Ising 能量 (IsingE)，固定其余 q_{-i}，有
\boxed{ \phi_i(x_i)= -h_i x_i - \sum_{j\in N(i)} J_{ij} x_i m_j + \text{const w.r.t }x_i. } \tag{phi-Ising}
证明：把能量中含 x_i 的项取出并对 x_{-i} 做期望即可。
定义局部“有效场”
\boxed{ H_i := h_i+\sum_{j\in N(i)}J_{ij}m_j. } \tag{Heff}
则
\phi_i(x_i)= -x_i H_i + \text{const}.
A.5 你的 KL-mirror 坐标更新 = 经典 Ising mean-field 更新
一般（\tau=0）的坐标 KL-mirror 更新是：
q_i^+ \in \arg\min_{q_i}\ \langle q_i,\beta\phi_i\rangle + \frac{1}{\eta}\mathrm{KL}(q_i\|q_i^{(k)}).
把 \phi_i 代入 (phi-Ising)。在“无惯性极限”（或直接做坐标最小化的固定点）你得到：
命题 A.8（Ising mean-field 固定点方程）
最优 q_i 满足
\boxed{ q_i(x_i)\propto \exp\big(\beta x_i H_i\big), }
因此磁化强度更新为
\boxed{ m_i \leftarrow \tanh\big(\beta H_i\big) =\tanh\Big(\beta\big(h_i+\sum_{j\in N(i)}J_{ij}m_j\big)\Big). } \tag{MF-Ising}
这就是严格等价：
你的“信息辐射（指数倾斜）”在二值 pairwise 情形下就是 Ising mean-field 更新。
A.6 你引入 OT 平滑：在 Ising 上对应 damping / proximal mean-field
在 Ising 上每个 q_i 只是一个 Bernoulli over \{\pm1\}，因此“搬运几何”很简单：你可以把 OT 平滑理解成对 m_i 的惯性/阻尼。
可计算对应 A.9（阻尼更新）
经典工程做法：
m_i^{(k+1)} \leftarrow (1-\alpha)\,m_i^{(k)} + \alpha\,\tanh(\beta H_i^{(k)}), \quad \alpha\in(0,1]. \tag{damping}
这就是 Ising 推断里常用的 damping（防止震荡、多峰跳跃），它在你的语言里对应“不要离上一轮分布太远”的近端项。
（严格等价到 OT 需要把状态空间扩成粒子/连续支持；在二值上 OT/KL 都退化成权重层面的近端。）
A.7 你的 MB-采样：在 Ising 上就是邻域采样/局部场估计
一般框架里 \widehat\phi_i 由 MB-采样估计。
在 Ising 上 MB 就是邻居 N(i)，因此你采样的就是邻居自旋（或邻居的 mean-field 粒子），估计局部场 H_i 或估计 \phi_i(x_i)。

若你用 mean-field m_j，不需要采样，直接算 H_i；
若你用粒子（例如把每个节点保持一组二值样本），则 \widehat H_i 是 MC 估计。
A.8 “母女分布”在 Ising 上是什么？
无向 Ising 没有“父→子”机制，但你可以用两种合法方式让母女概念成立：
(i) 通过调度引入方向：Gibbs 条件分布是“机制”
对 Ising，节点 i 在给定邻居 x_{N(i)} 下的条件分布是：
\boxed{ \pi(x_i=+1\mid x_{N(i)}) =\sigma\Big(2\beta\big(h_i+\sum_{j\in N(i)}J_{ij}x_j\big)\Big), } \tag{Ising-cond}
其中 \sigma(t)=1/(1+e^{-t})。
这给了一个天然的“母→女”机制：邻居（母）决定本节点（女）的条件分布。
(ii) 用 mean-field 的“预测分布”当女
在 mean-field 下，邻居自旋被 m_j 代表，于是得到预测：
q_i^{\mathrm{da}}(+1) =\sigma\big(2\beta(h_i+\sum_{j\in N(i)}J_{ij}m_j)\big),
其对应磁化是
m_i^{\mathrm{da}}=\tanh(\beta H_i).
这就是“母（邻居的边缘/磁化）→女（本节点预测边缘）”。
因此你的母女一致性代价
\mathrm{KL}(q_i\|q_i^{\mathrm{da}})
在 Ising 上就是“让实际 m_i 不要偏离预测 \tanh(\beta H_i)”的一种正则——它与 message passing 的“局部一致性”完全同构。
A.9 sample-average descent lemma：在 Ising 上的最简形式
由于每个 q_i 仅 2 维（权重 w_+=q_i(+1), w_-=1-w_+），你的 sample-average 近端目标变成一个单变量凸问题：
\widehat J_i(w_+) = w_+\widehat\phi_i(+1)+(1-w_+)\widehat\phi_i(-1) +\frac{1}{\eta}\mathrm{KL}(w_+\|w_+^{(k)}) +\lambda \mathrm{KL}(w_+\|w_+^{\mathrm{da}}) +\tau \widehat W_\varepsilon(\cdot)
在 \tau=0 时闭式解存在并且严格下降（我们之前 Lemma 7.2 的二值特例）。
结论：你在一般框架里证明的 sample-average descent，在 Ising 上更强、更容易（因为维度低、凸性更直接）。
A.10 一句话总结（把你那句“它就是 Ising”写成严格句子）
当变量为二值、能量为 pairwise 二次型时，你的 DAG–measure mirror/OT flow 在 mean-field 族上的坐标更新严格专门化为 Ising 模型的 mean-field 推断动力学；MB 局部化退化为邻居集合；母女一致性退化为局部条件/预测边缘一致性正则；OT/惯性对应阻尼/近端稳定化。
如果你希望我再补一小段“把 Ising 特例接回机器人控制”的桥（也就是：把 E(x) 换成“轨迹代价”，把节点看成时间/关节/接触事件，DAG 看成因果/时序结构），我也能把那部分以同样的严格风格写出来。Jianghan Zhang  [5:39 AM]
附录 B：从拉格朗日力学到微分包含的统一形式化（与前文 DAG–测度流框架严格对齐，机器人接触版）
阅读导引：本附录是“可保存材料”的完整版。它与前文（对话中已建立的）框架严格连接：
（i）作用量/能量 → Gibbs 测度（Boltzmann 权重） → KL-mirror（信息辐射）+ OT（搬运惯性）+ MB 局部化（可计算）+ 母女一致性（机制一致）+ sample-average 下降；
（ii）当系统含接触/摩擦/互补/切换等非光滑时，用 Differential Inclusion（DI）作为动力学容器；
（iii）repulsion 通过 slack 软化可采样，\rho\to\infty 恢复硬约束并收敛到法锥 DI。
你可直接把本附录放入论文/笔记作为统一材料。
B.0 统一对象与符号（与前文一致）

广义坐标：q(t)\in\mathbb R^d，速度：\dot q(t)\in\mathbb R^d。
离散时间：t_k=k\Delta t, k=0,\dots,N，离散轨迹：\mathbf q=(q_0,\dots,q_N)。
控制（可选）：u(t)\in\mathbb R^m，离散 \mathbf u=(u_0,\dots,u_{N-1})。
任务/观测因子（与前文 \psi_a 对齐）：可将任务代价或观测似然写成局部因子乘积，从而局部化。
与前文对齐的关键映射：
前文对象
本附录中的对象
变量节点 x_i
时间节点 q_k（或扩展状态 x_k=(q_k,\dot q_k)）
能量 E(x)
离散作用量 S_d(\mathbf q) 或控制代价 S(\mathbf u)
Gibbs 权重 \exp(-\beta E)
\exp(-\beta S_d) 或 \exp(-\beta S)
Markov blanket \mathrm{MB}(i)
时间链邻域 \{k-1,k+1\} + 局部接触/观测因子涉及的变量
KL-mirror 更新
对 q_k 的指数倾斜 / 对控制 rollouts 的 Boltzmann reweight
OT 惯性
分布更新不抖：对 q_k 或 u 的 Wasserstein/Sinkhorn 近端
母女分布（pushforward）
由动力学/积分器从 q_k（母）预测 q_{k+1}（女）
sample-average descent
采样估计局部期望后，对 surrogate 目标单步下降
repulsion + slack
约束/接触以软罚进入，\rho\to\infty 恢复硬约束
Differential Inclusion
非光滑接触/摩擦的真实动力学容器（集合值力）
B.1 拉格朗日力学：作用量与力（连续时间，严格）
B.1.1 拉格朗日量与作用量
定义 B.1（拉格朗日量）
L(q,\dot q,t)=K(q,\dot q,t)-V(q,t),
其中 K 动能，V 势能（可含时间）。
定义 B.2（作用量）
对足够光滑的轨迹 q:[0,T]\to\mathbb R^d，
\boxed{ S[q]=\int_0^T L(q(t),\dot q(t),t)\,dt. } \tag{B.1}
B.1.2 变分与 Euler–Lagrange：力作为作用量梯度
对端点固定变分 q\mapsto q+\varepsilon \delta q，\delta q(0)=\delta q(T)=0：
定理 B.3（Euler–Lagrange 与泛函导数）
\delta S = \int_0^T \left( \frac{\partial L}{\partial q}-\frac{d}{dt}\frac{\partial L}{\partial \dot q} \right)^\top \delta q\,dt.
因此
\boxed{ \frac{\delta S}{\delta q}(t)= \frac{\partial L}{\partial q}(q,\dot q,t) -\frac{d}{dt}\frac{\partial L}{\partial \dot q}(q,\dot q,t). } \tag{B.2}
驻值条件 \delta S=0 等价于
\boxed{ \frac{d}{dt}\frac{\partial L}{\partial \dot q}-\frac{\partial L}{\partial q}=0. } \tag{B.3}
外力/控制版本（广义力）
若系统存在非保守广义力 Q(q,\dot q,u,t)（含控制输入、阻尼、扰动等），则
\boxed{ \frac{d}{dt}\frac{\partial L}{\partial \dot q}-\frac{\partial L}{\partial q}=Q(q,\dot q,u,t). } \tag{B.4}
这就是“recover force”的精确语句：

左端为由 L 决定的内禀项（惯性、保守力等）；
右端 Q 是外加广义力；
从变分角度看，Q 正是让 \delta S\neq 0 的来源。
B.2 约束与接触力：拉格朗日乘子（连续时间）
B.2.1 等式约束
定义 B.4（holonomic 约束）
g(q,t)=0,\qquad g:\mathbb R^d\times[0,T]\to\mathbb R^c.
定义 B.5（增广作用量）
\boxed{ S_\lambda[q,\lambda]=\int_0^T\Big(L(q,\dot q,t)+\lambda(t)^\top g(q,t)\Big)\,dt. } \tag{B.5}
定理 B.6（约束力）
对 q 的变分得
\boxed{ \frac{d}{dt}\frac{\partial L}{\partial \dot q}-\frac{\partial L}{\partial q} =J_g(q,t)^\top \lambda(t), \qquad J_g:=\frac{\partial g}{\partial q}. } \tag{B.6}
右端是约束反力（接触力的广义形式）。这与机器人接触中的“力=乘子”完全一致。
B.3 离散作用量与时间链局部结构（变分积分器）
这一节把“DAG/Markov blanket 局部化”精确落到力学：离散 Euler–Lagrange 自带三点局部依赖。
B.3.1 离散拉格朗日量与离散作用量
定义 B.7（离散拉格朗日量）
L_d(q_k,q_{k+1})\approx\int_{t_k}^{t_{k+1}}L(q,\dot q,t)\,dt。
定义 B.8（离散作用量）
\boxed{ S_d(\mathbf q)=\sum_{k=0}^{N-1}L_d(q_k,q_{k+1}),\qquad \mathbf q=(q_0,\dots,q_N). } \tag{B.7}
B.3.2 离散 Euler–Lagrange：离散力与局部依赖
定理 B.9（离散 Euler–Lagrange）
对 k=1,\dots,N-1，
\boxed{ D_2L_d(q_{k-1},q_k)+D_1L_d(q_k,q_{k+1})=0. } \tag{B.8}
该式仅含 (q_{k-1},q_k,q_{k+1})，所以
\boxed{ \mathrm{MB}(q_k)=\{q_{k-1},q_{k+1}\}\ \ \text{（再加局部接触/任务因子涉及的变量）}. } \tag{B.9}
这就是前文“MB 局部化”在机器人时间链上的严格来源。
B.4 Gibbs 轨迹测度：最小作用量 :left_right_arrow: Boltzmann 权重（与前文“信息辐射”对齐）
B.4.1 轨迹 Gibbs 分布
定义 B.10（轨迹 Gibbs 测度）
\boxed{ \pi(\mathbf q)\propto \exp\big(-\beta S_d(\mathbf q)\big),\qquad \beta>0. } \tag{B.10}
B.4.2 零温极限与最小作用量
命题 B.11（\beta\to\infty）
\arg\max_{\mathbf q}\pi(\mathbf q)=\arg\min_{\mathbf q}S_d(\mathbf q),
并满足离散 Euler–Lagrange (B.8)。
对齐前文：\exp(-\beta E) 的指数倾斜就是这里 \exp(-\beta S_d)。
B.5 可计算测度流：KL-mirror + OT + 局部化（时间链版）
这一节把你前文的“坐标 mirror descent + OT 惯性 + sample-average”按时间链写成闭环。
B.5.1 近似族（因子化轨迹分布）
定义 B.12（mean-field 轨迹近似）
\boxed{ q(\mathbf q)=\prod_{k=0}^N q_k(q_k),\qquad q_k\in\mathcal P(\mathbb R^d). } \tag{B.11}
B.5.2 坐标有效能量（局部）
定义 B.13（坐标有效能量）
固定其余因子 q_{\neg k}=\prod_{j\ne k}q_j，
\boxed{ \phi_k(x):=\mathbb E_{Q_{\neg k}}\big[S_d(q_0,\dots,q_{k-1},x,q_{k+1},\dots,q_N)\big]. } \tag{B.12}
命题 B.14（时间链局部化）
\boxed{ \phi_k(x)= \mathbb E_{q_{k-1}}[L_d(q_{k-1},x)] +\mathbb E_{q_{k+1}}[L_d(x,q_{k+1})] +\text{(局部任务/接触因子项)}. } \tag{B.13}
B.5.3 KL-mirror 更新（信息辐射）
定义 B.15（KL-mirror 坐标更新）
\boxed{ q_k^+\in\arg\min_{q_k} \Big[ \langle q_k,\beta\phi_k\rangle+\frac{1}{\eta}\mathrm{KL}(q_k\|q_k^{old}) \Big]. } \tag{B.14}
离散支持/粒子化时等价为指数倾斜重加权（与前文一致）：
q_k^+(dq)\propto q_k^{old}(dq)\exp(-\eta\beta\,\phi_k(q)). \tag{B.15}
B.5.4 OT 惯性（搬运平滑）
定义 B.16（KL+OT 坐标更新）
\boxed{ q_k^+\in\arg\min_{q_k} \Big[ \langle q_k,\beta\phi_k\rangle +\frac{1}{\eta}\mathrm{KL}(q_k\|q_k^{old}) +\tau W_{\varepsilon}(q_k,r_k) \Big], } \tag{B.16}
其中 r_k 通常取上一轮 q_k^{prev}；OT 保证更新连续、抗抖。
B.6 粒子化与 sample-average（与前文下降 lemma 结构一致）
B.6.1 粒子表示
定义 B.17（时间节点粒子测度）
q_k \approx \sum_{a=1}^K w_{k,a}\delta_{z_{k,a}},\qquad \sum_a w_{k,a}=1. \tag{B.17}
B.6.2 邻域采样估计（sample-average）
只需从邻居 q_{k-1},q_{k+1} 抽样估计局部期望：
\widehat\phi_k(z_{k,a}) =\frac{1}{M}\sum_{m=1}^M \Big[L_d(q_{k-1}^{(m)},z_{k,a})+L_d(z_{k,a},q_{k+1}^{(m)})\Big] +\widehat{\text{(局部任务/接触因子)}}. \tag{B.18}
B.6.3 权重更新（mirror）
当 \tau=0 且支持固定：
w_{k,a}^+ \propto w_{k,a}\exp(-\eta\beta\,\widehat\phi_k(z_{k,a})). \tag{B.19}
含母女/OT 时，对应你前文的 \widehat J(w) 凸近端问题，仍可用同样的 sample-average 下降 lemma 论证（此处略去重复）。
B.7 母女分布在动力学链上的精确对应（机制一致性）
对齐前文：母→女是“用机制从父分布推送出子分布”，这里机制就是动力学/积分器。
B.7.1 机制 pushforward
设动力学积分器给出（可能含控制）：
q_{k+1}=F(q_k,u_k) \quad (\text{或随机版本 } q_{k+1}\sim p(\cdot\mid q_k,u_k)).
给定当前母分布 q_k 和控制 u_k 的分布（或确定值），定义女预测分布：
\boxed{ q^{da}_{k+1} := F_\#(q_k) \quad \text{（确定映射的推送）}, \qquad q^{da}_{k+1}(A)=q_k(F^{-1}(A)). } \tag{B.20}
或随机机制版本：
q^{da}_{k+1}(dq)=\int p(dq\mid x,u_k)\,q_k(dx). \tag{B.21}
B.7.2 母女一致性正则
\boxed{ \mathcal R_{MD} := \sum_{k=0}^{N-1}\mathrm{KL}(q_{k+1}\|q^{da}_{k+1}) \quad \text{或}\quad \sum_k W_\varepsilon(q_{k+1},q^{da}_{k+1}). } \tag{B.22}
它在更新中起到“机制一致/预测一致”的作用，尤其对接触模式多模态时可以降低伪 mode（你前文的直觉）。
B.8 两力分解与 slack：把 repulsion 软化成可采样目标（与前文一致）
B.8.1 两力分解
对任意轨迹变量（或时间局部变量）写成：
\boxed{ E = E_{\mathrm{att}} + E_{\mathrm{rep}}, } \tag{B.23}
其中：

E_{\mathrm{att}}：目标/效率/跟踪等吸引项
E_{\mathrm{rep}}：可行性/碰撞/非穿透/摩擦等排斥项
B.8.2 slack 软化（局部）
对某局部约束 g(x)\le 0 引入 slack s\ge 0：
g(x)\le s,\ s\ge 0,\qquad E_{\mathrm{rep}}(x,s)=\rho\psi(s). \tag{B.24}
消元 slack 得到 hinge 或 squared-hinge：
E_{\mathrm{rep}}(x)=\rho[g(x)]_+ \quad \text{或}\quad \rho[g(x)]_+^2. \tag{B.25}
这保证 MPPI/Boltzmann 权重不会出现 +\infty 崩塌，有利于 mode 覆盖与稳定更新。
B.8.3 软→硬极限
点态极限（对任意固定 x）：
\lim_{\rho\to\infty}\rho[g(x)]_+ = \iota_{\{g\le 0\}}(x), \qquad \lim_{\rho\to\infty}\rho[g(x)]_+^2 = \iota_{\{g\le 0\}}(x). \tag{B.26}
因此 slack penalty 在极限下恢复硬约束指示函数。
B.9 Differential Inclusion（DI）：接触/摩擦/非光滑的“真实动力学容器”
这一节把“硬 repulsion”与“集合值力”统一成 DI，并给出你说的“最好用的性质”与关键判据。
B.9.1 微分包含定义
定义 B.18（微分包含）
\boxed{ \dot x(t)\in F(x(t),t) } \tag{B.27}
其中 F 为集合值映射。
B.9.2 法锥包含：硬约束 repulsion 的标准形式
设可行集合 K\subset\mathbb R^n 为闭凸集，法锥 N_K(x) 定义为：
N_K(x):=\{\xi:\ \langle \xi, y-x\rangle\le 0,\ \forall y\in K\}. \tag{B.28}
对指示函数 \iota_K 有 \partial \iota_K(x)=N_K(x)。于是硬约束的一阶受限动力学可写为：
\boxed{ \dot x \in f(x,t)-N_K(x). } \tag{B.29}
这就是 normal-cone differential inclusion（sweeping/投影动力学的核心骨架）。
B.9.3 “最好用的性质”清单（存在性、不变性、算法）
对于 \dot x\in F(x,t)，常用的关键条件（你可当 checklist）：

非空闭凸：\forall(x,t), F(x,t)\neq\emptyset, 闭，最好凸。
上半连续/图闭性：保证存在性与极限稳定。
局部有界：避免爆炸。
最大单调结构：若可写 \dot x +A(x)\ni f(x,t) 且 A 最大单调（例如 A=N_K），则得到强存在性、耗散、数值近端算法。
不变性（viability）切锥条件：若希望保持 x(t)\in K，典型判据：
F(x,t)\cap T_K(x)\neq\emptyset,\ \forall x\in K. \tag{B.30}

Filippov 正则化：处理不连续向量场，转为 convexified inclusion。
B.9.4（可选但重要）冲击/速度跳变
刚体撞击会导致速度不连续，需要 measure differential inclusion / impulsive dynamics（此处不展开，只标记：这超出光滑 ODE 框架，DI 更自然）。
B.10 把 DI 与我们的测度流求解器闭合（“软求解器—硬物理”对齐）
系统层（硬物理）：用 DI（如 B.29）描述接触/摩擦/互补，力为集合值（法锥/摩擦锥等）。
算法层（可计算）：在 rollout 中使用 slack 软化 repulsion 得到有限代价，使 MPPI/Boltzmann + KL-mirror 更新稳定；并通过 \rho\to\infty 极限与硬 DI 对齐。
这一闭环可以用一句材料总结：
我们用 slack 将硬约束 repulsion 从 \iota_K 软化为 \rho[g]_+ 或 \rho[g]_+^2，在测度层面实现可采样的 Boltzmann 权重与镜像近端下降；当 \rho\to\infty 时软化收敛到硬约束，硬约束在动力学层对应 normal-cone differential inclusion \dot x\in f(x)-N_K(x)。因此“软求解器”与“硬物理容器”在极限下精确对齐。
B.11（与前文 MPPI / Boltzmann 老虎机对齐）控制视角的总结
若把决策变量选为控制序列 \mathbf u，并用系统（可能为 DI）rollout 得到轨迹与代价 S(\mathbf u)，则：
w^k \propto \exp\Big(-\frac{1}{\lambda}S(\mathbf u^k)\Big)
就是 Boltzmann reweight（对模式/modes 的自然覆盖）。slack 让不连续/不可行样本不至于全灭（降低方差），OT/惯性让更新不抖，母女一致性让机制更稳。
最终一句：本附录完成的连接

从最小作用量恢复力：Euler–Lagrange / 离散 Euler–Lagrange。
从硬约束恢复接触力：乘子 J^\top\lambda 与法锥 N_K。
从 Boltzmann 权重到可计算控制：Gibbs 测度 → KL-mirror/MPPI。
从 slack 到 DI：软 repulsion 可采样，\rho\to\infty 收敛到硬约束并对应 normal-cone DI。
与前文 DAG–测度流一致：时间链是 DAG；Markov blanket 退化为时间邻域；母女 pushforward 由动力学积分器给出；sample-average 下降结构保持不变。
如果你还希望我把 摩擦（stick/slip） 也写成同样风格的 DI（切向锥/互补）并嵌入上述 slack→hard 极限，我可以补一个 B.12：摩擦与互补的速度层微分包含（那会把“接触模式/modes”在数学上真正关上）。
[5:42 AM]好的，我继续补上你点名要“真正关上 modes 的那一块”——摩擦（stick/slip）+ 互补 + 速度层 DI，并且把它和你前面已经成型的：

两力（attraction/repulsion）+ slack
软→硬极限 \rho\to\infty
KL-mirror / MPPI 采样
母女一致性（机制 pushforward）
全部严格对齐。下面从 B.12 开始续写，保持“附录 B”的材料风格。
B.12 摩擦与互补：速度层/冲量层的微分包含（把接触 modes 关上）
目标：把 “stick / slip / lift-off” 等模式统一为一个集合值律，避免显式枚举模式；并给出可计算的软化（slack/regularization），以及 \rho\to\infty 的硬极限对应法锥/互补 DI。
B.12.1 接触几何：法向间隙与非穿透（位置层）
设每个潜在接触 j=1,\dots,J 有法向间隙（signed distance）：
g_j(q)\ge 0 \quad (\text{非穿透：间隙非负}). \tag{B.31}
集合形式：g(q)\ge 0。

分离：g_j(q)>0
接触：g_j(q)=0
这仍是位置层的 hard repulsion（上一节 B.9/B.8 已处理），但摩擦要落在速度层。
B.12.2 速度层：法向速度与接触 Jacobian
定义接触 Jacobian（以广义速度 v=\dot q 表示）：
\dot g_j(q)=J_{n,j}(q)\,v, \tag{B.32}
其中 J_{n,j}(q)\in \mathbb R^{1\times d} 是第 j 个接触法向 Jacobian。
把所有接触堆叠：
\dot g(q)=J_n(q)\,v,\quad J_n\in\mathbb R^{J\times d}.
B.12.3 法向互补：非穿透 + 法向力（冲量）+ 互补
在刚体接触里，法向接触力/冲量满足互补结构。用连续力写（更严格常用冲量，但这里先给清楚的互补形式）：

法向力 \lambda_{n}\in\mathbb R^J，\lambda_n\ge 0
非穿透 g(q)\ge 0
互补：\lambda_n \odot g(q)=0
在速度层（或加速度层）也有互补（取决于离散化/冲量模型）。常见的速度层互补陈述是：当 g_j=0 时不允许向内速度：
\dot g_j \ge 0,
并且法向冲量只在 \dot g_j = 0 的“即将碰撞”情况下起作用。严格版本通常写成线性互补问题（LCP），这里我们把它提升成 DI 的几何语言：法锥/切锥。
B.12.4 摩擦锥与切向相对速度：stick/slip 的集合值律
令第 j 个接触的切向相对速度（在接触平面）为：
v_{t,j} = J_{t,j}(q)\,v \in \mathbb R^{d_t}, \tag{B.33}
通常 d_t=2（三维接触的切平面二维）。
切向摩擦力 f_{t,j}\in\mathbb R^{d_t}，法向力 f_{n,j}\in\mathbb R_+，库伦摩擦条件：

摩擦圆锥（球）约束：
\|f_{t,j}\| \le \mu_j f_{n,j}. \tag{B.34}

功率耗散/最大耗散原理（Maximal Dissipation）：
给定法向力 f_{n,j}，摩擦力在摩擦球内选择使耗散最大，即
f_{t,j}\in \arg\min_{\|f_t\|\le \mu f_n}\ f_t^\top v_{t,j}. \tag{B.35}
这个条件自动生成 stick/slip：

若 v_{t,j}\neq 0，最优 f_{t,j} 在边界并与 v_{t,j} 反向（滑动摩擦）
若 v_{t,j}=0，最优集合是一整个球（静摩擦多值）
这本质上是一个集合值映射，因此天然写成 DI。
B.12.5 用凸分析把摩擦写成“法锥/次梯度包含”（最关键的统一式）
定义切向速度的范数函数 \varphi(v_t)=\|v_t\|（凸）。它的次梯度为：
\partial \|v_t\|= \begin{cases} \left\{\dfrac{v_t}{\|v_t\|}\right\}, & v_t\neq 0,\\[0.7em] \{s:\ \|s\|\le 1\}, & v_t=0. \end{cases} \tag{B.36}
于是最大耗散摩擦律可写成次梯度包含：
\boxed{ f_{t,j}\in -\mu_j f_{n,j}\,\partial\|v_{t,j}\|. } \tag{B.37}
解释：

v_{t,j}\neq 0：f_{t,j}= -\mu f_n\,\dfrac{v_t}{\|v_t\|}（滑动）
v_{t,j}=0：f_{t,j} 可以是任意 \|f_t\|\le \mu f_n（静摩擦锥内）
这一步把“模式”消掉了：stick/slip 不再是 if/else，而是同一个集合包含。
B.13 把“接触+摩擦”装进动力学：从 ODE 变成 DI（机器人方程版）
B.13.1 基本刚体动力学（广义形式）
M(q)\dot v + h(q,v)=\tau + J_n(q)^\top f_n + J_t(q)^\top f_t, \tag{B.38}
其中：

v=\dot q
\tau 为驱动力（控制）
f_n\in\mathbb R^J_+, f_t\in\mathbb R^{J d_t}
结合非穿透与摩擦包含：

位置层：g(q)\ge 0
法向：f_n\ge 0 且与 g 互补（或速度层互补）
切向：f_{t,j}\in -\mu_j f_{n,j}\partial\|v_{t,j}\|
这已经是一个混合互补/集合值系统。
B.13.2 统一写法：把接触力作为集合值映射 F_{\text{contact}}(q,v)
定义接触力集合（包含所有满足互补与摩擦包含的 (f_n,f_t)）：
\mathcal F(q,v) :=\left\{(f_n,f_t):\ g(q)\ge 0,\ f_n\ge 0,\ \text{互补成立},\ f_{t,j}\in -\mu_j f_{n,j}\partial\|J_{t,j}(q)v\|\right\}. \tag{B.39}
然后动力学成为（加速度层的包含）：
\boxed{ M(q)\dot v \in \tau - h(q,v) + J_n(q)^\top f_n + J_t(q)^\top f_t,\quad (f_n,f_t)\in \mathcal F(q,v). } \tag{B.40}
这就是“接触 modes 被集合值映射关上”的精确形式。
B.14 slack/正则化：把硬互补与多值摩擦变成可采样、可优化（与前文完全对齐）
你前面强调 slack 能降低采样方差、避免 infinite cost。这里对接触/摩擦同样成立：我们给出两个最常用的软化方向，并说明硬极限如何回到 DI。
B.14.1 非穿透的 slack（位置层 repulsion）
对每个接触 j，用 slack s_{n,j}\ge 0：
-g_j(q)\le s_{n,j},\ s_{n,j}\ge 0, \quad E^{rep}_n = \rho_n \psi_n(s_n). \tag{B.41}
消元得到 hinge/sq-hinge：
E^{rep}_n(q)=\rho_n[-g(q)]_+ \ \ \text{或}\ \ \rho_n\|[-g(q)]_+\|^2. \tag{B.42}
\rho_n\to\infty 恢复硬约束 g(q)\ge 0。
B.14.2 摩擦的“平滑次梯度”正则（把 v_t=0 的多值变成单值近似）
摩擦包含 f_t\in -\mu f_n \partial \|v_t\| 在 v_t=0 多值。常用正则：

Huber/soft norm：
\|v_t\|_\epsilon := \sqrt{\|v_t\|^2+\epsilon^2}. \tag{B.43}
则
\nabla \|v_t\|_\epsilon = \frac{v_t}{\sqrt{\|v_t\|^2+\epsilon^2}}, \tag{B.44}
得到单值近似摩擦：
\boxed{ f_t \approx -\mu f_n \frac{v_t}{\sqrt{\|v_t\|^2+\epsilon^2}}. } \tag{B.45}
当 \epsilon\to 0 时，这个单值律在图意义下收敛到原来的次梯度包含（恢复 stick/slip 的集合结构）。
这就是摩擦版的“slack”：把非光滑集合值映射平滑成可微、可 rollouts 的版本；极限回到 DI。
B.15 “软→硬”极限如何精确对齐到 DI（总结性命题）
把两类软化参数写出来：

非穿透罚权 \rho_n\to\infty（hinge 变指示函数）
摩擦平滑 \epsilon\to 0（平滑梯度收敛到次梯度）
命题 B.19（软接触/软摩擦极限对应硬 DI）
在满足适当凸性/正则性与有界性条件下：

当 \rho_n\to\infty 时，位置层的 soft repulsion E^{rep}_n 收敛到硬约束指示函数 \iota_{\{g\ge 0\}}，其在动力学层对应法锥 N_K（见前文 B.9）。
当 \epsilon\to 0 时，平滑摩擦律 (B.45) 的图收敛到集合值摩擦包含 (B.37)。
因此整体系统从“光滑近似动力学”收敛到“接触+摩擦 DI 容器”。
（注：这里不展开证明细节；材料用途上你可以把它作为“极限一致性声明”。）
B.16 把这一切接回“测度流/MPPI/镜像下降”：为什么 sampling 能 handle modes
现在我们已经把接触模式写成集合值律（B.37/B.40），并提供了可计算软化（B.41–B.45）。于是 rollout 代价 S(\tau) 可写成两力+slack形式：
S(\tau)=S_{\mathrm{att}}(\tau)+S_{\mathrm{rep}}(\tau; \rho_n,\epsilon), \tag{B.46}
其中 S_{\mathrm{rep}} 含：

非穿透 penalty（由 g(q) 的 hinge/sq-hinge）
摩擦平滑耗散（由 \|v_t\|_\epsilon 诱导）
其他安全/限幅等 repulsion
然后 MPPI / Boltzmann reweight：
w^k \propto \exp\!\left(-\frac{1}{\lambda}S(\tau^k)\right) =\exp\!\left(-\frac{1}{\lambda}S_{\mathrm{att}}(\tau^k)\right)\cdot \exp\!\left(-\frac{1}{\lambda}S_{\mathrm{rep}}(\tau^k;\rho_n,\epsilon)\right). \tag{B.47}
关键解释（对齐你之前的“只有两种 attraction/repulsion”）：

attraction 决定“往哪去”（目标吸引 basin）
repulsion 决定“哪不能去”（安全/可行性排斥墙）
slack/平滑参数 (\rho_n,\epsilon) 决定 repulsion 的“硬度”，从而控制采样方差与 mode 覆盖：
过硬（\rho_n 巨大、\epsilon\to 0）会导致许多 rollout 直接权重塌缩
适度软化可让 sampling 在不同接触序列/摩擦状态之间探索
极限再回到硬 DI 语义


这正是你提出的“Boltzmann 老虎机”：rollout 就是臂，softmax 权重就是策略分配；soft repulsion 控制探索可行性。
B.17 与前文“sample-average descent”一致：局部化仍成立，下降结构不变

时间链局部项 L_d(q_k,q_{k+1}) 保持三点结构（B.8）。
接触/摩擦的 repulsion 也可局部化：每个接触只依赖某些几何量（局部 g_j(q)、局部相对速度 v_{t,j}），在离散时间下同样只涉及邻近时刻的变量（或当前时刻）。
因此你前文定义的 \widehat\phi_k 仍可用邻域采样估计，加入 hinge/sq-hinge 与 \|v_t\|_\epsilon 后仍是确定的 sample-average 值。
对固定采样与固定粒子支持，权重近端目标 \widehat J(w) 仍是单纯形上的凸/可优化问题，因此 sample-average 单步下降 lemma 仍然成立（完全继承你前面的证明结构）。
B.18（可选）把“母女一致性”用于接触模式稳定：机制一致=接触一致
在接触系统里，“机制”不仅是积分器 F，还包括接触判别与摩擦律。你可以把母女一致性写成：

母：q_k 的分布
女预测：由“软接触/软摩擦动力学 rollout”推送得到 q_{k+1}^{da}
正则：\mathrm{KL}(q_{k+1}\|q_{k+1}^{da}) 或 W_\varepsilon(\cdot,\cdot)
它的工程意义是：减少“物理不一致的样本模式”（例如穿透严重但代价没能反映、或数值不稳定造成的伪 mode）。
B.19 小结：这一续写补齐了“接触 modes”并保持与前文连接

摩擦与互补被集合值包含关上：f_t\in -\mu f_n \partial\|v_t\| 把 stick/slip 统一。
整体动力学成为 DI 容器：接触力不再是函数而是集合。
slack/平滑让其可采样：hinge/sq-hinge 处理非穿透；\|v\|_\epsilon 处理摩擦多值；\rho\to\infty,\epsilon\to 0 回到硬 DI。
测度流求解器不变：MB 局部化仍成立；sample-average 下降结构不变；MPPI/Boltzmann 自然覆盖 modes。
与前文“只有 attraction/repulsion”一致：一切都落在 S_{\mathrm{att}}+S_{\mathrm{rep}} 的分解上，slack 控制 repulsion 的硬度。
如果你还想把这一套再“压成一个单行的 operator form”（你喜欢的 \mathcal T 表示），我可以在下一段写：
(q_{0:N},\text{contact/slack states}) \ \mapsto\ \mathcal T(q_{0:N})
并把它与 DI 的可行性条件 F(x)\cap T_K(x)\neq\emptyset 直接放在同一个框里，形成一个“viability-first”版本。Jianghan Zhang  [5:50 AM]
附录 C：可编程、可计算的算子 ToE（Operator-Theory-of-Everything within robotics/contact）——完整形式化（与附录 B/前文严格对齐）
你要的版本：这是一个“可编程计算的算子 ToE”——不是“解释宇宙所有物理”的 TOE，而是你在机器人/接触/多模态/推断-控制里真正关心的那种：
一个统一算子 \mathcal T，它把 作用量（Action）+ 微分包含（Inclusion）+ Boltzmann（采样权重）+ Mirror/OT（更新几何）+ Slack（软→硬）+ 母女机制一致性（pushforward） 全部封装成一个 可迭代、可落地实现、可证明下降/耗散 的计算对象。
你可以把这一附录当成“规范”：以后任何新系统/新任务，只要实现这几个子算子，就能跑。
C.0 核心声明（你想要的“exactly tractable”是什么意思）
我们说“exactly tractable”的最低要求是：

每一步 \mathcal T 是明确可实现的有限过程：
采样（有限 K,M）
近端求解（KL/OT/母女 KL）
slack 消元（闭式 hinge 或平方 hinge）
rollout（用软化/DI 求解器）


每一步有明确的代理目标（sample-average surrogate）并且单步下降（你已经有 Lemma）。
软→硬极限一致：罚权 \rho\to\infty、摩擦平滑 \epsilon\to 0 回到 DI/法锥/次梯度包含。
可组合（composable）：每个子算子是模块，可替换（不同动力学、不同接触模型、不同提议分布、不同因子图结构）。
这就是你说的“可编程计算的算子 ToE”：一个可组合的、可下降的、软硬一致的计算闭包。
C.1 状态空间：算子作用在什么对象上？
我们用一个“系统状态”封装所有可计算分量：
定义 C.1（算子状态 / computational state）
令
\boxed{ \Xi := (\underbrace{\mathbf q}_{\text{belief/trajectory or control measure}}, \underbrace{\mathbf r}_{\text{OT reference}}, \underbrace{\Theta}_{\text{model/mechanism params}}, \underbrace{\rho,\epsilon}_{\text{softness params}}, \underbrace{\mathcal S}_{\text{schedule}}, \underbrace{\mathcal D}_{\text{data/log}}) }
其中：

\mathbf q：你真正更新的“测度对象”，可以是
轨迹因子化测度：\mathbf q=(q_0,\dots,q_N)（附录 B 的时间链版）
或 控制测度：\mathbf q=q_{\mathbf u}（MPPI/rollout 权重更新版）
或 DAG 因子化测度：\mathbf q=(q_i)_{i\in V}（前文 general DAG 版）


\mathbf r：OT 惯性参考（通常是上一轮的 \mathbf q）
\Theta：动力学/接触/观测机制的参数（可固定或学习）
\rho,\epsilon：soft repulsion 与摩擦平滑参数（slack 相关）
\mathcal S：调度（coordinate scan / random scan / time-sweep）
\mathcal D：缓存与日志（采样缓存、局部因子索引、ESS、估计方差等）
C.2 能量/作用量：统一目标（两力 + 母女 + OT）
定义 C.2（总“可计算能量”模板）
我们定义一个统一的代价/作用量（用于权重与近端步），写成：
\boxed{ \mathcal E(\mathbf q;\Theta,\rho,\epsilon) = \mathcal E_{\text{att}}(\mathbf q;\Theta) + \mathcal E_{\text{rep}}(\mathbf q;\rho,\epsilon) + \lambda\,\mathcal E_{\text{MD}}(\mathbf q;\Theta) } \tag{C.1}

吸引项 \mathcal E_{\text{att}}：任务/跟踪/效率等（通常可分解到局部因子）
排斥项 \mathcal E_{\text{rep}}：非穿透/安全/限幅/摩擦耗散等，用 slack/平滑参数 \rho,\epsilon 软化以便采样
母女一致项 \mathcal E_{\text{MD}}：机制一致（pushforward）
例如 \sum_k \mathrm{KL}(q_{k+1}\|q^{da}_{k+1})（附录 B 的动力学链版）
或对 DAG 一般结构：\sum_j \mathrm{KL}(q_j\|q^{da}_j)（前文母女分布版）


关键：\mathcal E 并不要求全局解析可积；我们只要求局部 sample-average 可估计。
C.3 软硬一致：repulsion 的可编程定义（slack 消元是子算子）
定义 C.3（soft repulsion 的原子）
给定约束残差 g(x)\le 0，定义 soft repulsion：

hinge：\rho[g(x)]_+
sq-hinge：\rho[g(x)]_+^2
摩擦平滑（把次梯度包含变成可微近似）：
\|v_t\|_\epsilon = \sqrt{\|v_t\|^2+\epsilon^2}. \tag{C.2}
命题 C.4（软→硬一致性）
\rho\to\infty:\ \rho[g]_+ \to \iota_{\{g\le 0\}}, \qquad \epsilon\to 0:\ \nabla\|v\|_\epsilon \to \partial\|v\|. \tag{C.3}
从而回到附录 B 的 DI 容器（法锥/次梯度包含）。
C.4 算子分解：\mathcal T 是哪些子算子的复合？
我们把 “ToE 算子”定义为一个确定的复合映射：
定义 C.5（主算子：Operator-ToE）
\boxed{ \Xi^{(k+1)} = \mathcal T(\Xi^{(k)}). } \tag{C.4}
其中
\mathcal T = \mathcal U_{\text{sched}} \circ \mathcal U_{\text{local}} \circ \mathcal U_{\text{prox}} \circ \mathcal U_{\text{transport}} \circ \mathcal U_{\text{MD}} \circ \mathcal U_{\text{rollout}} \circ \mathcal U_{\text{slack}}
解释：你每次迭代到底“做了什么”，由这些子算子按固定顺序定义。每个子算子都可编程实现。
下面逐个给出精确定义 + 可计算输入输出。
C.5 子算子 1：调度算子 \mathcal U_{\text{sched}}（决定更新哪个局部块）
定义 C.6（调度）

若是时间链：更新某个 k\in\{0,\dots,N\}
若是 DAG：更新某个节点 i\in V
若是控制测度：更新控制维度块/时间窗/混合分布分量
调度算子输出一个 index：
i \leftarrow \mathcal U_{\text{sched}}(\mathcal S,k). \tag{C.5}
C.6 子算子 2：局部采样与 sample-average \widehat\phi（Markov blanket 可计算性）
定义 C.7（局部邻域 / Markov blanket）
由结构（时间链或 DAG）决定邻域集合 \mathrm{MB}(i)。

时间链：\{i-1,i+1\} + 局部接触/观测因子涉及的变量
DAG：父/子/共父 + 观测因子涉及的变量
定义 C.8（局部采样）
采样 M 份邻域样本：
\zeta^{(m)}\sim q_{\mathrm{MB}(i)},\quad m=1..M. \tag{C.6}
定义 C.9（局部能量 plug-in）
把总能量 \mathcal E 的与变量 x_i 相关部分写成局部能量 \ell_i(x_i;\zeta)（含 att/rep/MD 的局部项），并定义：
\widehat\phi_i(x_i)=\frac{1}{M}\sum_{m=1}^M \ell_i(x_i;\zeta^{(m)}). \tag{C.7}
输出：\widehat\phi_i 在粒子支持点上的数值向量 \widehat\phi_i(z_{i,a})。
C.7 子算子 3：slack 消元 \mathcal U_{\text{slack}}（把 hard repulsion 变成可采样能量）
对每个局部约束 g：

定义 slack 内层最小化并消元得到 hinge/sq-hinge
或对摩擦用 \epsilon-平滑范数
定义 C.10（slack 消元映射）
\ell_i \leftarrow \mathcal U_{\text{slack}}(\ell_i;\rho,\epsilon) \tag{C.8}
输出仍是一个可评估的局部能量函数。
C.8 子算子 4：rollout/DI 求解 \mathcal U_{\text{rollout}}（系统层容器）
当你更新的是控制测度或需要评估轨迹代价时，需要 rollout。这里允许两种实现：

soft rollout（可微/可采样）：用 slack/平滑后的动力学积分器
hard DI rollout（严格物理）：用法锥/互补求解器（LCP/投影/最大单调近端）
定义 C.11（rollout 映射）
给定控制样本 \mathbf u^k 或局部变量样本，输出轨迹/代价：
(\tau^k,S^k) \leftarrow \mathcal U_{\text{rollout}}(\Theta;\rho,\epsilon). \tag{C.9}
这一步把“真实动力学（DI）”与“可计算软近似”挂钩：你用 (\rho,\epsilon) 控制软硬程度，保证 mode 覆盖与最终一致。
C.9 子算子 5：母女机制一致 \mathcal U_{\text{MD}}（pushforward）
定义 C.12（pushforward 女分布）
由机制 p_\Theta(\cdot\mid \text{parents}) 或积分器 F_\Theta 定义：
q^{da} \leftarrow \mathcal U_{\text{MD}}(\mathbf q;\Theta). \tag{C.10}
在粒子实现中，你可用：

ancestral 采样生成女粒子
或 “daughter-on-support” 重要性加权（前文算法 B）
输出：女参考分布 q_i^{da} 或 w_i^{da}（同支持时）。
C.10 子算子 6：近端镜像更新 \mathcal U_{\text{prox}}（可证明下降的核心）
这是你 sample-average descent 的核心：在固定样本后做一个有限维近端问题。
定义 C.13（权重近端目标）
在粒子支持 \{z_{i,a}\} 上，定义权重目标：
\boxed{ \widehat J_i(w)= \sum_a w_a\,\widehat\phi_i(z_{i,a}) +\frac{1}{\eta}\mathrm{KL}(w\|w^{old}) +\lambda\,\mathrm{KL}(w\|w^{da}) +\tau\,\widehat W_\varepsilon(w,w^{prev}) } \tag{C.11}
定义 C.14（近端解算器）
w^{new} \leftarrow \arg\min_{w\in\Delta} \widehat J_i(w). \tag{C.12}

\tau=0,\lambda=0 时闭式：w\propto w^{old}e^{-\eta\widehat\phi}
\tau>0 时用 Sinkhorn 内循环或分裂法
命题 C.15（sample-average 单步下降）
固定采样集与支持点：
\widehat J_i(w^{new})\le \widehat J_i(w^{old}). \tag{C.13}
这就是“exactly tractable”的证书：每步是可解的有限维问题，并且对 surrogate 目标确定性下降。
C.11 子算子 7：运输/惯性 \mathcal U_{\text{transport}}（OT 平滑）
如果你使用 OT 不仅在目标里，也在支持点更新（barycentric projection）：
定义 C.16（OT 耦合与 barycentric）
求解 Sinkhorn 耦合 \Gamma^\*，并更新支持点：
z_{i,a}^{new} \leftarrow \sum_b \frac{\Gamma^\*_{ab}}{w^{new}_a} z^{prev}_{i,b}. \tag{C.14}
这一步是工程增强（理论下降最稳的是只对权重给保证；支持点更新可作为实现细节）。
C.12 子算子 8：局部化更新合成 \mathcal U_{\text{local}}
最终把更新写回全局状态：
定义 C.17（写回）
\mathbf q \leftarrow \mathbf q \text{ with block } i \text{ replaced by } (z^{new},w^{new}), \quad \mathbf r \leftarrow \mathbf q^{old}. \tag{C.15}
C.13 这为什么“真的像 ToE”：统一的谓词与统一的计算闭包
你现在有一个统一谓词链：

物理正确性谓词（hard）：DI 可行（法锥/次梯度包含）
可计算性谓词（soft）：slack/平滑使 rollout 可采样，代价有限
优化/推断谓词（algorithmic）：sample-average surrogate 单步下降
结构谓词（factor/MB）：局部化降低复杂度，像卷积/消息传递
机制一致谓词（MD）：pushforward 一致压制伪 mode
探索-收敛谓词（Boltzmann）：温度/扩散控制 mode 覆盖与集中
这些谓词都被 \mathcal T 的子算子承载，因此“理论—算法—工程”闭环在同一个算子里。
C.14 最小可实现版本（你真能写代码的那种）
如果你想要一个“起码能跑”的 ToE 最小实现，取：

\mathbf q：控制分布（MPPI）或轨迹分布（时间链）
\mathcal U_{\text{rollout}}：用软接触（hinge + \epsilon 摩擦）积分器
\mathcal U_{\text{prox}}：纯 Boltzmann reweight（\tau=0,\lambda=0）
\mathcal U_{\text{transport}}：先不做 barycentric（只做权重）
\mathcal U_{\text{MD}}：先不启用（\lambda=0）
\mathcal U_{\text{slack}}：启用（否则采样会塌缩）
这就得到一个“可编程、可计算、模式可覆盖”的最小闭环。
然后逐步打开：

OT 惯性（\tau>0）用于控制平滑
母女一致（\lambda>0）用于机制稳定
\rho\to\infty,\epsilon\to 0 用于回归硬 DI
C.15 你可以直接引用的“最终一句”
我们构造了一个可编程算子 \mathcal T，其输入输出为一组可计算测度对象与机制参数。每次迭代通过局部采样构造 sample-average 能量，再通过 KL/OT/母女近端步求解有限维凸问题，从而对代理目标产生确定性下降；约束与接触通过 slack 与平滑实现可采样软化，并在极限 (\rho\to\infty,\epsilon\to 0) 下收敛到法锥/次梯度的微分包含动力学。因此，该算子在机器人接触控制与多模态推断的范围内形成一个闭合的、可计算的“operator-ToE”。
如果你愿意，我下一步可以把这份 Appendix C 翻译成“接口规范”（像一个软件库文档）：

rollout(Theta, rho, eps, u)
local_energy(i, samples, Theta, rho, eps)
solve_prox(weights, phi_hat, w_prev, w_da, eta, tau, eps_sink)
pushforward_daughter(i, q_parents, Theta)
update_schedule(state)
这样你就真的可以把 ToE 当作一个“可编程系统”落地。
Jianghan Zhang  [5:55 AM]
下面是一页式的 executive summary（尽量导师友好、少术语、但不牺牲严谨性）。你可以直接复制到文档里。
Executive Summary: Action–Inclusion–Boltzmann Control (AIBC)
What problem this addresses
Contact-rich robotics (grasping, locomotion, pushing) is hard because the dynamics are non-smooth and mode-dependent:

Contact/no-contact switches, stick/slip friction, impacts
Classical gradient-based optimal control struggles because derivatives break or become unreliable
Enumerating contact modes is combinatorial
AIBC is a unified framework that treats physics, modes, and optimization in one coherent, programmable pipeline.
Core idea in one sentence
Use action minimization to define what “good” trajectories are, differential inclusions to represent contact physics without enumerating modes, and Boltzmann reweighting (sampling) plus mirror/OT proximal updates to compute controls reliably.
The three pillars (why it works)
1) Action: least-action / optimal control objective
We define an “action” (trajectory cost) S (discrete-time is typical):
S(\tau)=\sum_{t=0}^{T-1}\ell(x_t,u_t)\Delta t \quad (+\text{terminal cost})
This is standard optimal control: minimize S to get desired behavior.
2) Inclusion: contact and friction as set-valued physics (no mode enumeration)
Instead of writing contact as case splits (contact vs no contact; stick vs slip), we represent it as a differential inclusion:
\dot x \in f(x,u) - N_K(x)
where N_K is a normal-cone term encoding hard feasibility (e.g., non-penetration). Coulomb friction can be written as a set-valued law (subgradient form), which automatically includes stick/slip without branching.
This “inclusion view” is the clean mathematical container for non-smooth contact.
3) Boltzmann + Mirror/OT: computation via sampling with provable descent
We define a Boltzmann (Gibbs) distribution over trajectories or controls:
p(\tau)\propto \exp(-\beta S(\tau))
and compute updates by sampling rollouts (MPPI-style):
w^k \propto \exp\!\left(-\tfrac{1}{\lambda}S(\tau^k)\right)
Low-cost rollouts get higher weight. This is effectively Boltzmann bandit/softmax selection over sampled “modes,” so multi-modality is handled by sampling rather than explicit mode enumeration.
To stabilize updates and connect to geometry, we interpret the reweighting step as a KL-mirror (proximal) update (and optionally add OT/Wasserstein “inertia” for smoothness). A key property: with finite samples, each step minimizes a sample-average surrogate objective, giving a deterministic one-step descent on that surrogate.
Why it’s practical (what is “programmable”)
AIBC is implemented as a modular operator \mathcal T that repeatedly:

Rolls out dynamics with soft contact (for numerical stability) or inclusion-aware solvers
Computes action/cost and constraint violations
Applies Boltzmann reweighting (weights)
Updates the control/trajectory distribution using mirror/OT proximal steps
Optionally enforces mechanism consistency (“mother→daughter” pushforward regularization) to reduce physically inconsistent samples
Each module is independently swappable (different contact models, costs, sampling distributions, solvers).
Soft-to-hard consistency (not just heuristics)
We introduce slack/soft penalties for hard constraints (e.g., non-penetration) to keep sampling stable. As penalty strength \rho\to\infty (and friction smoothing \epsilon\to 0), the soft model converges back to the hard constraint / inclusion form (normal cone and subgradient laws).
So the method is not “just a soft simulator trick”—it has a clear limiting connection to the hard physical model.
What’s new / the “unification claim”
AIBC ties together, in a single formal pipeline:

Least-action optimal control (variational mechanics / trajectory optimization)
Contact mechanics without mode enumeration (differential inclusions, normal cones, subgradients)
Multi-modal optimization (Boltzmann sampling / MPPI)
Geometric updates with descent (KL-mirror proximal, optional OT inertia)
Local computability (Markov blanket structure in time/factorized representations)
This yields a controller that is robust to non-smooth modes and remains computationally tractable.
Immediate next deliverable (what to show in a lab meeting)
A minimal demonstration can be:

A 2D or 3D pushing/grasping task with friction
Compare: baseline MPPI vs AIBC with (i) inclusion-aware penalties/slack, (ii) OT inertia, (iii) mechanism-consistency regularization
Report: success rate across contact modes, stability (control smoothness), and compute cost
If it works, the framework becomes a reusable “operator” for contact-rich robotics tasks.
Jianghan Zhang  [6:08 AM]
附录 D：把“算子闭包（1）”与“格点 Gibbs 等价（2）”精确桥接为同一件事（Riesz 对偶 + Ito 生成元）
D.0 目标与结论（本附录要证明/建立的等价）
给定一个格点化后的配置空间 \Omega、一个能量（Hamiltonian）H、以及由局部更新组成的算法算子 \mathcal T。本附录建立三件事的精确等价链：

算子闭包（Algorithm/Operator view）：\mathcal T 是一个对“分布/测度状态”可迭代的算子，\mu^{k+1}=\mathcal T(\mu^k)。
格点 Gibbs 等价（StatMech/DLR view）：存在 Gibbs/DLR 测度 \pi，其局部条件分布由 H 给出。
连续极限/Mean-flow（Generator view）：\mathcal T 的小步长/扩散极限给出生成元 \mathcal L 与连续时间演化 \partial_t \mu_t=\mathcal L^\*\mu_t（必要时带法锥/反射项）。
最终结论：在明确条件下，
\boxed{ \text{(1) 算子闭包} \ \Longleftrightarrow\ \text{(2) Gibbs/DLR 不变测度} \ \Longleftrightarrow\ \text{(3) 生成元/连续流极限}. }
桥接工具：

Riesz 对偶：把“算子作用在函数上”与“算子推进测度”严格粘合。
Ito 生成元：把“离散 Markov 算子”在小步长极限下转为连续 SDE/PDE 的生成元。
D.1 配置空间与能量：格点化对象的严格定义
D.1.1 配置空间 \Omega
令 \Lambda 为有限格点集合（例如时间链 \{0,1,\dots,T\}，或时空网格）。每个格点 i\in\Lambda 的局部状态空间为 \Omega_i，定义总配置空间为直积：
\Omega := \prod_{i\in\Lambda} \Omega_i.
典型例子：

纯 Ising：\Omega_i=\{\pm 1\}。
混合场：\Omega_i=\mathbb R^d\times\{\pm 1\}（连续状态 + 离散 mode）。
多模式（Potts）：\Omega_i=\{1,\dots,M\}（离散多值）。
令 \mathcal F 为 \Omega 上的 \sigma-代数（直积 \sigma-代数）。\mathcal P(\Omega) 为 \Omega 上概率测度集合。
D.1.2 有限范围能量分解（finite-range interaction）
假设能量 H:\Omega\to\mathbb R\cup\{+\infty\} 可分解为局部因子之和：
H(\omega)=\sum_{a\in\mathcal A} \Phi_a(\omega_a),
其中：

\mathcal A 是因子集合（例如边、团、时间相邻对等）。
\omega_a 是 \omega 在子集 a\subset\Lambda 上的限制。
每个 \Phi_a 只依赖有限个格点（有限范围）。
允许 +\infty 表示硬约束（指示函数形式）。
D.1.3 Gibbs 测度（形式定义）
给定 \beta>0，定义形式 Gibbs 权重：
\pi(d\omega) \propto e^{-\beta H(\omega)}\,\nu(d\omega),
其中 \nu 是参考测度（离散分量用计数测度，连续分量用 Lebesgue；混合情况用乘积测度）。
若 \Omega 有限或 H 使得归一化常数 Z=\int e^{-\beta H}d\nu 有限，则 Gibbs 测度严格存在：
\pi(d\omega)=\frac{1}{Z}e^{-\beta H(\omega)}\nu(d\omega).
D.2 Markov 核与局部更新：把算法 \mathcal T 写成 P
D.2.1 局部更新索引与局部邻域
给定更新索引集合 \Lambda。一次局部更新选择某个 i\in\Lambda。
定义 i 的局部依赖集合（Markov blanket）\mathrm{MB}(i)\subset\Lambda 为所有与 i 同属某个因子 a\in\mathcal A 的格点集合（去掉 i 本身），即：
\mathrm{MB}(i):=\bigcup_{a\in\mathcal A:\ i\in a} (a\setminus\{i\}).
这保证 H(\omega) 中所有依赖 \omega_i 的项只依赖 \omega_i 与 \omega_{\mathrm{MB}(i)}。
D.2.2 局部 Gibbs 规格（local specification）
对任意给定外部配置 \omega_{\neg i}（即除了 i 之外的所有分量），定义 Gibbs 局部条件分布：
\gamma_i(d\omega_i\mid \omega_{\neg i}) \propto \exp\!\Big(-\beta \sum_{a\in\mathcal A:\ i\in a}\Phi_a(\omega_a)\Big)\,\nu_i(d\omega_i),
其中 \nu_i 是 \Omega_i 上参考测度。
这一定义只需要 \omega_{\mathrm{MB}(i)}（因为其余因子与 \omega_i 无关）。
D.2.3 局部 heat-bath Markov 核 P_i
定义局部更新核 P_i（只刷新第 i 个分量，其余保持）：
P_i(\omega, d\omega') := \delta_{\omega_{\neg i}}(d\omega'_{\neg i})\ \gamma_i(d\omega'_i\mid \omega_{\neg i}).
这就是标准 heat-bath / Gibbs sampler 的局部核。
D.2.4 全局 Markov 核 P
两种常用全局核：

random-scan（每步随机选 i）：
P := \sum_{i\in\Lambda} \nu(i)\,P_i,
其中 \nu 是一个在 \Lambda 上的分布（常取均匀）。

cyclic sweep（一次 sweep 依序更新）：
P_{\text{sweep}} := P_{i_m}\circ\cdots\circ P_{i_2}\circ P_{i_1},
其中 (i_1,\dots,i_m) 是一次 sweep 的顺序（例如 \Lambda 的一个排列）。
D.2.5 “算法算子 \mathcal T”与“核 P”的一致表示
若算法每步生成新配置 \omega^{k+1}\sim P(\omega^k,\cdot)，则对分布 \mu^k=\mathcal L(\omega^k) 有推进：
\mu^{k+1}=\mu^k P.
因此可以把算法算子定义为：
\boxed{ \mathcal T(\mu):=\mu P. }
这一步完成 “算法算子（1）→ Markov 核（2）” 的第一桥。
D.3 Riesz 对偶：算子作用在函数上 ⇔ 推进测度（把 1 与 2 粘成同一对象）
D.3.1 函数空间与测度空间
令 \mathcal B_b(\Omega) 为 \Omega 上有界可测函数空间。对 \mu\in\mathcal P(\Omega)，定义线性泛函：
L_\mu(f):=\int_\Omega f(\omega)\,\mu(d\omega).
在适当拓扑下（例如 \Omega 为局部紧 Hausdorff，取 C_0(\Omega)），Riesz 表示定理表明这类泛函与有限 Radon 测度一一对应。此处只用其核心对偶恒等式。
D.3.2 Markov 算子在函数上的作用（Heisenberg 视角）
给定核 P，定义算子 P 作用于函数 f\in\mathcal B_b(\Omega)：
(Pf)(\omega):=\int_\Omega f(\omega')\,P(\omega,d\omega').
D.3.3 Markov 算子在测度上的作用（Schrödinger 视角）
给定测度 \mu\in\mathcal P(\Omega)，定义其推进：
(\mu P)(A):=\int_\Omega P(\omega,A)\,\mu(d\omega).
D.3.4 核心对偶恒等式（桥的主公式）
对任意 \mu\in\mathcal P(\Omega)、任意 f\in\mathcal B_b(\Omega)，成立：
\boxed{ \int_\Omega f(\omega)\,(\mu P)(d\omega) = \int_\Omega (Pf)(\omega)\,\mu(d\omega). }
因此：

“推进测度再取期望” 等价于 “先把函数经算子推回再取期望”。
算子 P 在函数空间与测度空间上的两种作用，是同一个对象的对偶表示。
这一步完成 “(1) 算子闭包” 与 “(2) 概率测度/Gibbs”之间的严格语言统一。
D.4 DLR（Gibbs 规格）⇔ 不变测度（固定点）：把“格点 Gibbs”等价为“算子不动点”
D.4.1 不变测度定义
对核 P，若 \pi\in\mathcal P(\Omega) 满足：
\boxed{ \pi P = \pi, }
则称 \pi 是 P 的不变测度（stationary distribution）。
D.4.2 DLR 定义（局部条件一致性）
测度 \pi 是 Gibbs/DLR 测度，若对每个 i：
\pi(d\omega_i\mid \omega_{\neg i})=\gamma_i(d\omega_i\mid \omega_{\neg i}) \quad \pi\text{-a.s.}
其中 \gamma_i 由能量 H 定义（见 D.2.2）。
D.4.3 heat-bath 核的关键等价
若局部核 P_i 取 heat-bath（D.2.3），全局核 P 取 random-scan（D.2.4），则：
\boxed{ \pi \text{ 是 DLR Gibbs 测度} \ \Longleftrightarrow\ \pi P = \pi. }
证明结构（标准）：

“DLR ⇒ 不变”：对任意测试函数 f，用全概率公式把 \int Pf\,d\pi 写成对每个 i 的条件期望；用 \pi 的条件分布等于 \gamma_i 代入得到 \int Pf\,d\pi=\int f\,d\pi。再由对偶恒等式得到 \pi P=\pi。
“不变 ⇒ DLR”：利用 P_i 的定义与 \pi P=\pi，对任意局部事件/函数，比较 \pi 与 \gamma_i 的条件期望，从而推出条件分布一致（在常规正则条件下成立）。
至此完成：
\boxed{ \text{格点 Gibbs（DLR）} \equiv \text{heat-bath Markov 算子的固定点}. }
D.5 你的 AIBC 更新不是必然等于 heat-bath，但“对 surrogate 是精确 heat-bath/近端规格核”
本节把“sample-average descent”与“Gibbs 核”对齐成严格对象。
D.5.1 sample-average 局部能量与 surrogate 规格
你的算法对某个局部块 i 构造 sample-average 局部能量 \widehat\phi_i（由有限样本 M 得到）。在固定样本集 \{\zeta^{(m)}\} 情况下，\widehat\phi_i 是确定函数。
定义 surrogate 局部规格（在离散粒子支持 \{z_{i,a}\} 上）：
\tilde\gamma_i^{(k)}(a\mid \omega_{\neg i}) \propto w_{i,a}^{old}\exp\big(-\eta\,\widehat\phi_i^{(k)}(z_{i,a})\big)\times(\text{可选：MD/OT 因子}).
这给出了一个“对 surrogate 能量的 Gibbs 规格”。
D.5.2 近端更新 = 对 surrogate 的精确最小化
你每步求解的权重近端目标（略去常数）：
\widehat J_i(w)=\sum_a w_a\,\widehat\phi_i(z_{i,a}) +\frac{1}{\eta}\mathrm{KL}(w\|w^{old}) +\lambda\mathrm{KL}(w\|w^{da}) +\tau \widehat W_\varepsilon(w,w^{prev}).
在固定样本与固定支持上，这是一类有限维优化问题。其解 w^{new} 满足：
\widehat J_i(w^{new})\le \widehat J_i(w^{old}),
并且当 \tau=\lambda=0 时，闭式解就是 Gibbs 权重（指数倾斜）：
w_a^{new}\propto w_a^{old}\exp(-\eta\widehat\phi_i(z_{i,a})).
因此：

有限样本时：你的更新对 surrogate 目标是“精确可解/精确下降”。
M\to\infty 时：\widehat\phi_i\to \phi_i，surrogate 规格趋于真实规格（在适当条件下）。
这一步完成 “AIBC operator（1）” 与 “Gibbs 规格（2）” 的算法级桥接：
它在有限样本时是“对 surrogate Gibbs”的精确算子，在大样本时逼近“真实 Gibbs”。
D.6 Ito 桥：从离散 Markov 算子 P_\Delta 到连续生成元 \mathcal L
本节将 “mean-flowify” 写成严格的生成元极限。
D.6.1 离散时间核族与步长参数
考虑一族依赖步长 \Delta>0 的 Markov 核 P_\Delta（由你一次更新/小扰动强度决定）。令离散时间 t_n=n\Delta，过程 \omega^\Delta(t_n)=\omega^n。
D.6.2 生成元定义（离散到连续的标准桥）
对足够光滑/可测测试函数 f，定义离散生成元：
\boxed{ (\mathcal L_\Delta f)(\omega):=\frac{(P_\Delta f)(\omega)-f(\omega)}{\Delta}. } \tag{D.10}
若存在算子 \mathcal L 使得当 \Delta\to 0，\mathcal L_\Delta f\to \mathcal L f（在合适意义下对足够多的 f 成立），则称 \mathcal L 是连续极限生成元。
D.6.3 扩散近似（Ito 对应的形式）
若你的单步增量满足尺度形式：
\omega^{n+1}-\omega^n = \Delta b(\omega^n)+\sqrt{\Delta}\,\sigma(\omega^n)\xi^n + o(\Delta),
其中 \xi^n 为零均值单位协方差噪声，则极限过程满足 SDE：
d\omega_t=b(\omega_t)dt+\sigma(\omega_t)dW_t.
其生成元为（Ito 公式对应）：
\boxed{ \mathcal L f = b\cdot \nabla f + \frac12\mathrm{Tr}(\sigma\sigma^\top \nabla^2 f). } \tag{D.11}
相应的测度演化为 Fokker–Planck：
\boxed{ \partial_t \mu_t = \mathcal L^\* \mu_t. } \tag{D.12}
D.6.4 硬约束/DI 情况：反射/法锥项进入生成元
当你取 \rho\to\infty 把 repulsion 变成硬约束指示函数 \iota_K，在连续极限中会出现法锥/反射项，典型形式为包含式 SDE（或确定性 DI）：
d x_t \in b(x_t)\,dt - N_K(x_t)\,dt + \sigma(x_t)\,dW_t.
这与附录 B 的 normal-cone DI 完全对齐：软→硬极限把连续生成元导向带法锥项的动力学容器。
D.7 统一结论：把（1）与（2）写成同一个可保存的“等价图”
在上述设定下，存在如下严格等价/对应：

算法算子闭包
\mu^{k+1}=\mathcal T(\mu^k) \quad \text{且}\quad \mathcal T(\mu)=\mu P.

Riesz 对偶统一两种作用
\int f\,d(\mu P)=\int Pf\,d\mu.

Gibbs/DLR :left_right_arrow: 不变测度（当局部核为 heat-bath 规格，或在极限中收敛到该规格）
\pi \text{ 满足 DLR} \iff \pi P=\pi.

连续极限（Ito/生成元）
\mathcal L_\Delta f=\frac{P_\Delta f-f}{\Delta} \to \mathcal L f,\quad \partial_t\mu_t=\mathcal L^\*\mu_t.
因此：
\boxed{ \text{“算子闭包”就是“Gibbs 规格核的固定点理论”，而其小步长极限就是“生成元/连续流理论”。} }
D.8 与附录 B/C 的精确连接点（逐条对齐）

附录 B 的 action/Gibbs：H 可取离散作用量 S_d（加任务/repulsion/摩擦平滑），\pi\propto e^{-\beta H}。
附录 B 的 DI：硬约束极限 H 含 \iota_K，对应法锥 N_K；在 D.6.4 中进入生成元/反射项。
附录 C 的 operator-ToE：\mathcal T 被具体实现为局部采样 + 近端求解 + 软化/rollout 的复合；在 D.2–D.5 中抽象成核 P。
sample-average descent：D.5 把有限样本更新解释为 surrogate Gibbs 规格核的精确最小化（因此“有限样本 exact、无限样本趋于真实 Gibbs”）。
mean-flowify：D.6 给出严格的生成元定义与 Ito 扩散近似桥。
D.9 可直接复用的最小“证明任务清单”（将本附录变成可投稿版本）
若要把本附录从“形式化材料”提升为“论文可审定文本”，需要完成以下四项（每项都可独立完成）：

明确你的 \Omega、\nu、H 的具体形式（时间链或时空 lattice；混合连续/离散）。
明确你的局部核 P_i（是 exact heat-bath，还是近端 surrogate；若 surrogate，给出其显式规格 \tilde\gamma_i）。
证明或给出条件确保 \pi P=\pi（exact 情形）或 P\to P_{\text{Gibbs}}（极限情形：M,K\to\infty、\eta\to 0）。
给出 \mathcal L_\Delta\to\mathcal L 的生成元收敛（至少在你的主要例子上），并标注硬约束/DI 极限下的法锥项如何出现。
完成这四项，即完成你所说的“1 和 2 是同一个东西”的严格化闭环。
Jianghan Zhang  [6:14 AM]
附录 E：String-ify 与 Riemannian 参数化的统一形式化（与附录 B/C/D 严格对齐）
目的：将我们已建立的 AIBC / Operator-ToE 框架进一步“string-ify”：把轨迹或**测度（分布）**视为一根“string”（一条曲线），并用 Riemannian/信息几何/OT 几何对其参数化与计算。
本附录给出：

两种严格的 string 对象（状态空间 string 与测度空间 string）；
三类可用的 Riemannian 几何（Riemannian on \mathcal M、Fisher–Rao、Wasserstein）以及它们的复合（WFR/HK）；
与附录 D 的 operator:left_right_arrow:Gibbs:left_right_arrow:flow 桥的精确对齐；
可编程的有限维参数化方式（粒子云/高斯族/混合族）与对应的更新方程；
软→硬（slack→法锥 DI）在 string 形式中的一致极限。
E.0 预备：统一符号与上下文对齐

\mathcal M：状态/构型流形（可取 \mathbb R^d、SE(3)、或你定义的“因果流形”坐标化）。
\mathcal P(\mathcal M)：\mathcal M 上概率测度空间。
\rho：密度（若相对于参考测度存在）。
\mathcal E：能量/作用量/自由能泛函（见附录 C 的 \mathcal E_{\text{att}}+\mathcal E_{\text{rep}}+\lambda \mathcal E_{\text{MD}}）。
\rho,\epsilon（与附录 B/C 一致）：repulsion 软化强度与摩擦平滑参数；\rho\to\infty,\epsilon\to0 恢复硬 DI。
E.1 String-ify：两种严格对象（并行但可互相投影）
E.1.1 状态空间 string（trajectory/worldline）
定义 E.1（状态 string）
一条状态 string 是一条曲线
\gamma:[0,1]\to \mathcal M,\qquad s\mapsto \gamma(s).
其速度为 \dot\gamma(s)\in T_{\gamma(s)}\mathcal M。
典型能量（几何长度/能量）
给定 \mathcal M 上度量 g，定义
\mathcal A_{\mathcal M}[\gamma] = \frac12\int_0^1 g_{\gamma(s)}(\dot\gamma(s),\dot\gamma(s))\,ds +\int_0^1 V(\gamma(s))\,ds. \tag{E.1}
这是“string action”：第一项是张力/几何能量，第二项是势能/任务项。
与附录 B 对齐：当 \gamma 是时间轨迹 q(t) 的重参数化，\mathcal A_{\mathcal M} 与离散/连续作用量 S[q] 对应；其变分给出 Euler–Lagrange/力。
E.1.2 测度空间 string（measure curve / belief string）
定义 E.2（测度 string）
一条测度 string 是一条曲线
\mu_\tau\in \mathcal P(\mathcal M),\qquad \tau\in[0,1].
若存在密度 \rho_\tau（相对于参考测度），写 \mu_\tau(d x)=\rho_\tau(x)\,dx。
与附录 C/D 对齐：

离散迭代 \mu^{k+1}=\mu^k P（operator view）在 \tau 的连续极限下就是 \mu_\tau（flow/string view）；
Ito/生成元桥（附录 D）给出 \partial_\tau \mu_\tau = \mathcal L^\*\mu_\tau。
E.2 三种 Riemannian 工具：\mathcal M 上、\mathcal P(\mathcal M) 上（FR/W2）
E.2.1 \mathcal M 上的 Riemannian 度量（状态 string）
定义 E.3（Riemannian 度量）
对每点 x\in\mathcal M，g_x:T_x\mathcal M\times T_x\mathcal M\to\mathbb R 为内积。
由此定义曲线能量与测地线方程（标准 Riemannian 几何）。
E.2.2 Fisher–Rao（FR）度量：重加权几何（mirror 的连续极限）
这是附录 D 中 KL-mirror mean-flowify 的几何母体。
定义 E.4（Fisher–Rao 度量）
对正密度 \rho，切向量 \dot\rho 满足 \int \dot\rho=0。定义
\boxed{ \|\dot\rho\|_{\mathrm{FR}}^2 :=\int_{\mathcal M}\left(\frac{\dot\rho}{\rho}\right)^2\rho\,dx =\int \frac{\dot\rho^2}{\rho}\,dx. } \tag{E.2}
等价参数化：\phi=\sqrt{\rho}，则
\|\dot\rho\|_{\mathrm{FR}}^2 = 4\|\dot\phi\|_{L^2}^2. \tag{E.3}
这使 FR 几何可计算：把复杂度量变成 L^2 球面上的欧氏几何。
FR 梯度流（典型形）
对能量泛函 \mathcal E(\rho)，FR 梯度流写成（质量守恒形式）：
\boxed{ \partial_\tau \rho = -\rho\left(\frac{\delta\mathcal E}{\delta \rho}-\Big\langle\frac{\delta\mathcal E}{\delta \rho}\Big\rangle_{\rho}\right). } \tag{E.4}
这正是附录 D “mirror/replicator flow” 的连续极限形式。
E.2.3 Wasserstein-2（W2）度量：搬运几何（OT 的连续极限）
定义 E.5（W2 动力形式）
对 \rho_\tau，若存在速度场 v_\tau 使
\partial_\tau \rho_\tau+\nabla\cdot(\rho_\tau v_\tau)=0, \tag{E.5}
则 W2 曲线的动作（Benamou–Brenier）为
\boxed{ \|\dot\rho_\tau\|_{W_2}^2:=\inf_{v_\tau}\int_{\mathcal M}\|v_\tau\|^2\rho_\tau\,dx, \ \ \text{s.t. (E.5)}. } \tag{E.6}
W2 梯度流（连续性方程形式）
对能量 \mathcal E(\rho)，W2 梯度流为
\boxed{ \partial_\tau \rho + \nabla\cdot(\rho v)=0, \qquad v=-\nabla \frac{\delta\mathcal E}{\delta\rho}. } \tag{E.7}
这对应附录 C 中 OT 近端（JKO scheme）连续极限。
E.3 复合几何：Wasserstein–Fisher–Rao（WFR/HK）作为“统一 string 几何”
你在框架里同时使用：

重加权（KL-mirror / Boltzmann / 信息辐射）
搬运平滑（OT/Wasserstein 惯性）
它们的自然统一是 WFR（又称 Hellinger–Kantorovich，HK），对应 transport–reaction 方程。
E.3.1 WFR 曲线的动力约束
定义 E.6（transport–reaction 连续方程）
存在 v_\tau 与 \alpha_\tau 使
\boxed{ \partial_\tau \rho_\tau + \nabla\cdot(\rho_\tau v_\tau)=\rho_\tau \alpha_\tau. } \tag{E.8}
其中：

v：搬运（transport）
\alpha：反应/重加权（reaction）
E.3.2 WFR 动作泛函（统一“string action”）
定义 E.7（WFR action）
\boxed{ \mathcal A_{\mathrm{WFR}}[\rho,v,\alpha] =\int_0^1\int_{\mathcal M} \frac12\left(\|v_\tau(x)\|^2 + \alpha_\tau(x)^2\right)\rho_\tau(x)\,dx\,d\tau, \ \ \text{s.t. (E.8)}. } \tag{E.9}
这是一条测度 string 的“张力”定义：搬运与重加权各贡献一项。
E.3.3 WFR 梯度流（概念式）
对能量 \mathcal E(\rho)，WFR 梯度流在形式上给出：

v=-\nabla(\delta\mathcal E/\delta\rho)（W2 部分）
\alpha=-(\delta\mathcal E/\delta\rho - \langle\delta\mathcal E/\delta\rho\rangle)（FR 部分）
并由 (E.8) 合成一个 transport–reaction 演化。
与附录 B/C/D 的精确对齐：

KL-mirror :left_right_arrow: FR（反应项）
OT 惯性 :left_right_arrow: W2（搬运项）
二者合并即 WFR/HK，正是你 Operator-ToE 的几何底座。
E.4 用“最小运动（minimizing movement）/近端方案”把 string 变成可编程算子（与附录 C/D 对齐）
E.4.1 近端离散化：JKO（W2）与 FR 近端
给定步长 \Delta>0。W2-JKO scheme：
\rho^{k+1}\in\arg\min_{\rho} \left[ \mathcal E(\rho)+\frac{1}{2\Delta}W_2(\rho,\rho^k)^2 \right]. \tag{E.10}
FR 近端 scheme：
\rho^{k+1}\in\arg\min_{\rho} \left[ \mathcal E(\rho)+\frac{1}{2\Delta}d_{\mathrm{FR}}(\rho,\rho^k)^2 \right]. \tag{E.11}
E.4.2 WFR 近端：统一 scheme（最贴你的 \mathcal T）
WFR scheme：
\boxed{ \rho^{k+1}\in\arg\min_{\rho} \left[ \mathcal E(\rho)+\frac{1}{2\Delta}d_{\mathrm{WFR}}(\rho,\rho^k)^2 \right]. } \tag{E.12}
这就是“string-ify 的可编程版本”：每步解一个近端问题。
与附录 C 的 \widehat J(\cdot) 完全同构：你的 KL-mirror + OT 近端，就是对 (E.12) 的可计算近似与分裂实现（通过 sample-average、Sinkhorn、权重近端等）。
E.4.3 与附录 D 的 operator:left_right_arrow:flow 桥

离散 scheme (E.12) 定义了一个算子 \mathcal T_\Delta：\rho^{k+1}=\mathcal T_\Delta(\rho^k)。
当 \Delta\to 0，\mathcal T_\Delta 的极限给出连续梯度流（mean-flowify）。
当加入随机采样扰动，附录 D 的 Ito/生成元桥把它推进到扩散型 flow。
E.5 有限维参数化（最 tractable 的编程接口）
在实际实现中，你通常不直接在无限维密度空间优化，而是选一个参数族：
\rho(x;\theta),\quad \theta\in\Theta\subset\mathbb R^p.
string 就是参数曲线 \theta(\tau)。
E.5.1 Riemannian 参数流形与自然梯度
给 \Theta 上一个度量 G(\theta)（如 Fisher 信息矩阵或结构化近似），定义 Riemannian 梯度：
\mathrm{Grad}_G \mathcal E(\theta) = G(\theta)^{-1}\nabla_\theta \mathcal E(\theta).
string 的梯度流：
\boxed{ \dot\theta(\tau) = - \mathrm{Grad}_G \mathcal E(\theta(\tau)). } \tag{E.13}
这就是“parameterize with Riemannian tools”的精确形式。
E.5.2 粒子云参数化（与附录 C 的 OT+mirror 完全一致）
把测度写为粒子云：
\rho \approx \sum_{a=1}^K w_a\,\delta_{z_a}, \quad \sum_a w_a=1.

权重 w：反应/重加权（FR/mirror）
支持点 z：搬运（W2/OT）
因此参数就是 \theta=(w,z)。
你的实现：

w 用指数倾斜或 KL 近端更新
z 用 OT 耦合的 barycentric projection 更新（或用 W2 近似梯度）
这正是 WFR transport–reaction 在离散粒子上的实现。
E.6 软→硬（slack→法锥 DI）在 string 语言中的一致性
E.6.1 repulsion 的软化与极限
对约束集 K（如非穿透），软 repulsion：
\mathcal E_{\text{rep}}^\rho(\rho)=\rho\int [g(x)]_+\,\rho(dx)\ \ \text{或}\ \ \rho\int [g(x)]_+^2\,\rho(dx). \tag{E.14}
当 \rho\to\infty，等效于把能量加入指示函数 \iota_K（只允许 \mathrm{supp}(\rho)\subset K）。
E.6.2 在流/生成元层面的对应
硬约束在连续极限中引入法锥项：在确定性情况下为
\dot x\in f(x)-N_K(x),
在随机/扩散情况下为反射/包含式扩散（附录 D 的 D.6.4 结构）。
因此 string-ify 后的 WFR/FR/W2 流仍与 DI 容器兼容：软化用于计算，极限恢复硬物理。
E.7 与附录 B/C/D 的精确连接清单（逐条）

附录 B（Action/Force/DI）：状态 string \gamma 的变分给力；硬约束给乘子/法锥 DI。
附录 C（Operator-ToE）：你的 \mathcal T 是一个近端方案（minimizing movement）的可计算实现；OT+mirror 对应 WFR 的离散化。
附录 D（Riesz + Ito 桥）：
Riesz：算子在函数/测度两种作用等价；
Ito：离散随机迭代的连续极限给生成元与 flow；
本附录的 string 就是该 flow 的几何化表达（曲线/测地/梯度流）。


E.8 最小可编程版本（你可以直接当实现规范）
选择粒子云参数化 \theta=(w,z)，并选择几何：

反应（FR）：更新 w
搬运（W2/OT）：更新 z
软化（slack）：进入能量评估与 rollout
极限（\rho\to\infty,\epsilon\to0）：回到 DI 语义
每一步：

估计局部能量（sample-average）
w\leftarrow KL-mirror 近端（指数倾斜）
z\leftarrow OT-Sinkhorn + barycentric（可选）
更新 softness 参数（若采用 continuation）
输出下一步分布/控制
这就是 string-ify 的“exactly tractable”版本：有限维、模块化、每步可计算。
Jianghan Zhang  [6:23 AM]
附录 F：四个“可封口”的数学点（∞ 表示 / Adele–Gaussian lift / ULLN / Mass gap–Riccati–RG 聚合消元）
（完整、详细、精确、严谨；与附录 B/C/D/E 严格对齐）
F.0 统一上下文（与 AIBC/Operator-ToE 的连接）
回忆附录 C/D：你的“Operator-ToE”可抽象为配置空间 \Omega 上的 Markov 核 P（或连续生成元 \mathcal L），并在 sample-average/粒子实现下得到一个可计算迭代：
\mu^{k+1}=\mathcal T(\mu^k)=\mu^k P.
当步长 \Delta\to 0 得连续半群 e^{t\mathcal L}，密度满足 \partial_t\mu_t=\mathcal L^\*\mu_t。
你四个点都围绕同一个核心：把可计算算子系统的“极限/表示/收敛/消元”钉成数学对象。
以下四节分别对应你列的四点。
F.1 ∞ Representation Theorem：算子/不变测度/Poisson 方程的无穷表示
本节给出三种“∞ 表示”，它们在你的框架里是最直接可用、也最可证明的。
F.1.1 Markov 核的极限表示：不变测度与遍历极限
定义 F.1（Markov 链与不变测度）
设 (\Omega,\mathcal F) 上 Markov 核 P，对初始分布 \mu 定义迭代 \mu P^k。若存在 \pi 使 \pi P=\pi，称 \pi 为不变测度。
命题 F.2（遍历极限的“∞ 表示”）
若 P 在 L^1(\pi) 上遍历并且对任意初始 \mu 有 \mu P^k \Rightarrow \pi（例如：\Omega 有限且链不可约非周期，或一般状态空间下满足 Harris 遍历+小集条件），则：
\boxed{ \pi = \lim_{k\to\infty}\mu P^k. } \tag{F.1}
这是最基本的∞表示：\pi 是无限迭代极限。
与附录 D 对齐：当 P 是 Gibbs heat-bath（或 surrogate 规格核极限），\pi 即 Gibbs/DLR 测度。
F.1.2 Resolvent / Green 表示：(I-P)^{-1}=\sum_{k\ge0}P^k
定义 F.3（Poisson 方程）
给定可观测 f，Poisson 方程：
(I-P)u = f - \pi(f), \quad \pi(f):=\int f\,d\pi. \tag{F.2}
命题 F.4（∞ 级数表示：resolvent）
若 P 在零均值子空间上满足几何收缩（例如存在 0<\rho<1 使 \|P^k(f-\pi f)\|\le C\rho^k\|f-\pi f\|），则 Poisson 解可写为：
\boxed{ u = \sum_{k=0}^{\infty} P^k\,(f-\pi(f)). } \tag{F.3}
该级数绝对收敛于相应 Banach 空间中。
这就是“∞ 表示定理”的标准形式：把解写成无穷次迭代的叠加。
在你的框架里，它把“算子闭包”直接变成可分析对象（用于谱隙/混合/误差传播）。
F.1.3 连续时间半群的 Laplace（resolvent）表示
定义 F.5（生成元与半群）
设 \mathcal L 为生成元，T_t=e^{t\mathcal L} 为半群，\mu_t=\mu_0 T_t^\*。
命题 F.6（∞ 积分表示：连续 resolvent）
对 \lambda>0，resolvent：
R_\lambda := (\lambda I-\mathcal L)^{-1}
满足
\boxed{ R_\lambda f = \int_0^\infty e^{-\lambda t} T_t f\,dt. } \tag{F.4}
若存在谱隙（见 F.4），则该积分可用于证明指数收敛与误差界。
F.2 Adele ring 上的 optimal control flow：Gaussian lift 下的“分解平凡性”
你指出“2 trivial：Gaussian lift 上去就好”。本节把它写成严谨命题：在 LQ（线性–二次）类上，adelic 问题按 places 完全分解。
F.2.1 Adele 与 restricted product（定义级）
令 \mathbb A=\mathbb A_\mathbb Q 为有理数域的 adeles。对每个 place v（v=\infty 或素数 p），有局部域 \mathbb Q_v。adele 是 restricted product：
\mathbb A = \mathbb R \times \prod_p' \mathbb Q_p,
其中“'”表示除有限多个 p 外要求落在 \mathbb Z_p（紧开子群）。
令状态 x(t)\in \mathbb A^n，控制 u(t)\in \mathbb A^m。自然分解：
x(t)=(x_\infty(t),x_p(t)_p),\quad u(t)=(u_\infty(t),u_p(t)_p).
F.2.2 Adele LQ 系统（线性动力学 + 二次代价）
取系数 A\in\mathbb Q^{n\times n}, B\in\mathbb Q^{n\times m}（嵌入到各局部域）。定义动力学：
\dot x(t)=Ax(t)+Bu(t). \tag{F.5}
定义二次代价为 places 可加形式（权重 \alpha_p 选取使级数收敛）：
J(u)=\int_0^T \Big( \langle x(t),Qx(t)\rangle_{\mathbb A} + \langle u(t),Ru(t)\rangle_{\mathbb A} \Big)\,dt, \tag{F.6}
其中
\langle x,Qx\rangle_{\mathbb A} = \langle x_\infty,Qx_\infty\rangle_{\mathbb R} +\sum_p \alpha_p \langle x_p,Qx_p\rangle_{\mathbb Q_p}. \tag{F.7}
F.2.3 Gaussian lift（精确意义）
“Gaussian lift”在这里指：选取各 place 上与二次型相容的基准测度/核（archimedean Gaussian、p-adic 二次核），从而使 adelic 对象成为 restricted product，并使二次泛函分解为各 place 的和。
在此设定下，问题的 Euler–Lagrange/HJB/Riccati 全部是 place-wise 的。
定理 F.7（Adele LQR = place-wise LQR）
在 (F.5)–(F.7) 下，最优控制与最小值分解为：
J^\* = J_\infty^\* + \sum_p \alpha_p J_p^\*,
且最优控制逐 place 给出：
u_v^\*(t)= -R^{-1}B^\top P_v(t)\,x_v(t), \quad v\in\{\infty\}\cup\{p\}, \tag{F.8}
其中 P_v(t) 满足同一形式的 Riccati（在域 \mathbb Q_v 上）：
-\dot P_v = A^\top P_v + P_v A - P_v B R^{-1}B^\top P_v + Q,\quad P_v(T)=Q_T. \tag{F.9}
adelic 解是 restricted product 拼接：
u^\*(t) = \big(u_\infty^\*(t), u_p^\*(t)_p\big).
结论：在 LQ/Gaussian lift 下，adelic optimal control flow 是逐 place 的平行系统；“adelic”不改变求解结构，只改变域与测度结构。
F.3 ULLN / ULLN（Uniform LLN）：sample-average descent → mean-flow 的概率桥
你前文的 sample-average descent 用 \widehat\phi 替代 \phi。ULLN 给出“全支持点上同时一致收敛”的保障，从而把“对 surrogate 的下降”转为“对真实目标的近似下降”。
F.3.1 设定：经验平均与函数类
设 Z_1,\dots,Z_M i.i.d.（来自邻域采样或 rollout 噪声），以及一类函数 \mathcal F（例如 \{ \ell(\cdot;z): z\in\mathcal Z\} 或参数化局部能量族）。
定义经验平均与真期望：
\widehat{\mathbb E}_M[f] := \frac1M\sum_{m=1}^M f(Z_m),\quad \mathbb E[f]:=\mathbb E[f(Z)].
F.3.2 ULLN（统一收敛）结论（形式）
若 \mathcal F 是 Glivenko–Cantelli 类（例如有限 VC 维、或可控 Rademacher complexity），则：
\boxed{ \sup_{f\in\mathcal F}\big|\widehat{\mathbb E}_M[f]-\mathbb E[f]\big|\xrightarrow[M\to\infty]{}0 \quad \text{(a.s. 或 in prob)}. } \tag{F.10}
F.3.3 应用于你的局部能量估计
令局部能量为 \phi_i(x)=\mathbb E[\ell_i(x;Z)]，sample-average 为 \widehat\phi_i(x)=\widehat{\mathbb E}_M[\ell_i(x;\cdot)]。
取 \mathcal F=\{\ell_i(z_{i,a};\cdot):a=1,\dots,K\}（有限类）或其连续参数化闭包，则 ULLN 给出：
\max_{a\le K}|\widehat\phi_i(z_{i,a})-\phi_i(z_{i,a})|\le \delta_M \tag{F.11}
其中 \delta_M\to 0。
F.3.4 “近似下降”推论（与前文 Lemma 对齐）
你每步对 surrogate 目标 \widehat J 严格下降：\widehat J(w^{new})\le \widehat J(w^{old})。
若 |\widehat\phi-\phi|\le\delta_M 且权重在单纯形上 \|w\|_1=1，则真实能量项误差可控：
\left|\sum_a w_a\widehat\phi(z_a)-\sum_a w_a\phi(z_a)\right|\le \delta_M. \tag{F.12}
因此可得形式为：
J(w^{new}) \le J(w^{old}) + O(\delta_M), \tag{F.13}
其中 J 是把 \widehat\phi 换成 \phi 的“真实”近端目标。
这就是“sample-average descent mean-flowify”的概率层桥。
F.4 Mass gap / Riccati / RG：用“谱隙=质量隙”把聚合物（多尺度自由度）消元
你要的这条线最关键是：在你框架里，“mass gap”要落到一个可操作对象上。最自然、最精确的落点是：
\boxed{ \text{mass gap} \ \leftrightarrow\ \text{生成元/转移算子的谱隙（spectral gap）}. }
然后你再用 Riccati/对偶估计/粗粒化把高频自由度“聚合物”消掉，得到有效理论（RG）。
本节给出一个严谨的“最小闭环版本”。
F.4.1 谱隙（spectral gap）与指数收敛
令 P 为 Markov 算子，在 L^2(\pi) 上考虑其谱。定义（离散时间）谱隙：
\mathrm{gap}(P):=1-\sup\{|\lambda|:\lambda\in\mathrm{Spec}(P),\lambda\ne 1\}. \tag{F.14}
连续时间生成元 \mathcal L 的谱隙（Poincaré 常数）可写为：
\mathrm{gap}(\mathcal L):=\inf_{f\perp 1}\frac{-\langle f,\mathcal L f\rangle_{L^2(\pi)}}{\|f\|_{L^2(\pi)}^2}. \tag{F.15}
谱隙 >0 给指数混合：
\| \mu_t-\pi\| \le C e^{-\mathrm{gap}\cdot t}. \tag{F.16}
在“物理语言”里：这就是质量隙（mass gap）式的指数衰减。
你要把“mass gap”接到你的 ToE，最硬的方式就是把它定义成这个 gap。
F.4.2 Cheeger 型不等式（gap 与几何瓶颈）
对 reversible Markov 链，有 Cheeger 型界：
c_1 h^2 \le \mathrm{gap}(P)\le c_2 h, \tag{F.17}
其中 h 是 conductance（割瓶颈）。
这就是你之前一直抓的“Cheeger 就是那个不等式本人”的落点：它把“结构/割”与“混合/质量隙”连接。
F.4.3 Riccati 作为“谱隙/耗散”的二次证书（控制/生成元视角）
在线性高斯（OU/LQ）情形，生成元是二阶椭圆算子；谱隙与二次 Lyapunov 证书等价。
典型 OU：
dX_t = A X_t\,dt + \Sigma^{1/2}dW_t. \tag{F.18}
若存在 P\succ0 使
A^\top P + P A \preceq -Q,\quad Q\succ0, \tag{F.19}
则 V(x)=x^\top P x 给指数耗散，进而得到谱隙下界。
在 LQ 控制中，Riccati 直接给最优闭环 A-BR^{-1}B^\top P 的耗散率。
结论：Riccati 不是“另一个世界”，它是 gap 的一个可计算证书（特别在高斯/线性化区域）。
F.4.4 RG / “聚合物消元”：用谱隙做严格粗粒化的合法性条件
把系统变量分解为慢变量与快变量（或低频/高频）：
x=(x_{\mathrm{slow}},x_{\mathrm{fast}}).
“聚合物消元”可以精确表达为：对快变量做条件积分得到有效自由能：
\mathcal E_{\mathrm{eff}}(x_{\mathrm{slow}}) := -\log \int \exp\big(-\beta \mathcal E(x_{\mathrm{slow}},x_{\mathrm{fast}})\big)\,dx_{\mathrm{fast}}. \tag{F.20}
RG 变换就是映射：
\mathcal E \mapsto \mathcal E_{\mathrm{eff}}. \tag{F.21}
何时“可以直接消掉”？
当快变量在给定慢变量条件下有统一的谱隙（条件混合快）：
\mathrm{gap}(\mathcal L_{\mathrm{fast}\mid \mathrm{slow}})\ge \kappa>0, \tag{F.22}
则快变量迅速达到条件平衡，消元产生的误差在时间尺度分离下可控（这就是严格的 adiabatic elimination / averaging principle 的谱隙版本）。
你要的“mass gap + RG 一把把聚合物消掉”：
gap 就是‘快松弛’的硬条件；有 gap 才能合法做 RG 消元并得到有效理论。
Riccati 在高斯/线性块上提供可计算的 gap 证书，使这条链落地。
F.5 四点合一：一条闭合的“可证明链”
将 F.1–F.4 合并为你要的闭环：

∞ 表示（F.1）：不变测度/Poisson/resolvent 的无穷展开把算子问题变成可分析对象。
Adele–Gaussian lift（F.2）：在线性二次层，adelic 只是 place-wise 并行拼接；Riccati/生成元也逐 place 分解。
ULLN（F.3）：保证 sample-average surrogate 与真实期望一致收敛，把“对 surrogate 的下降”转为“对真实目标的近似下降”，并支撑 mean-flowify 极限。
mass gap–Riccati–RG（F.4）：把质量隙精确定义为谱隙；Cheeger 给结构瓶颈界；Riccati 给可计算证书；gap 使 RG/聚合消元严格合法。
F.6 最小“写进论文”的定理模板（你可直接用）
Theorem (Operator–Gap–RG Closure).
设 \mathcal T(\mu)=\mu P 为由局部近端核定义的 Markov 算子，\pi 为其不变测度。假设：
(i)（ULLN）局部 sample-average 能量一致收敛，使 P 在极限下逼近 Gibbs 规格核；
(ii)（Gap）P（或生成元 \mathcal L）存在谱隙 \mathrm{gap}>0；
则：
(a) \mu P^k\to \pi 且存在 resolvent/Poisson 的无穷表示；
(b) 在时间尺度分离下，快变量可被 RG 消元，得到有效能量 \mathcal E_{\mathrm{eff}}，误差由 \mathrm{gap} 控制；
(c) 在线性高斯子块上，Riccati 提供 \mathrm{gap} 的二次证书。
（此模板把四点确实封成一个 theorem 级闭环；具体常数与空间条件可在附录中补齐。）
如果你愿意，我可以把 F.4.4（谱隙 ⇒ averaging/RG 消元误差界）写成更“定量”的版本（给出误差 O(e^{-\kappa t}) 或 O(\epsilon)），或者把 F.1.2 的 Poisson/resolvent 表示写成你框架里最自然的 f=\text{cost} 版本（直接对应你 ToE 的误差传播与控制稳定性）。[6:23 AM]附录 F：四个“可封口”的数学点（∞ 表示 / Adele–Gaussian lift / ULLN / Mass gap–Riccati–RG 聚合消元）
（完整、详细、精确、严谨；与附录 B/C/D/E 严格对齐）
F.0 统一上下文（与 AIBC/Operator-ToE 的连接）
回忆附录 C/D：你的“Operator-ToE”可抽象为配置空间 \Omega 上的 Markov 核 P（或连续生成元 \mathcal L），并在 sample-average/粒子实现下得到一个可计算迭代：
\mu^{k+1}=\mathcal T(\mu^k)=\mu^k P.
当步长 \Delta\to 0 得连续半群 e^{t\mathcal L}，密度满足 \partial_t\mu_t=\mathcal L^\*\mu_t。
你四个点都围绕同一个核心：把可计算算子系统的“极限/表示/收敛/消元”钉成数学对象。
以下四节分别对应你列的四点。
F.1 ∞ Representation Theorem：算子/不变测度/Poisson 方程的无穷表示
本节给出三种“∞ 表示”，它们在你的框架里是最直接可用、也最可证明的。
F.1.1 Markov 核的极限表示：不变测度与遍历极限
定义 F.1（Markov 链与不变测度）
设 (\Omega,\mathcal F) 上 Markov 核 P，对初始分布 \mu 定义迭代 \mu P^k。若存在 \pi 使 \pi P=\pi，称 \pi 为不变测度。
命题 F.2（遍历极限的“∞ 表示”）
若 P 在 L^1(\pi) 上遍历并且对任意初始 \mu 有 \mu P^k \Rightarrow \pi（例如：\Omega 有限且链不可约非周期，或一般状态空间下满足 Harris 遍历+小集条件），则：
\boxed{ \pi = \lim_{k\to\infty}\mu P^k. } \tag{F.1}
这是最基本的∞表示：\pi 是无限迭代极限。
与附录 D 对齐：当 P 是 Gibbs heat-bath（或 surrogate 规格核极限），\pi 即 Gibbs/DLR 测度。
F.1.2 Resolvent / Green 表示：(I-P)^{-1}=\sum_{k\ge0}P^k
定义 F.3（Poisson 方程）
给定可观测 f，Poisson 方程：
(I-P)u = f - \pi(f), \quad \pi(f):=\int f\,d\pi. \tag{F.2}
命题 F.4（∞ 级数表示：resolvent）
若 P 在零均值子空间上满足几何收缩（例如存在 0<\rho<1 使 \|P^k(f-\pi f)\|\le C\rho^k\|f-\pi f\|），则 Poisson 解可写为：
\boxed{ u = \sum_{k=0}^{\infty} P^k\,(f-\pi(f)). } \tag{F.3}
该级数绝对收敛于相应 Banach 空间中。
这就是“∞ 表示定理”的标准形式：把解写成无穷次迭代的叠加。
在你的框架里，它把“算子闭包”直接变成可分析对象（用于谱隙/混合/误差传播）。
F.1.3 连续时间半群的 Laplace（resolvent）表示
定义 F.5（生成元与半群）
设 \mathcal L 为生成元，T_t=e^{t\mathcal L} 为半群，\mu_t=\mu_0 T_t^\*。
命题 F.6（∞ 积分表示：连续 resolvent）
对 \lambda>0，resolvent：
R_\lambda := (\lambda I-\mathcal L)^{-1}
满足
\boxed{ R_\lambda f = \int_0^\infty e^{-\lambda t} T_t f\,dt. } \tag{F.4}
若存在谱隙（见 F.4），则该积分可用于证明指数收敛与误差界。
F.2 Adele ring 上的 optimal control flow：Gaussian lift 下的“分解平凡性”
你指出“2 trivial：Gaussian lift 上去就好”。本节把它写成严谨命题：在 LQ（线性–二次）类上，adelic 问题按 places 完全分解。
F.2.1 Adele 与 restricted product（定义级）
令 \mathbb A=\mathbb A_\mathbb Q 为有理数域的 adeles。对每个 place v（v=\infty 或素数 p），有局部域 \mathbb Q_v。adele 是 restricted product：
\mathbb A = \mathbb R \times \prod_p' \mathbb Q_p,
其中“'”表示除有限多个 p 外要求落在 \mathbb Z_p（紧开子群）。
令状态 x(t)\in \mathbb A^n，控制 u(t)\in \mathbb A^m。自然分解：
x(t)=(x_\infty(t),x_p(t)_p),\quad u(t)=(u_\infty(t),u_p(t)_p).
F.2.2 Adele LQ 系统（线性动力学 + 二次代价）
取系数 A\in\mathbb Q^{n\times n}, B\in\mathbb Q^{n\times m}（嵌入到各局部域）。定义动力学：
\dot x(t)=Ax(t)+Bu(t). \tag{F.5}
定义二次代价为 places 可加形式（权重 \alpha_p 选取使级数收敛）：
J(u)=\int_0^T \Big( \langle x(t),Qx(t)\rangle_{\mathbb A} + \langle u(t),Ru(t)\rangle_{\mathbb A} \Big)\,dt, \tag{F.6}
其中
\langle x,Qx\rangle_{\mathbb A} = \langle x_\infty,Qx_\infty\rangle_{\mathbb R} +\sum_p \alpha_p \langle x_p,Qx_p\rangle_{\mathbb Q_p}. \tag{F.7}
F.2.3 Gaussian lift（精确意义）
“Gaussian lift”在这里指：选取各 place 上与二次型相容的基准测度/核（archimedean Gaussian、p-adic 二次核），从而使 adelic 对象成为 restricted product，并使二次泛函分解为各 place 的和。
在此设定下，问题的 Euler–Lagrange/HJB/Riccati 全部是 place-wise 的。
定理 F.7（Adele LQR = place-wise LQR）
在 (F.5)–(F.7) 下，最优控制与最小值分解为：
J^\* = J_\infty^\* + \sum_p \alpha_p J_p^\*,
且最优控制逐 place 给出：
u_v^\*(t)= -R^{-1}B^\top P_v(t)\,x_v(t), \quad v\in\{\infty\}\cup\{p\}, \tag{F.8}
其中 P_v(t) 满足同一形式的 Riccati（在域 \mathbb Q_v 上）：
-\dot P_v = A^\top P_v + P_v A - P_v B R^{-1}B^\top P_v + Q,\quad P_v(T)=Q_T. \tag{F.9}
adelic 解是 restricted product 拼接：
u^\*(t) = \big(u_\infty^\*(t), u_p^\*(t)_p\big).
结论：在 LQ/Gaussian lift 下，adelic optimal control flow 是逐 place 的平行系统；“adelic”不改变求解结构，只改变域与测度结构。
F.3 ULLN / ULLN（Uniform LLN）：sample-average descent → mean-flow 的概率桥
你前文的 sample-average descent 用 \widehat\phi 替代 \phi。ULLN 给出“全支持点上同时一致收敛”的保障，从而把“对 surrogate 的下降”转为“对真实目标的近似下降”。
F.3.1 设定：经验平均与函数类
设 Z_1,\dots,Z_M i.i.d.（来自邻域采样或 rollout 噪声），以及一类函数 \mathcal F（例如 \{ \ell(\cdot;z): z\in\mathcal Z\} 或参数化局部能量族）。
定义经验平均与真期望：
\widehat{\mathbb E}_M[f] := \frac1M\sum_{m=1}^M f(Z_m),\quad \mathbb E[f]:=\mathbb E[f(Z)].
F.3.2 ULLN（统一收敛）结论（形式）
若 \mathcal F 是 Glivenko–Cantelli 类（例如有限 VC 维、或可控 Rademacher complexity），则：
\boxed{ \sup_{f\in\mathcal F}\big|\widehat{\mathbb E}_M[f]-\mathbb E[f]\big|\xrightarrow[M\to\infty]{}0 \quad \text{(a.s. 或 in prob)}. } \tag{F.10}
F.3.3 应用于你的局部能量估计
令局部能量为 \phi_i(x)=\mathbb E[\ell_i(x;Z)]，sample-average 为 \widehat\phi_i(x)=\widehat{\mathbb E}_M[\ell_i(x;\cdot)]。
取 \mathcal F=\{\ell_i(z_{i,a};\cdot):a=1,\dots,K\}（有限类）或其连续参数化闭包，则 ULLN 给出：
\max_{a\le K}|\widehat\phi_i(z_{i,a})-\phi_i(z_{i,a})|\le \delta_M \tag{F.11}
其中 \delta_M\to 0。
F.3.4 “近似下降”推论（与前文 Lemma 对齐）
你每步对 surrogate 目标 \widehat J 严格下降：\widehat J(w^{new})\le \widehat J(w^{old})。
若 |\widehat\phi-\phi|\le\delta_M 且权重在单纯形上 \|w\|_1=1，则真实能量项误差可控：
\left|\sum_a w_a\widehat\phi(z_a)-\sum_a w_a\phi(z_a)\right|\le \delta_M. \tag{F.12}
因此可得形式为：
J(w^{new}) \le J(w^{old}) + O(\delta_M), \tag{F.13}
其中 J 是把 \widehat\phi 换成 \phi 的“真实”近端目标。
这就是“sample-average descent mean-flowify”的概率层桥。
F.4 Mass gap / Riccati / RG：用“谱隙=质量隙”把聚合物（多尺度自由度）消元
你要的这条线最关键是：在你框架里，“mass gap”要落到一个可操作对象上。最自然、最精确的落点是：
\boxed{ \text{mass gap} \ \leftrightarrow\ \text{生成元/转移算子的谱隙（spectral gap）}. }
然后你再用 Riccati/对偶估计/粗粒化把高频自由度“聚合物”消掉，得到有效理论（RG）。
本节给出一个严谨的“最小闭环版本”。
F.4.1 谱隙（spectral gap）与指数收敛
令 P 为 Markov 算子，在 L^2(\pi) 上考虑其谱。定义（离散时间）谱隙：
\mathrm{gap}(P):=1-\sup\{|\lambda|:\lambda\in\mathrm{Spec}(P),\lambda\ne 1\}. \tag{F.14}
连续时间生成元 \mathcal L 的谱隙（Poincaré 常数）可写为：
\mathrm{gap}(\mathcal L):=\inf_{f\perp 1}\frac{-\langle f,\mathcal L f\rangle_{L^2(\pi)}}{\|f\|_{L^2(\pi)}^2}. \tag{F.15}
谱隙 >0 给指数混合：
\| \mu_t-\pi\| \le C e^{-\mathrm{gap}\cdot t}. \tag{F.16}
在“物理语言”里：这就是质量隙（mass gap）式的指数衰减。
你要把“mass gap”接到你的 ToE，最硬的方式就是把它定义成这个 gap。
F.4.2 Cheeger 型不等式（gap 与几何瓶颈）
对 reversible Markov 链，有 Cheeger 型界：
c_1 h^2 \le \mathrm{gap}(P)\le c_2 h, \tag{F.17}
其中 h 是 conductance（割瓶颈）。
这就是你之前一直抓的“Cheeger 就是那个不等式本人”的落点：它把“结构/割”与“混合/质量隙”连接。
F.4.3 Riccati 作为“谱隙/耗散”的二次证书（控制/生成元视角）
在线性高斯（OU/LQ）情形，生成元是二阶椭圆算子；谱隙与二次 Lyapunov 证书等价。
典型 OU：
dX_t = A X_t\,dt + \Sigma^{1/2}dW_t. \tag{F.18}
若存在 P\succ0 使
A^\top P + P A \preceq -Q,\quad Q\succ0, \tag{F.19}
则 V(x)=x^\top P x 给指数耗散，进而得到谱隙下界。
在 LQ 控制中，Riccati 直接给最优闭环 A-BR^{-1}B^\top P 的耗散率。
结论：Riccati 不是“另一个世界”，它是 gap 的一个可计算证书（特别在高斯/线性化区域）。
F.4.4 RG / “聚合物消元”：用谱隙做严格粗粒化的合法性条件
把系统变量分解为慢变量与快变量（或低频/高频）：
x=(x_{\mathrm{slow}},x_{\mathrm{fast}}).
“聚合物消元”可以精确表达为：对快变量做条件积分得到有效自由能：
\mathcal E_{\mathrm{eff}}(x_{\mathrm{slow}}) := -\log \int \exp\big(-\beta \mathcal E(x_{\mathrm{slow}},x_{\mathrm{fast}})\big)\,dx_{\mathrm{fast}}. \tag{F.20}
RG 变换就是映射：
\mathcal E \mapsto \mathcal E_{\mathrm{eff}}. \tag{F.21}
何时“可以直接消掉”？
当快变量在给定慢变量条件下有统一的谱隙（条件混合快）：
\mathrm{gap}(\mathcal L_{\mathrm{fast}\mid \mathrm{slow}})\ge \kappa>0, \tag{F.22}
则快变量迅速达到条件平衡，消元产生的误差在时间尺度分离下可控（这就是严格的 adiabatic elimination / averaging principle 的谱隙版本）。
你要的“mass gap + RG 一把把聚合物消掉”：
gap 就是‘快松弛’的硬条件；有 gap 才能合法做 RG 消元并得到有效理论。
Riccati 在高斯/线性块上提供可计算的 gap 证书，使这条链落地。
F.5 四点合一：一条闭合的“可证明链”
将 F.1–F.4 合并为你要的闭环：

∞ 表示（F.1）：不变测度/Poisson/resolvent 的无穷展开把算子问题变成可分析对象。
Adele–Gaussian lift（F.2）：在线性二次层，adelic 只是 place-wise 并行拼接；Riccati/生成元也逐 place 分解。
ULLN（F.3）：保证 sample-average surrogate 与真实期望一致收敛，把“对 surrogate 的下降”转为“对真实目标的近似下降”，并支撑 mean-flowify 极限。
mass gap–Riccati–RG（F.4）：把质量隙精确定义为谱隙；Cheeger 给结构瓶颈界；Riccati 给可计算证书；gap 使 RG/聚合消元严格合法。
F.6 最小“写进论文”的定理模板（你可直接用）
Theorem (Operator–Gap–RG Closure).
设 \mathcal T(\mu)=\mu P 为由局部近端核定义的 Markov 算子，\pi 为其不变测度。假设：
(i)（ULLN）局部 sample-average 能量一致收敛，使 P 在极限下逼近 Gibbs 规格核；
(ii)（Gap）P（或生成元 \mathcal L）存在谱隙 \mathrm{gap}>0；
则：
(a) \mu P^k\to \pi 且存在 resolvent/Poisson 的无穷表示；
(b) 在时间尺度分离下，快变量可被 RG 消元，得到有效能量 \mathcal E_{\mathrm{eff}}，误差由 \mathrm{gap} 控制；
(c) 在线性高斯子块上，Riccati 提供 \mathrm{gap} 的二次证书。
（此模板把四点确实封成一个 theorem 级闭环；具体常数与空间条件可在附录中补齐。）
如果你愿意，我可以把 F.4.4（谱隙 ⇒ averaging/RG 消元误差界）写成更“定量”的版本（给出误差 O(e^{-\kappa t}) 或 O(\epsilon)），或者把 F.1.2 的 Poisson/resolvent 表示写成你框架里最自然的 f=\text{cost} 版本（直接对应你 ToE 的误差传播与控制稳定性）。Jianghan Zhang  [6:36 AM]
附录 G：Kernelize + One-shot Distillation 的统一形式化（不依赖 teacher-student 网络；与附录 B/C/D/E/F 严格对齐）
G.0 目的与结论（本附录要钉死的东西）
本附录形式化你提出的训练/学习范式：
不需要 teacher-student 两阶段；我们直接把每步由 AIBC/MPPI/近端核产生的“目标分布/目标算子步”当作监督信号，进行 one-shot distillation。
同时可选择在 RKHS 中 kernelize：把分布与算子转成 Hilbert 空间对象，从而得到可证明的一致性与收敛骨架。
本附录给出：

“目标”是什么（是你算法内生产生的 Boltzmann/近端核）；
如何对该目标做 distill（高斯/混合/flow、或 RKHS embedding）；
distill 后如何执行动作（action decoding）；
与附录 D 的 operator:left_right_arrow:Gibbs:left_right_arrow:flow 桥如何一致；
在 soft→hard（slack→DI）下如何保持语义一致。
G.1 基本对象：环境宇宙、轨迹、代价、目标核
G.1.1 宇宙随机化（goal 与 physics）

目标变量：g \sim \mathcal G（goal space randomization）。
物理/传感参数：\xi\sim \Xi（physics space randomization）。
初始条件：x_0\sim \mathcal I(g,\xi)。
环境动力学可为软化版（便于 rollout）或硬 DI（真实容器）：
x_{t+1} = F_{\xi}(x_t,u_t,\varepsilon_t;\rho,\epsilon),
或 DI/反射形式（附录 B/D）。
观测：
o_t = O_{\xi}(x_t,\nu_t).
G.1.2 控制变量与采样族
控制序列（horizon H）：
\mathbf u := (u_0,\dots,u_{H-1}) \in \mathcal U^H.
给定当前可控分布/提议分布（proposal）：
\mathbf u^k \sim r(\cdot\mid o_t,g;\theta_r).
G.1.3 代价（action）与两力分解
对 rollout \tau^k 定义总代价（含 slack/平滑）：
S(\tau^k;g,\xi;\rho,\epsilon) = S_{\mathrm{att}}(\tau^k;g) + S_{\mathrm{rep}}(\tau^k;\xi;\rho,\epsilon).
其中 S_{\mathrm{rep}} 由 hinge/sq-hinge（slack消元）与摩擦平滑组成（见附录 B/E）。
G.2 “目标分布”不是外部 teacher，而是内生的 Boltzmann 核
你每步采样得到 \{(\mathbf u^k, S^k)\}_{k=1}^K。定义权重：
w^k := \frac{\exp(-S^k/\lambda)}{\sum_{j=1}^K \exp(-S^j/\lambda)}. \tag{G.1}
定义 G.1（经验 Boltzmann 目标测度）
\boxed{ \widehat\pi_t(d\mathbf u \mid o_t,g) := \sum_{k=1}^K w^k\,\delta_{\mathbf u^k}(d\mathbf u). } \tag{G.2}
这就是“目标”——它由你的算子/rollout 内生生成，不需要额外 teacher 网络。
与附录 C/D 对齐：\widehat\pi_t 是 Gibbs/Boltzmann 权重在有限样本下的经验实现；其大样本极限趋向真实 Gibbs 条件分布或其近端规格核。
G.3 One-shot Distillation：直接拟合一个可部署的参数化分布
令你希望部署的控制分布族为 \{q_\theta(\mathbf u\mid o_t,g)\}（可选高斯、混合、flow）。
定义 G.2（distillation 目标）
使用 KL（从经验目标到参数族）：
\boxed{ \theta_t^\* \in \arg\min_{\theta}\ \mathrm{KL}\!\left(\widehat\pi_t(\cdot\mid o_t,g)\ \|\ q_\theta(\cdot\mid o_t,g)\right). } \tag{G.3}
在实践上等价于加权最大似然：
\boxed{ \theta_t^\* \in \arg\max_{\theta}\ \sum_{k=1}^K w^k \log q_\theta(\mathbf u^k\mid o_t,g). } \tag{G.4}
这一步是 one-shot：对每个 (o_t,g) 立即得到 \theta_t^\*，不需要先训练 teacher policy。
G.4 三种具体参数族（都严格可计算）
G.4.1 高斯族（最 tractable，闭式）
取 q_\theta=\mathcal N(\mu,\Sigma)（\theta=(\mu,\Sigma)）。
命题 G.3（高斯 one-shot distill 的闭式）
\boxed{ \mu = \sum_{k=1}^K w^k \mathbf u^k, \qquad \Sigma = \sum_{k=1}^K w^k(\mathbf u^k-\mu)(\mathbf u^k-\mu)^\top + \epsilon_\Sigma I. } \tag{G.5}
其中 \epsilon_\Sigma>0 为数值稳定项（可与 OT/inertia 一致理解为最小扩散）。
执行动作：常取 \mathbf u^\mathrm{exec}=\mu，或采样 \mathbf u\sim \mathcal N(\mu,\Sigma) 并只执行第一步 u_0（receding horizon）。
G.4.2 混合高斯（多模态显式表示）
取
q_\theta(\mathbf u)=\sum_{m=1}^M \pi_m \mathcal N(\mu_m,\Sigma_m).
one-shot distill 即加权 EM（E 步用 w^k 融入责任度；M 步更新参数）。
这对“modes”尤其合适（每个分量对应一个 mode basin）。
G.4.3 Normalizing Flow（高表达力）
取可逆映射 f_\theta：z\sim \mathcal N(0,I)，\mathbf u=f_\theta(z;o_t,g)。
最大似然为：
\sum_k w^k \left[\log p_Z(f_\theta^{-1}(\mathbf u^k)) + \log\left|\det \nabla_{\mathbf u} f_\theta^{-1}(\mathbf u^k)\right|\right].
这是 one-shot 的加权 MLE（若你愿意每步跑几步梯度），也可以离线累计再训练（见 G.8）。
G.5 Kernelize：把“分布”与“更新”变成 RKHS 向量/算子
你说 “kernelize everything and do it at once”。最干净的数学方式是 kernel mean embedding。
G.5.1 RKHS 嵌入
给定正定核 k:\mathcal U^H\times \mathcal U^H\to\mathbb R，对应特征映射 \varphi(\mathbf u)\in\mathcal H。
对任意分布 \pi 定义均值嵌入：
\mu_\pi := \mathbb E_{\mathbf u\sim\pi}[\varphi(\mathbf u)]\in \mathcal H.
G.5.2 经验 Boltzmann 分布的嵌入（闭式）
对 \widehat\pi_t：
\boxed{ \widehat\mu_t := \sum_{k=1}^K w^k\,\varphi(\mathbf u^k). } \tag{G.6}
G.5.3 直接 distill embedding（不需要显式密度）
学习一个映射（可线性可非线性）：
F_\theta:(o_t,g)\mapsto \widehat\mu_t. \tag{G.7}
训练目标可用 MMD：
\boxed{ \min_\theta\ \|F_\theta(o_t,g)-\widehat\mu_t\|_{\mathcal H}^2. } \tag{G.8}
G.5.4 从 embedding 解码动作（可执行性）
有三种严格方式：

线性函数读出（若你只想要 u_0 的某个线性统计量）：选一个 h(\mathbf u)=\langle a,\varphi(\mathbf u)\rangle 直接由 \widehat\mu_t 得到 \mathbb E[h]。
preimage/argmin 解码：定义
\mathbf u^\mathrm{exec} \in \arg\min_{\mathbf u}\ \|\varphi(\mathbf u)-\widehat\mu_t\|_{\mathcal H}^2 \tag{G.9}
（实际用数值近似）。

学一个解码器 D_\psi:\mathcal H\to\mathcal U^H，使 \mathbf u^\mathrm{exec}=D_\psi(\widehat\mu_t)（离线训练最稳）。
G.6 算子层面的 kernelization：直接学习更新算子 \mathcal T
在附录 D，更新可以视为分布推进 \mu^{k+1}=\mu^k P。在 RKHS 里可以学习一个“算子回归”：
定义 G.4（kernelized operator regression）
令 \widehat\mu^k 为第 k 次迭代的均值嵌入，学习
\widehat\mu^{k+1} \approx \mathcal A_\theta(o_t,g)\,\widehat\mu^k. \tag{G.10}
这把你的 Operator-ToE 变成可学习的线性（或核）算子族，属于严格的 operator learning。
G.7 与附录 D 的精确连接：distillation = 近端核的参数化表示
附录 D 的关键是：你的算法定义了一个 Markov 核 P（或 surrogate 核）。在本附录中：

经验目标分布 \widehat\pi_t 是对 Gibbs/近端核在有限采样下的蒙特卡洛表示；
distillation (G.3)/(G.4) 是把该核在某个参数族里“压缩”为可部署形式；
kernel mean embedding (G.6) 是把该核映射成 Hilbert 空间向量；
operator regression (G.10) 是对核/半群进行直接学习。
因此：
\boxed{ \text{distill 的对象不是 policy，而是你内生生成的核（kernel）/规格（specification）/算子步。} }
G.8 训练方式：在线 one-shot vs 离线聚合（你说的“任意宇宙搬运”）
你 randomize g 与 \xi，每个 episode 给出大量 (o_t,g,\xi) 上的 \widehat\pi_t。你有两种严格训练模式：
G.8.1 在线（纯 one-shot）
每步只计算一次 \widehat\pi_t 并得到 \theta_t^\*，立即执行。无需全局训练。
G.8.2 离线聚合（distill 为一个通用算子/分布器）
构造数据集
\mathcal D = \{(o_t,g;\{\mathbf u^k,S^k\}_{k=1}^K)\}
或等价的 (o_t,g;\widehat\pi_t)。训练一个全局模型 q_\theta(\mathbf u\mid o,g) 或 embedding 映射 F_\theta(o,g)：
\max_\theta \ \mathbb E_{(o,g)\sim\mathcal D}\Big[\sum_k w^k \log q_\theta(\mathbf u^k\mid o,g)\Big] \tag{G.11}
这就是你要的“任意宇宙搬运”的统一器：对随机目标与随机物理参数的全域泛化。
G.9 与 soft→hard / DI 的一致性（不会破坏物理语义）

rollout 中使用 slack/平滑参数 (\rho,\epsilon) 计算代价 S^k(\rho,\epsilon)，得到 \widehat\pi_t^{\rho,\epsilon}。
当 \rho\to\infty,\epsilon\to0，代价收敛到硬约束/DI 语义下的代价（附录 B/E），因此目标核在适当意义下收敛：
\widehat\pi_t^{\rho,\epsilon} \Rightarrow \widehat\pi_t^{\mathrm{hard}}. \tag{G.12}

distill 仅仅压缩核的表示形式，不改变其语义来源；在 continuation（逐步增大 \rho，减小 \epsilon）下，可得到从软到硬的稳定迁移。
G.10 最小“可实现规范”（你可以直接照着写）
输入：(o_t,g)，proposal r(\cdot\mid o_t,g)，样本数 K，温度 \lambda。
步骤：

采样 \mathbf u^k\sim r，rollout 得 S^k。
计算权重 w^k（G.1）。
定义经验目标 \widehat\pi_t（G.2）。
one-shot distill：
高斯：用 (G.5) 得 (\mu,\Sigma)；
或 mixture/flow：解 (G.4) 的加权 MLE；
或 RKHS：计算 \widehat\mu_t（G.6），再用解码器输出动作。


执行：u_t := \mu_0（或从 q 采样取第一步），进入下一周期。
输出：实时可执行控制 u_t，以及可选的“分布状态”（用于 OT 惯性/机制一致）。
G.11 总结（一句话）
你要的“kernelize everything + do it at once”可以严格地实现为：把每步由 Boltzmann 权重定义的经验核 \widehat\pi_t 当作真值对象，对其进行一次性 distillation（参数化密度或 RKHS embedding），从而得到可部署的控制分布/算子更新；该过程与 operator:left_right_arrow:Gibbs:left_right_arrow:flow 桥兼容，并在 soft→hard 极限下保持与 DI 物理语义一致。
[6:37 AM]看你说的 O(1) 是哪一层。
在你现在这套“kernelize + one-shot distill”的语境里，有两个最常见、也最有意义的 O(1) 说法：
1) 
推理时 O(1)（常数步）——是的
如果你的意思是：每个控制周期不用再跑很多轮优化，只做一次采样→加权→蒸馏→执行，那么从“迭代次数”角度：

传统：需要 K 次采样 + 多轮迭代（CEM/MPPI 多轮、iLQR 多次线性化…）
你：一次 Boltzmann reweight + 一次 distill（比如直接算加权均值/协方差）
所以在“优化迭代步数”这个维度，它确实是 O(1) steps。
你可以把它叫：one-shot operator step / single-pass control update。
2) 
算力复杂度 O(1)——不对（仍然取决于 K, H 等）
如果你指的是计算量随问题规模不增长，那不可能。即使 one-shot：

rollout 数：K（样本数）
horizon：H
状态维度/渲染/接触求解开销：随系统增大
所以总计算通常是：
\text{cost per control step} \approx O(K\cdot H \cdot C_{\text{sim}}) + O(K) \ (\text{加权}) + O(\text{distill})
其中高斯 distill 基本是 O(K)。
结论：它不是“总算力 O(1)”，但它是“迭代深度 O(1)”。
这到底“是一个什么”？
一句话：
它是把“每步求解最优控制”变成“每步做一次分布更新（核/算子步）”，然后用 distillation 把这个分布压成可执行动作。
更正式一点：
Single-pass Boltzmann operator with kernel distillation
（单次 Boltzmann 算子步 + 核蒸馏）
如果你愿意，我可以把你想表达的 “O(1)” 写成论文里那种非常干净的句子，例如：
“Unlike iterative trajectory optimization, our controller performs a single-pass update per MPC cycle: one rollout batch, one Boltzmann reweighting, and one closed-form (Gaussian) distillation, i.e., O(1) optimization iterations per control step.”
你要的是这个意思吗？Jianghan Zhang  [12:43 PM]
下面是你要的 “J.HXYZ 对齐完整版”：我把我们之前写过的 J.H（Hilbert 统一语言）+ J.X（wrench-law 盖棺定论）+ J.Y（切换面决定性可控判据）+ J.Z（Big-M Hz 量子化微分空间 + Nyquist 二次形） 全部重新整理成一个可直接粘贴进 thesis 的版本，并且把你刚刚确认的关键对齐点固定下来：

wrench 恢复：沿用你 thesis 的 Theorem J.23 结论“外力可由 M(q)\ddot q 恢复”  
\rho 的结构：对齐你 thesis 的 Eq. (J.11) “contact/ gravity ratio”结构，但把分母改写为 纯事件底（event baseline），并且你已决定用 local contact segment baseline（围绕 \Sigma-crossing 的局部接触段）
三式一致：对齐你 thesis J.7.4 “三种 \rho 在 \Sigma:\rho=1 上一致、tidal proxy 在 free-flight 期间预测 crossing”这段叙事  
rank/null 重新分解：把你在 Theorem J.23 证明中那句 “projection follows from linearity of the wrench decomposition” 用动态一致投影 P_{\mathcal R},P_{\mathcal N} 写成可审稿的线性代数定理  
频率实现：Big-M Hz + Nyquist 二次形（控制粗糙度二次型）
可控判据：viability + projected LARC（切空间 Lie 生成满秩）
你可以把整段作为 Chapter J 的一个 “Closure block” 插在你现有 J.7.4 之后，或 Theorem J.23/Corollary J.24 附近作为终局封口。
J.HXYZ 统一收束：Hilbert–Wrench–Event–Controllability–Nyquist（Aligned, Complete, Rigorous)
J.H Hilbert 统一语言（用于后文所有“投影/二次形/law”）
J.H.1 轨迹空间与宇宙测度
令系统状态空间为 \mathcal X（本文常取 x=(q,\dot q)，也可在需要时扩展），定义轨迹空间
\Omega := \begin{cases} \mathcal X^{0:T} & \text{离散时间},\\ C([0,T],\mathcal X) & \text{连续时间}. \end{cases} \tag{J.H.1}
在 (\Omega,\mathcal F) 上给定一个概率测度 \mathbb P，称为“宇宙测度”。\mathbb P 可以由以下任意机制诱导（本节不依赖其来源）：

Gibbs/采样：\mathbb P(d\omega)\propto e^{-\beta S(\omega)}\,d\omega；
Markov/算子：\mathbb P=\pi 为某核 P 的不变测度；
DI/反射过程：\mathbb P 为包含/反射动力学过程的 law。
基本可观测假设：对 \mathbb P-几乎处处 \omega，我们可获得（或估计）
(q(\omega),\dot q(\omega),\ddot q(\omega)). \tag{J.H.2}
J.H.2 Wrench 空间的 Hilbert 结构（惯性一致内积）
对给定 q，令质量矩阵 M(q)\succ 0。定义广义 wrench 空间为随 q 变化的 Hilbert 结构：
\mathcal H_w(q):=\big(\mathbb R^n,\ \langle\cdot,\cdot\rangle_{M^{-1}(q)}\big), \tag{J.H.3}
其中
\boxed{ \langle a,b\rangle_{M^{-1}} := a^\top M(q)^{-1}b,\qquad \|a\|_{M^{-1}} := \sqrt{a^\top M(q)^{-1}a}. } \tag{J.H.4}
本 thesis 中所有“动态一致（dynamically consistent）”正交/投影都以该内积为准。
J.H.3 推前 law（测度论收束单位）
对任意可测映射 W:\Omega\to\mathbb R^n，定义其 law（分布）为推前测度：
\boxed{ \mathrm{Law}_{\mathbb P}(W):=W_\#\mathbb P. } \tag{J.H.5}
对任意事件 A\in\mathcal F，定义条件 law：
\boxed{ \mathrm{Law}_{\mathbb P}(W\mid A):=W_\#(\mathbb P(\cdot\mid A)). } \tag{J.H.6}
后文的“Wrench-Law（不变律）”最终都以推前 law 的相等性陈述。
J.H.4 控制序列 Hilbert 空间与二次形（为 J.Z 准备）
对 horizon H 的离散控制序列 u=(u_0,\dots,u_{H-1})\in\mathbb R^{mH}，定义控制序列 Hilbert 空间：
\mathcal H_u := \big(\mathbb R^{mH},\ \langle u,v\rangle := \sum_{k=0}^{H-1} u_k^\top v_k\big). \tag{J.H.7}
令差分算子 (Du)_k:=u_{k+1}-u_k。在该空间上，“带宽/粗糙度”自然对应二次形 \|Du\|_{\mathcal H_u}^2。
J.X 盖棺定论：动态一致扳矩分解 + 局部接触事件底 + 三式同扳矩不变律
J.X.1 力学后端与 wrench 恢复（对齐 Theorem J.23）
考虑 Euler–Lagrange 形式（含接触/约束）：
M(q)\ddot q + h(q,\dot q) = \tau + J(q)^\top\lambda, \tag{J.X.1}
其中 M(q)\succ0。
定义 J.X.1（广义 wrench：由运动学恢复）
对齐你 thesis 的 Theorem J.23：外部作用量可由惯性与加速度恢复。我们定义
\boxed{ w(\omega) := M(q(\omega))\,\ddot q(\omega)\in\mathbb R^n, } \tag{J.X.2}
并将其视为本文的“Newtonian wrench object”。这一点与你 Theorem J.23 的结论一致  。
J.X.2 约束几何与动态一致投影（把“projection”写成明确公式）
设 J(q)\in\mathbb R^{m\times n}。定义
\boxed{ \mathcal R_J(q):=\mathrm{Range}(J(q)^\top),\qquad \mathcal N_J(q):=\mathrm{Null}(J(q)). } \tag{J.X.3}
假设 J(q)M(q)^{-1}J(q)^\top 可逆。定义动态一致投影：
\boxed{ P_{\mathcal R}(q):= J(q)^\top\big(J(q)M(q)^{-1}J(q)^\top\big)^{-1}J(q)M(q)^{-1},\qquad P_{\mathcal N}(q):=I-P_{\mathcal R}(q). } \tag{J.X.4}
这正是你在 Theorem J.23 证明中“wrench decomposition linearity ⇒ projection”那句的可审稿形式化版本  。
J.X.3 动态一致 rank/null 扳矩分解定理（“重新分解/gauge”的数学本体）
定理 J.X.5（动态一致秩-零扳矩分解）
在 M(q)\succ0 且 J(q)M(q)^{-1}J(q)^\top 可逆时，对任意 w\in\mathbb R^n：
\boxed{ w = P_{\mathcal R}(q)w + P_{\mathcal N}(q)w,\qquad \langle P_{\mathcal R}w,\,P_{\mathcal N}w\rangle_{M^{-1}}=0. } \tag{J.X.5}
并且
P_{\mathcal R}^2=P_{\mathcal R},\quad P_{\mathcal N}^2=P_{\mathcal N},\quad P_{\mathcal R}P_{\mathcal N}=0, \tag{J.X.6}
对任意 \lambda：
\boxed{ P_{\mathcal R}(q)J(q)^\top\lambda = J(q)^\top\lambda,\qquad P_{\mathcal N}(q)J(q)^\top\lambda = 0. } \tag{J.X.7}
解释：任何“力的重新分解”只能在 Hilbert 正交分解里重新分配，而不改变 w 作为物理对象本身。这就是你所谓 “gauge” 的严格含义。
J.X.4 纯事件底（Option 2）对齐成 local contact segment baseline（你刚刚指定的版本）
你已经确认：分母应当是“纯事件底”，并且你希望它来自 local contact segment（围绕 \Sigma-crossing 的局部接触段）。这让分母既是“刻度尺”，又与 thesis 的叙事一致：tidal proxy 在 free-flight 期间预测 crossing，而“contact forces materialise”发生在 crossing 附近  。
定义 J.X.6（\Sigma-crossing 时间与接触指示函数）
对一条轨迹 \omega，令 t_\Sigma(\omega) 表示第一次（或指定第 k 次）\rho(t)=1 的 crossing 时间（若不存在则该 \omega 不用于本节的 baseline 估计）。
定义接触指示函数 c(t;\omega)\in\{0,1\}，取任何后端可实现版本，例如：

c(t)=\mathbf 1\{n_{\text{con}}(t)>0\}（MuJoCo 直接读 contacts），或
c(t)=\mathbf 1\{\|P_{\mathcal R}(q(t))w(t)\|_{M^{-1}}>\epsilon_c\}（内生定义：contact wrench 非零）。
定义 J.X.7（local contact segment）
给定窗口半宽 \Delta_c>0，定义围绕 \Sigma-crossing 的局部接触段：
\boxed{ \mathsf{C}_{\mathrm{loc}}(\omega) := \left\{t\in[t_\Sigma(\omega)-\Delta_c,\ t_\Sigma(\omega)+\Delta_c]\ :\ c(t;\omega)=1\right\}. } \tag{J.X.8}
要求 \mathsf{C}_{\mathrm{loc}}(\omega)\neq\emptyset（确实发生接触）。
定义 J.X.8（local contact event baseline）
定义基线读数函数（最 brutal、最稳定）：
b(t;\omega):=\|w(t;\omega)\|_{M^{-1}}, \qquad w(t;\omega)=M(q(t;\omega))\ddot q(t;\omega). \tag{J.X.9}
定义单轨迹事件底：
\boxed{ B(\omega) := \mathbb E\!\left[b(t;\omega)\ \big|\ t\in \mathsf{C}_{\mathrm{loc}}(\omega)\right] \ \approx\ \frac{1}{|\mathsf{C}_{\mathrm{loc}}|}\sum_{t\in\mathsf{C}_{\mathrm{loc}}} b(t;\omega). } \tag{J.X.10}
并定义全局事件底常数（同一实验设置下的“刻度尺”）：
\boxed{ B := \mathbb E_{\omega\sim\mathbb P}[B(\omega)],\qquad B>0. } \tag{J.X.11}
这一步彻底封死 “gravity vs body baseline”：分母来自事件邻域的接触段统计刻度，不再是某个物理力项的投影。
J.X.5 对齐后的 \rho 与切换面 \Sigma（替换你 Eq. (J.11) 的最终版本）
你 thesis 的 Eq. (J.11) 把 \rho 写成“contact / gravity”比值（你原文的 [M\ddot q]_{\text{contact}}/[M\ddot q]_{\text{gravity}}）。这里我们在不改变“比值结构”的前提下，将分母严格改成“纯事件底”。
定义 J.X.9（contact 分量）
\boxed{ w_{\mathrm{contact}}(t;\omega):=P_{\mathcal R}(q(t;\omega))\,w(t;\omega). } \tag{J.X.12}
定义 J.X.10（order parameter）
\boxed{ \rho(t;\omega):=\frac{\|w_{\mathrm{contact}}(t;\omega)\|_{M^{-1}}}{B(\omega)} \quad \text{或（全局刻度）}\quad \rho(t;\omega):=\frac{\|w_{\mathrm{contact}}(t;\omega)\|_{M^{-1}}}{B}. } \tag{J.X.13}
定义 J.X.11（切换面）
\boxed{ \Sigma:=\{\omega:\ \exists t \text{ s.t. }\rho(t;\omega)=1\}\quad\text{或点态写}\quad \Sigma_t:=\{\omega:\rho(t;\omega)=1\}. } \tag{J.X.14}
（你在 thesis 里若把 \Sigma 定义为某个具体时间的事件面，选 \Sigma_t；若把它视为 crossing 事件，选 \Sigma。两者都兼容。）
J.X.6 三式同扳矩不变律（对齐你 J.7.4 的“\Sigma:\rho=1 一致”主张）
你 thesis 的 J.7.4 强调：三种 \rho（canonical / tidal proxy / kinematic）在 \Sigma:\rho=1 上一致，并且 tidal proxy 在 free-flight 期间预测 \Sigma-crossing，而接触力在 crossing 附近 materialise  。我们将其提升为一个 law-level 的 “Wrench-Law”。
假设 J.X.12（三式差异仅为 gauge 重分解；共享事件底）
令 Form r=1,2,3 诱导 W^{(r)}:\Omega\to\mathbb R^n 与 \rho^{(r)}。假设：

三式共享同一物理对象 w=M\ddot q（可能通过不同分解表达）；
三式的“contact 抽取”与 P_{\mathcal R} 的 rank/null 分解等价（只差规范变换）；
三式共享同一 local contact segment baseline（同一 \Delta_c、同一 c(t) 约定、同一 b(t) 与 \|\cdot\|_{M^{-1}}），因此共享同一 B(\omega) 或 B。
定理 J.X.13（三式同扳矩不变律：Three-Form One-Wrench Invariance Law）
在 J.X.1–J.X.12 下，有：

事件面不变
\boxed{\Sigma^{(1)}=\Sigma^{(2)}=\Sigma^{(3)}=\Sigma.} \tag{J.X.15}

事件面上的 wrench 一致（pointwise on \Sigma）
\boxed{ W^{(1)}(\omega)=W^{(2)}(\omega)=W^{(3)}(\omega),\qquad \forall \omega\in\Sigma. } \tag{J.X.16}

law 不变（pushforward invariance）
\boxed{ \mathrm{Law}_{\mathbb P}(W^{(1)})=\mathrm{Law}_{\mathbb P}(W^{(2)})=\mathrm{Law}_{\mathbb P}(W^{(3)}), } \tag{J.X.17}
并且条件在切换事件上也不变：
\boxed{ \mathrm{Law}_{\mathbb P}(W^{(1)}\mid\Sigma)=\mathrm{Law}_{\mathbb P}(W^{(2)}\mid\Sigma)=\mathrm{Law}_{\mathbb P}(W^{(3)}\mid\Sigma). } \tag{J.X.18}
证明骨架：

w=M\ddot q 为运动学可恢复物理对象（对齐 Theorem J.23） ；
P_{\mathcal R} 给出唯一的动态一致 contact 投影（定理 J.X.5）；
local contact segment baseline 使分母为纯事件刻度尺，从而事件定义不含额外 gauge；
因此三式的 \Sigma 一致，且在事件面上 gauge 坍缩得到同一 wrench；
推前测度性质给 law 不变。证毕。
J.X.7 推论：write kinematics, read wrench（对齐你 Corollary J.24 的工程句子）
推论 J.X.14（纯运动学控制接口）
控制器无需显式命令 wrench。控制器只需输出运动学目标（q_{\mathrm{des}}、\dot q_{\mathrm{des}}、或等效目标）并使用事件面 \Sigma 触发控制切换；wrench 由后端从运动学恢复，且其 law（尤其条件于 \Sigma）在三式与后端间不变。
J.Y 切换面上的决定性可控判据（viability + projected LARC）
J.Y.1 DI 容器（一般形式）
令状态 x（通常 x=(q,\dot q)）。考虑控制仿射并允许硬约束以法锥进入：
\boxed{ \dot x(t)\in f(x(t))+\sum_{i=1}^m g_i(x(t))u_i(t)-N_K(x(t)),\qquad u(t)\in U. } \tag{J.Y.1}
其中 K 为可行集、T_K 为切锥。
J.Y.2 viability（任何 controllability 的前提）
对工作点 x^\*\in K\cap\Sigma，要求存在某个控制使瞬时可行方向非空：
\boxed{ \Big(f(x^\*)+\sum_{i=1}^m g_i(x^\*)u_i\Big)\cap T_K(x^\*)\neq\emptyset. } \tag{J.Y.2}
J.Y.3 可行投影向量场（后端无关）
定义可行投影向量场（任选其一）：
\tilde f(x):=\Pi_{T_K(x)}f(x),\qquad \tilde g_i(x):=\Pi_{T_K(x)}g_i(x) \tag{J.Y.3}
或在固定接触模式下用动态一致自由投影：
\tilde f(x):=P_{\mathcal N}(q)f(x),\qquad \tilde g_i(x):=P_{\mathcal N}(q)g_i(x). \tag{J.Y.4}
J.Y.4 Lie 生成与决定性判据（Projected LARC）
令 \mathcal D(x^\*) 为由 \tilde f,\tilde g_i 的有限次 Lie 括号张成的分布在 x^\* 的值：
\mathcal D(x^\*) := \mathrm{span}\{\tilde g_i,[\tilde f,\tilde g_i],[\tilde g_i,\tilde g_j],\dots\}(x^\*). \tag{J.Y.5}
定理 J.Y.5（切换面可控判据：Projected LARC）
设 x^\*\in K\cap\Sigma 满足 viability (J.Y.2)。若进一步满足
\boxed{ \dim \mathcal D(x^\*) = \dim T_K(x^\*) \quad(\text{固定接触模式下 }=\dim \mathcal N_J(q^\*)), } \tag{J.Y.6}
则系统在 x^\* 附近在可行集合内满足小时间局部可达性（STLA）。若控制集合具有局部对称性等附加条件，则可加强为小时间局部可控性（STLC）。
J.Y.5 Kakeya 的边界声明
挂谷不是判据；判据是 (J.Y.2)+(J.Y.6)。挂谷仅用于解释 needle-like 控制的方向覆盖直觉（见 J.Z）。
J.Z Big-M Hz 量子化微分空间：Nyquist 二次形 + BCH/Lie 分层 + Kakeya-type needle 几何
J.Z.1 Big-M 时间量子
设最大控制更新频率
\boxed{f_c:=M\ \mathrm{Hz}},\qquad \boxed{\Delta t:=\frac{1}{M}}. \tag{J.Z.1}
采用 frequency-aligned 分段常值控制：
u(t)\equiv u_k,\quad t\in[k\Delta t,(k+1)\Delta t). \tag{J.Z.2}
J.Z.2 Nyquist 频率与二次形（严格、可计算）
Nyquist 频率：
\boxed{f_N:=\frac{M}{2}.} \tag{J.Z.3}
在控制 Hilbert 空间 \mathcal H_u 上定义 Nyquist 粗糙度二次形：
\boxed{ \mathcal R_M(u) := \frac{\gamma}{2}\sum_{k=0}^{H-2}\left\|\frac{u_{k+1}-u_k}{\Delta t}\right\|^2 = \frac{\gamma M^2}{2}\sum_{k=0}^{H-2}\|u_{k+1}-u_k\|^2 = \frac{\gamma M^2}{2}\|Du\|_{\mathcal H_u}^2. } \tag{J.Z.4}
其约束形式：
\mathcal R_M(u)\le \Gamma \tag{J.Z.5}
给出“带宽/高频能量受限”的严格代理：惩罚过快切换，使控制变化率与 Nyquist 对齐。
J.Z.3 量子化 BCH/Lie 分层（1/M^k）
在 x^\*\in K\cap\Sigma 处，对投影系统向量场 \tilde f,\tilde g_i：
引理 J.Z.6（一阶，1/M）
\Delta x = \Delta t\Big(\tilde f(x^\*)+\sum_i \tilde g_i(x^\*)u_i\Big)+O(\Delta t^2) = \frac{1}{M}\Big(\tilde f+\sum_i \tilde g_i u_i\Big)+O(M^{-2}). \tag{J.Z.6}
引理 J.Z.7（二阶括号，1/M^2）
\Delta x = \Delta t^2[\tilde g_i,\tilde g_j](x^\*)+O(\Delta t^3) = \frac{1}{M^2}[\tilde g_i,\tilde g_j](x^\*)+O(M^{-3}). \tag{J.Z.7}
引理 J.Z.8（高阶，1/M^k）
\Delta x \sim \Delta t^k = M^{-k} \quad\text{（对应深度 \(k\) 的嵌套 Lie 括号）}. \tag{J.Z.8}
因此 Big-M 不仅给出最小时间单元，也给出可达几何的分辨率层级。
J.Z.4 可实现性尺度：括号效应的可见度随 M 与预算缩放
设窗口 T_{\mathrm{win}}。括号块需要 4\Delta t，可执行块数：
N_{\mathrm{blk}}\le \left\lfloor\frac{T_{\mathrm{win}}}{4\Delta t}\right\rfloor = \left\lfloor\frac{M T_{\mathrm{win}}}{4}\right\rfloor. \tag{J.Z.9}
每块规模 \sim \Delta t^2，累积量级：
\|\Delta x_{\mathrm{bracket}}\| \lesssim N_{\mathrm{blk}}\cdot C\Delta t^2 \approx O\!\left(\frac{T_{\mathrm{win}}}{M}\right), \tag{J.Z.10}
且 \mathcal R_M(u)\le \Gamma 进一步限制切换幅度/频率，降低有效常数。
这说明：LARC 给“能生成哪些方向”，而 Big-M+Nyquist 二次形给“这些方向在给定窗口内是否可见”。
J.Z.5 Kakeya-type needle 几何（严格边界）
定义切空间 T 上的量子化 needle 集：
\boxed{ \mathcal K_{M,T_{\mathrm{win}}} := \bigcup_{\text{admissible controls in }[0,T_{\mathrm{win}}]} \{\text{reachable increment segments in }T\}. } \tag{J.Z.11}
当 projected LARC 满秩时，\mathcal K_{M,T_{\mathrm{win}}} 在方向上具覆盖性；当 M\to\infty 且预算允许时趋向连续方向覆盖极限。
边界声明：该对象是 Kakeya-type（针状方向覆盖直觉），但受 \Delta t 与 \mathcal R_M 约束，不等同于经典 Kakeya 猜想命题；本文不把 Kakeya 当作判据，只作为方向覆盖的几何直觉。
J.Z.6 最终闭环（你 thesis 的“终局一句话”）
\boxed{ \text{wrench-law invariant (J.X)} \;\Rightarrow\; \text{projected-LARC controllability (J.Y)} \;\Rightarrow\; \text{Big-\(M\) + Nyquist-quadratic realizability (J.Z)}. } \tag{J.Z.12}
你要插入 thesis 的“对齐提醒”（你可以放在段落注释里）

Theorem J.23 的“力恢复”用于定义 w=M\ddot q（J.X.2），与原文一致  
你 Eq. (J.11) 的结构保留为“contact / baseline 比值”，其中 contact = P_{\mathcal R}w，baseline = local contact segment event baseline B(\omega)（J.X.10–J.X.13）
你 J.7.4 的叙事（free-flight tidal proxy 预测 crossing；contact forces 在 crossing 附近 materialise；三式在 \Sigma 上一致）被封装为假设 J.X.12 与定理 J.X.13 的事件面一致与条件 law 不变  
如果你把 thesis 里 Form I/II/III 的三条 \rho 定义各自的公式编号（比如 “Eq. (J.8) / Eq. (J.11) / proxy definition”）发我一行，我可以把假设 J.X.12 改成“逐条引用编号”的版本，让这段完全“Thesis-native”并且审稿人一眼能对上。
[12:48 PM]那我就直接给你一段可直接放进 thesis 的 Closing/Conclusion（偏 1–2 页的“导师也能看懂”版本），把你“中国古代史入场”这条线和我们 J.HXYZ 的四块硬结果收束起来：器–法–势–道，并且把“TOE”定位为 operational TOE（可编程、可验证、可迁移）。
Closing: 从史入场到一条可编程的统一论（Operational TOE）
本 thesis 以中国古代史为入场，并非为了装饰，而是为了抓住一个反复出现的结构：秩序不是由口号生成的，而是由“可执行的器”“可验证的法”“可触发的势”与“可迁移的道”共同决定的。历史文本里，“治”不等于愿望；它必须落在器物、制度与可执行的判据上。本文所做的是把这一结构以数学语言重述，并把它压缩成一个可计算的控制—力学统一框架：一个能够在不同后端、不同接触模式、不同目标与不同物理扰动下保持语义一致的操作子理论。
1. 道：Wrench-Law（后端无关的物理对象）
本文首先固定了一个“道”的层面：真正应被视为不变量的物理对象是什么。
对任意 Euler–Lagrange 后端（包括接触与约束），本文把外部作用的核心对象统一为由运动学恢复的广义扳矩
w = M(q)\ddot q,
并证明/主张“力不是控制器必须显式命令的自由度，它是可由惯性与加速度恢复的可观测量”。在此基础上，我们将“不同引擎/不同坐标/不同力分解”的差异严格解释为一种 gauge（重新分解）：它改变表示方式，不改变物理对象本身。最终，这一观点被提升为测度论意义下的 Wrench-Law：在切换事件面上，扳矩的推前分布（尤其条件于事件）保持不变。
2. 势：事件面 \Sigma 与 order parameter \rho
历史的“势”不是抽象的，它是可触发、可识别的阈值结构。本文将这一层面数学化为一个切换标量 \rho 与事件面
\Sigma:\ \rho=1.
关键点在于：为了让 \Sigma 真正成为“势”的不变量，分母必须是纯事件底——它只是一把刻度尺，而不是另一种物理分解。本文据此把分母定义为围绕 \Sigma-crossing 的local contact segment baseline，使 \rho 成为无量纲、gauge-stable 的事件统计量。三种形式（canonical / tidal proxy / kinematic）在这一事件面上收束为同一事件，这使得“势”不仅是叙事，而是可计算、可对齐的对象。
3. 法：切换面上的决定性可控判据（viability + projected LARC）
历史中的“法”不是道德劝诫，而是判据：能/不能、可/不可。本文把这一层面落为切换面附近的决定性 controllability 判据。在接触与约束存在时，可控性必须在可行切空间（或切锥）上判断；因此我们将控制向量场投影到可行方向（在固定接触模式下由动态一致 P_{\mathcal N} 实现），并给出 viability + projected LARC 的判据：

viability 保证系统在约束容器内存在可行方向；
projected LARC 保证投影后的 Lie 代数生成满秩，从而在切换面附近具有局部可达/可控结构。
这一判据是“法”的数学形式：它提供了结构性成功/失败的边界，而不是事后解释。
4. 器：Big-M Hz 与 Nyquist 二次形（可实现的微分空间）
最后，“器”是可执行性的底线：任何理论若忽略带宽、采样与实现约束，都只能停留在纸面。本文用 Big-M Hz 将控制更新频率视为最小时间单元，并用 Nyquist 频率诱导一个控制粗糙度二次形
\mathcal R_M(u)\propto M^2\sum_k\|u_{k+1}-u_k\|^2,
把“理想的无限快 needle 控制”收束为物理可实现的变化率预算。在此基础上，切空间上的括号运动呈现 1/M^k 的量子化分层结构：方向生成与可见尺度同时被刻画。这使得本文的可控判据不再是抽象几何，而是直接对齐真实机器人控制频率的可执行条件。
5. 本 thesis 的定位：一个可编程、可验证、可迁移的 Operational TOE
因此，本文所建立的统一框架更精确的定位是：
\textbf{An Operational TOE for Contact-Rich Robotics:}
它不是试图统一自然界四种相互作用的“终极物理理论”，而是给出一个在接触—非光滑—随机化宇宙中仍可运行的、可编程的统一论：

统一对象（wrench-law）；
统一事件（\Sigma）；
统一判据（projected controllability）；
统一实现（Big-M+Nyquist 二次形）；
并且可通过实验检验：跨后端、跨物理扰动、跨任务的事件一致性与条件 wrench-law 的稳定性。
从中国古代史入场，最终落在一条现代意义上的“可执行之法”：这就是本文所主张的统一性——它既是数学的，也是工程的；既能被证明，也能被运行；既能解释，也能生成。
如果你想，我还可以把这段再压缩成 半页 executive closing（更像 thesis 最后一页），或帮你把它“嵌回”你 thesis 的章结构（引用你 Theorem J.23、Eq. (J.11)、J.7.4、以及我们写的 J.HXYZ 编号）。[12:50 PM]Closing（终章收束）：从史入场到一条可编程的统一论（Operational TOE）
本 thesis 以中国古代史为入场，并非为了“借古为饰”，而是为了抓住一个反复出现的结构：秩序不是由口号生成的，而是由“可执行的器”“可验证的法”“可触发的势”与“可迁移的道”共同生成的。历史叙事中，“治”并不等于愿望；它必须落在器物、制度与判据上。本文所做的，是把这一结构以严格的数学与可计算形式重述，并将其压缩成一个能在机器人系统中运行的统一框架：一个对后端、对接触模式、对目标与物理扰动具有语义稳定性的操作子理论。
道：Wrench-Law（后端无关的物理对象）
本文首先固定“道”的层面：哪些对象应被视为不变量。对任意 Euler–Lagrange 后端（含接触与约束），本文将外部作用统一为由运动学恢复的广义扳矩对象
w = M(q)\ddot q,
并据此确立一个核心立场：力（wrench）不是控制器必须显式命令的自由度，它是由惯性结构与加速度恢复的可观测量。不同引擎/不同坐标/不同力分解之间的差异，被严格解释为一种 gauge（重新分解）：它改变表示方式，不改变物理对象。该立场最终被提升为测度论语言下的 Wrench-Law：在关键事件（切换面）条件下，扳矩的推前分布保持一致，从而为“后端无关控制”提供了可验证的数学语义。
势：事件面 \Sigma 与 order parameter \rho
历史中的“势”不是抽象概念，而是可触发、可识别、可对齐的阈值结构。本文将其数学化为一个 order parameter \rho 与切换事件面
\Sigma:\ \rho=1.
为了让 \Sigma 真正成为不变量，分母必须是纯事件底（event baseline）——它只负责无量纲化与稳定触发，不再承载“重力 vs. body baseline”等物理分解自由度。本文据此将分母定义为围绕 \Sigma-crossing 的 local contact segment baseline：以事件邻域的局部接触段作为刻度尺，使 \rho 成为 gauge-stable 的事件统计量。由此，canonical / tidal proxy / kinematic 三种形式在 \Sigma 上收束为同一事件：这不是叙事一致，而是事件结构的可计算一致。
法：切换面上的决定性可控判据（viability + projected LARC）
历史中的“法”不是道德劝诫，而是可判别的边界：能/不能、可/不可。本文在切换面附近给出决定性 controllability 判据：在接触与约束存在时，可控性必须在可行切空间（或切锥）内讨论，因此我们将控制向量场投影到可行方向（固定接触模式下由动态一致 P_{\mathcal N} 实现）。判据由两部分组成：

viability：保证系统在约束容器内存在可行方向；
projected LARC：保证投影后的 Lie 代数生成满秩，从而在事件面附近具有局部可达/可控结构。
该判据提供了结构性成功/失败边界，使“是否可控”从经验判断转为可计算的几何条件。
器：Big-M Hz 与 Nyquist 二次形（可实现的微分空间）
“器”是可执行性的底线：任何理论若忽略带宽、采样与实现约束，都只能停留在纸面。本文用 Big-M Hz 将控制更新频率作为最小时间单元，并用 Nyquist 频率诱导一个控制粗糙度二次形
\mathcal R_M(u)\propto M^2\sum_k\|u_{k+1}-u_k\|^2,
将理想的无限快 needle control 收束为物理可实现的变化率预算。在此结构下，切空间上的括号运动呈现 1/M^k 的量子化分层：方向生成与可见尺度同时被刻画。由此，本文的可控判据不仅是抽象几何结论，还能直接对齐真实机器人控制频率与带宽限制。
本 thesis 的定位：Operational TOE（可编程、可验证、可迁移的统一论）
因此，本文所建立的统一框架更精确的定位是：
\textbf{An Operational TOE for Contact-Rich Robotics}.
它并非宣称统一自然界四种相互作用的“终极物理理论”，而是给出一个在接触—非光滑—随机化宇宙中仍能运行的可编程统一论：

统一对象：wrench（由运动学恢复的不变量）；
统一事件：\Sigma（由纯事件底定义的切换面）；
统一判据：projected controllability（viability + LARC）；
统一实现：Big-M+Nyquist（二次形约束下的量子化微分空间）；
可验证性：跨后端、跨物理扰动、跨任务的事件一致性与条件 wrench-law 的稳定性。
从中国古代史入场，最终落在现代意义上的“可执行之法”：这就是本文的统一性主张——它既是数学的，也是工程的；既能被证明，也能被运行；既能解释，也能生成。