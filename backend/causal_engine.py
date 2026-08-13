"""
因果推理引擎 (Causal Inference Engine)
=====================================
AI + Education + Causal Inference

核心能力：
1. 因果知识图谱 - 知识点间的因果关系建模
2. 根因分析 - 从错误模式追溯根本原因
3. 反事实推理 - "如果掌握了知识点A，成绩会怎样？"
4. 精准干预推荐 - 基于因果链的最优学习路径

学术基础：
- Pearl's Causal Hierarchy: Association → Intervention → Counterfactual
- DoWhy framework: Identify → Estimate → Refute
- Knowledge Tracing + Causal Discovery
"""

import random
import math
import time
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json


# ============================================================
# 数据模型
# ============================================================

@dataclass
class KnowledgeNode:
    """知识图谱节点"""
    node_id: str
    name: str
    category: str          # 基础/核心/进阶
    difficulty: float      # 难度系数 0-1
    mastery: float = 0.5   # 学生掌握度 0-1
    description: str = ""


@dataclass
class CausalEdge:
    """因果边（有向）"""
    source: str            # 原因知识点
    target: str            # 结果知识点
    causal_strength: float # 因果效应强度 0-1
    edge_type: str         # direct/indirect/mediated
    description: str = ""


@dataclass
class StudentState:
    """学生认知状态"""
    student_id: str
    knowledge_mastery: Dict[str, float] = field(default_factory=dict)  # node_id -> mastery
    error_history: List[Dict] = field(default_factory=list)            # 错误记录
    learning_timeline: List[Dict] = field(default_factory=list)        # 学习时间线


@dataclass
class RootCauseResult:
    """根因分析结果"""
    surface_errors: List[Dict]       # 表面错误
    root_causes: List[Dict]          # 根本原因
    causal_chains: List[Dict]        # 因果链路
    confidence: float                # 置信度
    intervention_priority: List[Dict]  # 干预优先级


@dataclass
class CounterfactualResult:
    """反事实推理结果"""
    scenario: str                    # 假设场景
    target_node: str                 # 干预目标
    intervention_value: float        # 干预值
    predicted_outcomes: Dict[str, float]  # 预测结果
    expected_improvement: Dict[str, float]  # 预期提升
    confidence: float
    reasoning: str                   # 推理过程


# ============================================================
# 因果知识图谱
# ============================================================

class CausalKnowledgeGraph:
    """
    因果知识图谱
    - 节点：知识点
    - 边：因果关系（有向，带强度）
    - 支持路径查找、因果效应传播、反事实推理
    """

    def __init__(self, subject: str = "math"):
        self.subject = subject
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, CausalEdge] = {}  # "source->target" -> edge
        self.adjacency: Dict[str, List[str]] = defaultdict(list)  # 邻接表（正向）
        self.reverse_adj: Dict[str, List[str]] = defaultdict(list)  # 邻接表（反向）

        self._build_graph()

    def _build_graph(self):
        """构建学科因果知识图谱"""
        if self.subject == "math":
            self._build_math_graph()
        elif self.subject == "chinese":
            self._build_chinese_graph()
        elif self.subject == "programming":
            self._build_programming_graph()
        else:
            self._build_math_graph()

    def _build_math_graph(self):
        """数学知识图谱（含因果结构）"""
        # 知识点定义（按学习顺序）
        nodes_def = [
            # 基础层
            ("k_arithmetic", "四则运算", "基础", 0.2, "加减乘除基本运算"),
            ("k_fraction", "分数与小数", "基础", 0.3, "分数概念与运算"),
            ("k_negative", "负数概念", "基础", 0.25, "正负数理解与运算"),
            ("k_exponent", "指数与幂", "基础", 0.35, "指数运算规则"),
            # 核心层
            ("k_algebra_basic", "代数基础", "核心", 0.4, "字母表示数、代数式"),
            ("k_equation_linear", "一元一次方程", "核心", 0.45, "线性方程求解"),
            ("k_equation_quadratic", "一元二次方程", "核心", 0.6, "二次方程求解"),
            ("k_inequality", "不等式", "核心", 0.5, "不等式性质与求解"),
            ("k_function_concept", "函数概念", "核心", 0.55, "函数定义与表示"),
            ("k_function_linear", "一次函数", "核心", 0.5, "线性函数图像与性质"),
            ("k_function_quadratic", "二次函数", "核心", 0.65, "抛物线图像与性质"),
            # 进阶层
            ("k_geometry_basic", "几何基础", "进阶", 0.4, "点线面基本概念"),
            ("k_triangle", "三角形", "进阶", 0.5, "三角形性质与全等"),
            ("k_coordinate", "坐标系", "进阶", 0.45, "平面直角坐标系"),
            ("k_statistics", "统计与概率", "进阶", 0.5, "数据描述与概率计算"),
            ("k_derivative", "导数初步", "进阶", 0.75, "变化率与导数"),
        ]

        for nid, name, cat, diff, desc in nodes_def:
            self.nodes[nid] = KnowledgeNode(nid, name, cat, diff, description=desc)

        # 因果边定义（source -> target, strength, type, description）
        # 这些边表示"掌握source是学习target的因果前提"
        edges_def = [
            ("k_arithmetic", "k_fraction", 0.85, "direct", "四则运算是分数运算的基础"),
            ("k_arithmetic", "k_negative", 0.80, "direct", "四则运算扩展到负数"),
            ("k_arithmetic", "k_exponent", 0.75, "direct", "乘法运算引出指数概念"),
            ("k_fraction", "k_algebra_basic", 0.70, "direct", "分数运算迁移到代数式"),
            ("k_negative", "k_algebra_basic", 0.65, "direct", "负数概念是代数运算前提"),
            ("k_exponent", "k_algebra_basic", 0.55, "direct", "指数是代数式的一部分"),
            ("k_algebra_basic", "k_equation_linear", 0.80, "direct", "代数基础直接支撑方程学习"),
            ("k_equation_linear", "k_equation_quadratic", 0.75, "direct", "一次方程是二次方程的基础"),
            ("k_algebra_basic", "k_inequality", 0.65, "direct", "代数基础支撑不等式"),
            ("k_equation_linear", "k_function_concept", 0.60, "direct", "方程概念过渡到函数"),
            ("k_function_concept", "k_function_linear", 0.80, "direct", "函数概念直接支撑一次函数"),
            ("k_function_linear", "k_function_quadratic", 0.70, "direct", "一次函数过渡到二次函数"),
            ("k_equation_quadratic", "k_function_quadratic", 0.55, "direct", "二次方程与二次函数关联"),
            ("k_arithmetic", "k_geometry_basic", 0.40, "indirect", "运算能力辅助几何计算"),
            ("k_geometry_basic", "k_triangle", 0.80, "direct", "几何基础直接支撑三角形"),
            ("k_coordinate", "k_function_linear", 0.65, "direct", "坐标系是函数图像的基础"),
            ("k_geometry_basic", "k_coordinate", 0.55, "direct", "几何概念过渡到坐标系"),
            ("k_function_quadratic", "k_derivative", 0.60, "direct", "二次函数变化率引出导数"),
            ("k_statistics", "k_derivative", 0.25, "indirect", "统计思维辅助理解变化趋势"),
            ("k_inequality", "k_function_quadratic", 0.35, "indirect", "不等式与函数值域关联"),
            # 汇聚边：使部分节点对同时存在直接和间接因果路径
            ("k_arithmetic", "k_algebra_basic", 0.50, "direct", "算术运算直接迁移到代数思维"),
            ("k_algebra_basic", "k_function_quadratic", 0.30, "direct", "代数思维直接辅助二次函数理解"),
            ("k_equation_linear", "k_function_linear", 0.45, "direct", "一元一次方程与一次函数互为表里"),
        ]

        for src, tgt, strength, etype, desc in edges_def:
            edge_key = f"{src}->{tgt}"
            self.edges[edge_key] = CausalEdge(src, tgt, strength, etype, desc)
            self.adjacency[src].append(tgt)
            self.reverse_adj[tgt].append(src)

    def _build_chinese_graph(self):
        """语文知识图谱"""
        nodes_def = [
            ("k_pinyin", "拼音基础", "基础", 0.15, "声韵母与拼读"),
            ("k_character", "汉字识写", "基础", 0.2, "汉字结构与书写"),
            ("k_word", "词语理解", "基础", 0.3, "词义与用法"),
            ("k_sentence", "句子构造", "核心", 0.4, "句型与修辞"),
            ("k_reading", "阅读理解", "核心", 0.55, "文本分析与理解"),
            ("k_logic", "逻辑思维", "核心", 0.5, "因果与论证"),
            ("k_structure", "篇章结构", "进阶", 0.6, "文章组织与布局"),
            ("k_theme", "立意构思", "进阶", 0.7, "主题提炼与深化"),
            ("k_expression", "语言表达", "进阶", 0.65, "修辞与文采"),
            ("k_argument", "论证方法", "进阶", 0.7, "论点论据论证"),
        ]
        for nid, name, cat, diff, desc in nodes_def:
            self.nodes[nid] = KnowledgeNode(nid, name, cat, diff, description=desc)

        edges_def = [
            ("k_pinyin", "k_character", 0.70, "direct", "拼音辅助识字"),
            ("k_character", "k_word", 0.80, "direct", "识字是词语理解前提"),
            ("k_word", "k_sentence", 0.75, "direct", "词语组合成句子"),
            ("k_sentence", "k_reading", 0.70, "direct", "句子理解支撑阅读"),
            ("k_sentence", "k_logic", 0.60, "direct", "句型训练逻辑思维"),
            ("k_reading", "k_structure", 0.65, "direct", "阅读积累篇章结构认知"),
            ("k_logic", "k_structure", 0.55, "direct", "逻辑支撑文章组织"),
            ("k_structure", "k_theme", 0.70, "direct", "篇章结构服务立意"),
            ("k_logic", "k_argument", 0.75, "direct", "逻辑直接支撑论证"),
            ("k_theme", "k_expression", 0.60, "direct", "立意决定表达方向"),
            ("k_reading", "k_theme", 0.50, "indirect", "阅读启发立意"),
            ("k_word", "k_expression", 0.45, "indirect", "词语积累支撑表达"),
        ]
        for src, tgt, strength, etype, desc in edges_def:
            edge_key = f"{src}->{tgt}"
            self.edges[edge_key] = CausalEdge(src, tgt, strength, etype, desc)
            self.adjacency[src].append(tgt)
            self.reverse_adj[tgt].append(src)

    def _build_programming_graph(self):
        """编程知识图谱"""
        nodes_def = [
            ("k_variable", "变量与类型", "基础", 0.2, "数据类型与变量"),
            ("k_operator", "运算符", "基础", 0.25, "算术逻辑运算"),
            ("k_control", "流程控制", "核心", 0.4, "if-else与循环"),
            ("k_function", "函数定义", "核心", 0.5, "函数封装与调用"),
            ("k_array", "数组与列表", "核心", 0.45, "数据结构基础"),
            ("k_recursion", "递归", "进阶", 0.65, "递归思想"),
            ("k_oop", "面向对象", "进阶", 0.7, "类与对象"),
            ("k_algorithm", "算法基础", "进阶", 0.75, "排序与查找"),
            ("k_debug", "调试能力", "进阶", 0.55, "错误定位与修复"),
            ("k_design", "程序设计", "进阶", 0.80, "系统设计思维"),
        ]
        for nid, name, cat, diff, desc in nodes_def:
            self.nodes[nid] = KnowledgeNode(nid, name, cat, diff, description=desc)

        edges_def = [
            ("k_variable", "k_operator", 0.75, "direct", "变量是运算的基础"),
            ("k_operator", "k_control", 0.70, "direct", "运算支撑条件判断"),
            ("k_control", "k_function", 0.65, "direct", "流程控制封装为函数"),
            ("k_variable", "k_array", 0.60, "direct", "变量扩展为集合"),
            ("k_function", "k_recursion", 0.80, "direct", "函数调用引出递归"),
            ("k_array", "k_algorithm", 0.70, "direct", "数组操作支撑算法"),
            ("k_function", "k_oop", 0.60, "direct", "函数封装演进到类"),
            ("k_recursion", "k_algorithm", 0.55, "direct", "递归是重要算法思想"),
            ("k_control", "k_debug", 0.50, "direct", "流程理解辅助调试"),
            ("k_oop", "k_design", 0.65, "direct", "面向对象支撑系统设计"),
            ("k_algorithm", "k_design", 0.55, "direct", "算法能力支撑设计"),
            ("k_function", "k_debug", 0.40, "indirect", "函数隔离简化调试"),
        ]
        for src, tgt, strength, etype, desc in edges_def:
            edge_key = f"{src}->{tgt}"
            self.edges[edge_key] = CausalEdge(src, tgt, strength, etype, desc)
            self.adjacency[src].append(tgt)
            self.reverse_adj[tgt].append(src)

    # ============================================================
    # 图谱操作
    # ============================================================

    def get_all_causes(self, node_id: str) -> List[Tuple[str, float, List[str]]]:
        """
        获取一个知识点的所有因果祖先（递归向上追溯）
        返回: [(ancestor_id, total_causal_effect, path), ...]
        """
        results = []
        visited = set()

        def _trace(current: str, accumulated_effect: float, path: List[str]):
            parents = self.reverse_adj.get(current, [])
            for parent in parents:
                if parent in visited:
                    continue
                visited.add(parent)
                edge = self.edges.get(f"{parent}->{current}")
                if edge:
                    new_effect = accumulated_effect * edge.causal_strength
                    new_path = [parent] + path
                    results.append((parent, new_effect, new_path))
                    _trace(parent, new_effect, new_path)

        _trace(node_id, 1.0, [node_id])
        # 按因果效应排序
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def get_all_effects(self, node_id: str) -> List[Tuple[str, float, List[str]]]:
        """
        获取一个知识点的所有因果后代（递归向下传播）
        返回: [(descendant_id, total_causal_effect, path), ...]
        """
        results = []
        visited = set()

        def _trace(current: str, accumulated_effect: float, path: List[str]):
            children = self.adjacency.get(current, [])
            for child in children:
                if child in visited:
                    continue
                visited.add(child)
                edge = self.edges.get(f"{current}->{child}")
                if edge:
                    new_effect = accumulated_effect * edge.causal_strength
                    new_path = path + [child]
                    results.append((child, new_effect, new_path))
                    _trace(child, new_effect, new_path)

        _trace(node_id, 1.0, [node_id])
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def find_causal_paths(self, source: str, target: str) -> List[Dict]:
        """找到从source到target的所有因果路径"""
        paths = []
        visited = set()

        def _dfs(current: str, path: List[str], effects: List[float]):
            if current == target and len(path) > 1:
                avg_effect = sum(effects) / len(effects) if effects else 0
                paths.append({
                    "path": path,
                    "path_names": [self.nodes[nid].name for nid in path],
                    "avg_causal_strength": round(avg_effect, 4),
                    "path_length": len(path) - 1,
                })
                return
            for child in self.adjacency.get(current, []):
                if child not in visited:
                    visited.add(child)
                    edge = self.edges.get(f"{current}->{child}")
                    if edge:
                        _dfs(child, path + [child], effects + [edge.causal_strength])
                    visited.discard(child)

        visited.add(source)
        _dfs(source, [source], [])
        paths.sort(key=lambda x: x["avg_causal_strength"], reverse=True)
        return paths

    def get_graph_data(self) -> Dict:
        """获取图谱可视化数据"""
        nodes = []
        categories = {"基础": 0, "核心": 1, "进阶": 2, "高阶": 3, "应用": 2}
        for nid, node in self.nodes.items():
            nodes.append({
                "id": nid,
                "name": node.name,
                "category": categories.get(node.category, 0),
                "category_name": node.category,
                "difficulty": node.difficulty,
                "symbolSize": 20 + node.difficulty * 30,
                "description": node.description,
            })

        links = []
        for edge_key, edge in self.edges.items():
            links.append({
                "source": edge.source,
                "target": edge.target,
                "value": edge.causal_strength,
                "type": edge.edge_type,
                "description": edge.description,
            })

        return {
            "nodes": nodes,
            "links": links,
            "categories": ["基础", "核心", "进阶"],
        }


# ============================================================
# 因果推理引擎
# ============================================================

class CausalInferenceEngine:
    """
    因果推理引擎
    - 根因分析：从错误模式追溯根本原因
    - 反事实推理：do-calculus
    - 干预推荐：基于因果链的最优学习路径
    - 因果效应估计：量化干预效果
    """

    def __init__(self):
        self.graphs: Dict[str, CausalKnowledgeGraph] = {}
        self.student_states: Dict[str, StudentState] = {}
        self.diagnosis_history: List[Dict] = []

        # 初始化各学科图谱
        for subject in ["math", "chinese", "programming"]:
            self.graphs[subject] = CausalKnowledgeGraph(subject)

    def get_graph(self, subject: str = "math") -> CausalKnowledgeGraph:
        return self.graphs.get(subject, self.graphs["math"])

    # ============================================================
    # 根因分析 (Root Cause Analysis)
    # ============================================================

    def diagnose_root_cause(
        self,
        student_id: str,
        error_nodes: List[str],
        subject: str = "math",
        current_mastery: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        根因分析：从学生表面错误追溯根本原因

        算法流程：
        1. 收集学生表现不佳的知识点（表面错误）
        2. 对每个错误节点，向上追溯因果祖先
        3. 计算每个祖先节点的"根因概率"：
           P(root_cause) = Σ (causal_effect × error_severity)
        4. 聚合多个错误节点的共同祖先（出现次数多 = 更可能是根因）
        5. 生成因果链路和干预优先级
        """
        graph = self.get_graph(subject)

        # 初始化学生状态（生成差异化掌握度）
        student_mastery = self.get_student_mastery(student_id, graph)
        if current_mastery:
            student_mastery.update(current_mastery)
        for nid, m in student_mastery.items():
            if nid in graph.nodes:
                graph.nodes[nid].mastery = m

        # Step 1: 记录表面错误
        surface_errors = []
        for nid in error_nodes:
            if nid in graph.nodes:
                mastery = graph.nodes[nid].mastery
                severity = 1.0 - mastery  # 掌握度越低，错误越严重
                surface_errors.append({
                    "node_id": nid,
                    "node_name": graph.nodes[nid].name,
                    "mastery": round(mastery, 3),
                    "error_severity": round(severity, 3),
                    "category": graph.nodes[nid].category,
                })

        # Step 2: 因果祖先追溯 + 根因概率计算
        cause_scores: Dict[str, float] = defaultdict(float)
        cause_paths: Dict[str, List[List[str]]] = defaultdict(list)
        cause_appearances: Dict[str, int] = defaultdict(int)

        for error in surface_errors:
            nid = error["node_id"]
            severity = error["error_severity"]
            ancestors = graph.get_all_causes(nid)

            for ancestor_id, effect, path in ancestors:
                # 根因概率 = 因果效应 × 错误严重度
                cause_scores[ancestor_id] += effect * severity
                cause_paths[ancestor_id].append(path)
                cause_appearances[ancestor_id] += 1

        # Step 3: 聚合排序，生成根因列表
        root_causes = []
        for cause_id, score in sorted(cause_scores.items(), key=lambda x: x[1], reverse=True):
            appearances = cause_appearances[cause_id]
            # 多个错误指向同一根因 → 置信度更高
            multi_error_boost = 1.0 + 0.15 * (appearances - 1)
            final_score = min(score * multi_error_boost, 1.0)

            # 获取该根因影响的所有下游知识点
            downstream_effects = graph.get_all_effects(cause_id)
            affected_nodes = [
                {
                    "node_id": eff_id,
                    "node_name": graph.nodes[eff_id].name,
                    "impact": round(eff, 3),
                }
                for eff_id, eff, _ in downstream_effects[:5]
            ]

            root_causes.append({
                "node_id": cause_id,
                "node_name": graph.nodes[cause_id].name,
                "root_cause_probability": round(final_score, 4),
                "appearances": appearances,
                "current_mastery": round(graph.nodes[cause_id].mastery, 3),
                "category": graph.nodes[cause_id].category,
                "description": graph.nodes[cause_id].description,
                "affected_downstream": affected_nodes,
                "causal_paths": [
                    {
                        "path": [graph.nodes[nid].name for nid in p],
                        "path_ids": p,
                    }
                    for p in cause_paths[cause_id][:3]  # 最多展示3条路径
                ],
            })

        # Step 4: 生成因果链路（可视化用）
        causal_chains = []
        for error in surface_errors[:3]:
            ancestors = graph.get_all_causes(error["node_id"])
            for anc_id, effect, path in ancestors[:3]:
                causal_chains.append({
                    "chain": [graph.nodes[nid].name for nid in path],
                    "chain_ids": path,
                    "causal_effect": round(effect, 4),
                    "error_node": error["node_name"],
                })

        # Step 5: 干预优先级
        interventions = []
        for rc in root_causes[:5]:
            # 计算干预该根因的预期效果
            downstream = graph.get_all_effects(rc["node_id"])
            total_impact = sum(eff for _, eff, _ in downstream)
            interventions.append({
                "node_id": rc["node_id"],
                "node_name": rc["node_name"],
                "priority": len(interventions) + 1,
                "expected_impact": round(total_impact, 3),
                "affected_count": len(downstream),
                "current_mastery": rc["current_mastery"],
                "recommendation": self._generate_intervention(rc, graph),
            })

        # 整体置信度
        confidence = 0.5
        if root_causes:
            top_score = root_causes[0]["root_cause_probability"]
            multi_error_factor = min(len(surface_errors) / 5, 1.0)
            confidence = min(0.5 + top_score * 0.3 + multi_error_factor * 0.2, 0.95)

        result = {
            "diagnosis_id": f"diag_{int(time.time())}_{random.randint(1000, 9999)}",
            "student_id": student_id,
            "subject": subject,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "surface_errors": surface_errors,
            "root_causes": root_causes[:8],
            "causal_chains": causal_chains,
            "intervention_priority": interventions,
            "confidence": round(confidence, 4),
            "confidence_level": self._confidence_label(confidence),
            "summary": self._generate_diagnosis_summary(surface_errors, root_causes, interventions),
        }

        self.diagnosis_history.append(result)
        return result

    def _generate_intervention(self, root_cause: Dict, graph: CausalKnowledgeGraph) -> str:
        """生成干预建议"""
        mastery = root_cause["current_mastery"]
        name = root_cause["node_name"]
        affected = root_cause.get("affected_downstream", [])

        if mastery < 0.3:
            base = f"建议重新系统学习「{name}」的基础概念，当前掌握度仅{mastery:.0%}"
        elif mastery < 0.6:
            base = f"建议针对「{name}」进行专项强化练习，查漏补缺"
        else:
            base = f"建议对「{name}」进行巩固提升，防止知识遗忘"

        if affected:
            downstream_names = "、".join([a["node_name"] for a in affected[:3]])
            base += f"。掌握后将正面影响：{downstream_names}"

        return base

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "高置信度"
        elif confidence >= 0.65:
            return "中置信度"
        else:
            return "低置信度（建议补充更多错误数据）"

    def _generate_diagnosis_summary(self, errors, root_causes, interventions) -> str:
        """生成诊断摘要"""
        if not root_causes:
            return "未检测到明显的因果根因，建议收集更多学习数据。"

        top_cause = root_causes[0]
        summary = (
            f"学生共出现 {len(errors)} 个知识点的错误。"
            f"因果分析显示，最可能的根本原因是「{top_cause['node_name']}」"
            f"（根因概率={top_cause['root_cause_probability']:.2f}）。"
        )

        if interventions:
            top_intervention = interventions[0]
            summary += f"建议优先干预「{top_intervention['node_name']}」，预期改善 {top_intervention['affected_count']} 个下游知识点。"

        return summary

    # ============================================================
    # 反事实推理 (Counterfactual Reasoning)
    # ============================================================

    def counterfactual_analysis(
        self,
        student_id: str,
        target_node: str,
        intervention_mastery: float,
        subject: str = "math",
        current_mastery: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        反事实推理：do(target_node = intervention_mastery)

        核心问题："如果该学生掌握了知识点A，他的后续成绩会怎样？"

        算法：
        1. 记录当前状态（观测值）
        2. 执行 do 操作：将 target_node 的掌握度设为 intervention_mastery
        3. 沿因果图向下传播效应（causal effect propagation）
        4. 计算每个下游节点的预期掌握度变化
        5. 估计整体成绩改善
        """
        graph = self.get_graph(subject)

        # 初始化学生差异化掌握度
        student_mastery = self.get_student_mastery(student_id, graph)
        if current_mastery:
            student_mastery.update(current_mastery)
        for nid, m in student_mastery.items():
            if nid in graph.nodes:
                graph.nodes[nid].mastery = m

        if target_node not in graph.nodes:
            return {"error": f"知识点 {target_node} 不存在"}

        original_mastery = graph.nodes[target_node].mastery

        # 获取所有下游因果效应
        downstream_effects = graph.get_all_effects(target_node)

        # 反事实推理：传播干预效应
        predicted_outcomes = {}
        expected_improvement = {}

        for desc_id, causal_effect, path in downstream_effects:
            original = graph.nodes[desc_id].mastery

            # 因果效应传播模型：
            # 新掌握度 = 原掌握度 + (干预值 - 原值) × 因果效应 × 衰减因子
            delta = (intervention_mastery - original_mastery) * causal_effect
            # 衰减：路径越长，效应越弱
            decay = math.exp(-0.15 * (len(path) - 2)) if len(path) > 2 else 1.0
            adjusted_delta = delta * decay

            predicted = max(0.0, min(1.0, original + adjusted_delta))
            improvement = predicted - original

            predicted_outcomes[desc_id] = round(predicted, 4)
            expected_improvement[desc_id] = round(improvement, 4)

        # 排序：按改善幅度排序
        sorted_improvements = sorted(
            expected_improvement.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 计算整体预期提升
        total_improvement = sum(expected_improvement.values()) / len(expected_improvement) if expected_improvement else 0

        # 生成推理过程
        reasoning_parts = [
            f"反事实场景：do({graph.nodes[target_node].name} = {intervention_mastery:.0%})",
            f"当前{graph.nodes[target_node].name}的掌握度为 {original_mastery:.0%}",
            f"干预将{graph.nodes[target_node].name}的掌握度提升至 {intervention_mastery:.0%}",
            f"通过因果图向下传播效应，影响 {len(downstream_effects)} 个下游知识点",
        ]

        if sorted_improvements:
            top_impact = sorted_improvements[0]
            reasoning_parts.append(
                f"改善最显著的知识点：{graph.nodes[top_impact[0]].name}"
                f"（预期提升 {top_impact[1]:+.1%}）"
            )

        reasoning_parts.append(f"整体预期平均掌握度提升：{total_improvement:+.1%}")

        # 生成详细结果列表
        detailed_results = []
        for desc_id, improvement in sorted_improvements[:10]:
            detailed_results.append({
                "node_id": desc_id,
                "node_name": graph.nodes[desc_id].name,
                "original_mastery": round(graph.nodes[desc_id].mastery, 4),
                "predicted_mastery": predicted_outcomes[desc_id],
                "improvement": improvement,
                "causal_effect": next(
                    (eff for did, eff, _ in downstream_effects if did == desc_id), 0
                ),
            })

        return {
            "analysis_id": f"cf_{int(time.time())}_{random.randint(1000, 9999)}",
            "student_id": student_id,
            "subject": subject,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "scenario": f"do({graph.nodes[target_node].name} = {intervention_mastery:.0%})",
            "target_node": target_node,
            "target_node_name": graph.nodes[target_node].name,
            "original_mastery": round(original_mastery, 4),
            "intervention_value": intervention_mastery,
            "predicted_outcomes": predicted_outcomes,
            "expected_improvement": expected_improvement,
            "detailed_results": detailed_results,
            "total_expected_improvement": round(total_improvement, 4),
            "affected_count": len(downstream_effects),
            "confidence": round(min(0.6 + total_improvement * 2, 0.92), 4),
            "reasoning": "\n".join(reasoning_parts),
        }

    # ============================================================
    # 因果效应估计 (Causal Effect Estimation)
    # ============================================================

    def estimate_causal_effect(
        self,
        cause_node: str,
        effect_node: str,
        subject: str = "math",
    ) -> Dict:
        """
        估计两个知识点间的因果效应
        区分直接效应和间接效应：直接效应=有直接连边的强度，间接效应=通过中介节点的效应
        """
        graph = self.get_graph(subject)

        if cause_node not in graph.nodes or effect_node not in graph.nodes:
            return {"error": "知识点不存在"}

        # 找到所有因果路径
        paths = graph.find_causal_paths(cause_node, effect_node)

        if not paths:
            return {
                "cause_node": cause_node,
                "cause_name": graph.nodes[cause_node].name,
                "effect_node": effect_node,
                "effect_name": graph.nodes[effect_node].name,
                "direct_causal_effect": 0,
                "indirect_causal_effect": 0,
                "total_causal_effect": 0,
                "paths": [],
                "interpretation": f"未找到从「{graph.nodes[cause_node].name}」到「{graph.nodes[effect_node].name}」的因果路径",
            }

        # 直接效应：如果有直接连边，取边的因果强度
        direct_edge_key = f"{cause_node}->{effect_node}"
        direct_effect = 0
        if direct_edge_key in graph.edges:
            direct_effect = graph.edges[direct_edge_key].causal_strength

        # 间接效应：非直接路径的效应之和
        indirect_effect = 0
        path_details = []
        direct_path_found = False

        for i, path_info in enumerate(paths):
            # 路径效应 = 平均因果强度 × 路径衰减
            path_effect = path_info["avg_causal_strength"] * math.exp(-0.1 * path_info["path_length"])

            is_direct = path_info["path_length"] == 1
            if is_direct:
                direct_path_found = True
            else:
                # 间接路径效应累加（权重递减）
                indirect_effect += path_effect * (0.8 ** (i - (1 if direct_path_found else 0)))

            path_details.append({
                "path_index": i + 1,
                "path": path_info["path_names"],
                "avg_strength": path_info["avg_causal_strength"],
                "length": path_info["path_length"],
                "path_effect": round(path_effect, 4),
                "is_direct": is_direct,
            })

        # 总效应：直接效应 + 间接路径效应（带衰减）
        total_raw = direct_effect
        for i, path_info in enumerate(paths):
            if path_info.get("path_length", 999) == 1 or path_info.get("is_direct", False):
                continue  # 跳过直接路径
            path_effect = path_info["avg_causal_strength"] * math.exp(-0.1 * path_info["path_length"])
            total_raw += path_effect * (0.8 ** i)

        # 确保总效应在合理范围
        total_effect = min(total_raw, 1.0)
        # 间接效应 = 总效应 - 直接效应，确保非负
        indirect_effect = max(total_effect - direct_effect, 0)

        # 效应强度标签
        if total_effect >= 0.7:
            strength_label = "强因果效应"
        elif total_effect >= 0.4:
            strength_label = "中等因果效应"
        elif total_effect >= 0.2:
            strength_label = "弱因果效应"
        else:
            strength_label = "微弱因果效应"

        return {
            "cause_node": cause_node,
            "cause_name": graph.nodes[cause_node].name,
            "effect_node": effect_node,
            "effect_name": graph.nodes[effect_node].name,
            "direct_causal_effect": round(direct_effect, 4),
            "indirect_causal_effect": round(indirect_effect, 4),
            "total_causal_effect": round(total_effect, 4),
            "strength_label": strength_label,
            "path_count": len(paths),
            "paths": path_details,
            "interpretation": (
                f"「{graph.nodes[cause_node].name}」对「{graph.nodes[effect_node].name}」"
                f"的总因果效应为 {total_effect:.2f}（直接效应 {direct_effect:.2f} + 间接效应 {indirect_effect:.2f}），"
                f"共找到 {len(paths)} 条因果路径，属于{strength_label}。"
            ),
        }

    # ============================================================
    # 因果发现 (Causal Discovery - 简化版PC算法)
    # ============================================================

    def causal_discovery(
        self,
        score_data: List[Dict],
        subject: str = "math",
    ) -> Dict:
        """
        从学生评分数据中进行因果发现
        简化版PC算法：基于条件独立性检验学习因果结构

        输入：多个学生的知识点评分数据
        输出：学习到的因果结构（邻接矩阵）
        """
        graph = self.get_graph(subject)
        node_ids = list(graph.nodes.keys())
        n_nodes = len(node_ids)

        if not score_data:
            # 生成模拟数据
            score_data = self._generate_causal_discovery_data(graph, 50)

        # 构建评分矩阵
        score_matrix = []
        for record in score_data:
            row = [record.get(nid, random.uniform(0.4, 0.9)) for nid in node_ids]
            score_matrix.append(row)

        # Step 1: 计算相关系数矩阵
        n_samples = len(score_matrix)
        corr_matrix = self._correlation_matrix(score_matrix, n_nodes)

        # Step 2: 条件独立性检验（简化版：用偏相关系数）
        # 如果 X ⊥ Y | Z，则移除 X-Y 边
        adj_matrix = [[0.0] * n_nodes for _ in range(n_nodes)]

        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                # 零阶相关
                if abs(corr_matrix[i][j]) > 0.3:
                    # 一阶偏相关（控制一个变量）
                    keep_edge = True
                    for k in range(n_nodes):
                        if k != i and k != j:
                            partial = self._partial_correlation(
                                corr_matrix, i, j, [k]
                            )
                            if abs(partial) < 0.15:  # 条件独立
                                keep_edge = False
                                break

                    if keep_edge:
                        # 使用先验知识确定方向（基于学习顺序）
                        # 如果 i 是 j 的先验知识，则 i -> j
                        edge_key = f"{node_ids[i]}->{node_ids[j]}"
                        reverse_key = f"{node_ids[j]}->{node_ids[i]}"

                        if edge_key in graph.edges:
                            strength = graph.edges[edge_key].causal_strength
                            adj_matrix[i][j] = strength
                        elif reverse_key in graph.edges:
                            strength = graph.edges[reverse_key].causal_strength
                            adj_matrix[j][i] = strength
                        else:
                            # 新发现的因果关系
                            adj_matrix[i][j] = round(abs(corr_matrix[i][j]) * 0.6, 4)

        # 生成发现的因果边
        discovered_edges = []
        for i in range(n_nodes):
            for j in range(n_nodes):
                if adj_matrix[i][j] > 0:
                    edge_key = f"{node_ids[i]}->{node_ids[j]}"
                    is_known = edge_key in graph.edges
                    discovered_edges.append({
                        "source": node_ids[i],
                        "source_name": graph.nodes[node_ids[i]].name,
                        "target": node_ids[j],
                        "target_name": graph.nodes[node_ids[j]].name,
                        "causal_strength": round(adj_matrix[i][j], 4),
                        "is_known": is_known,
                        "is_new_discovery": not is_known,
                    })

        discovered_edges.sort(key=lambda x: x["causal_strength"], reverse=True)

        new_discoveries = [e for e in discovered_edges if e["is_new_discovery"]]

        return {
            "discovery_id": f"cd_{int(time.time())}_{random.randint(1000, 9999)}",
            "subject": subject,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "sample_size": n_samples,
            "node_count": n_nodes,
            "discovered_edges": discovered_edges,
            "new_discoveries": new_discoveries,
            "new_discovery_count": len(new_discoveries),
            "method": "PC算法（简化版）+ 先验知识定向",
            "summary": (
                f"从 {n_samples} 个样本中发现 {len(discovered_edges)} 条因果关系，"
                f"其中 {len(new_discoveries)} 条为新发现（不在先验知识图谱中）。"
            ),
        }

    def _generate_causal_discovery_data(self, graph: CausalKnowledgeGraph, n: int) -> List[Dict]:
        """生成因果发现用的模拟数据"""
        data = []
        node_ids = list(graph.nodes.keys())

        for _ in range(n):
            record = {}
            # 按拓扑顺序生成（先基础后进阶）
            for nid in node_ids:
                base = random.uniform(0.5, 0.9)
                # 受因果祖先影响
                parents = graph.reverse_adj.get(nid, [])
                for p in parents:
                    if p in record:
                        edge = graph.edges.get(f"{p}->{nid}")
                        if edge:
                            base = base * 0.6 + record[p] * edge.causal_strength * 0.4
                record[nid] = max(0.1, min(1.0, base + random.gauss(0, 0.08)))
            data.append(record)

        return data

    def get_student_mastery(self, student_id: str, graph: CausalKnowledgeGraph) -> Dict[str, float]:
        """
        获取学生各知识点的掌握度
        根据学生ID生成确定性的差异化掌握度（同学生多次查询结果一致）
        """
        # 用学生ID的哈希值作为随机种子，确保同一学生数据一致
        seed = hash(student_id) % (2**31)
        rng = random.Random(seed)

        mastery = {}
        node_ids = list(graph.nodes.keys())

        for nid in node_ids:
            node = graph.nodes[nid]
            # 基础掌握度：基础知识点较高，高阶知识点较低
            category_map = {0: "基础", 1: "核心", 2: "应用", 3: "高阶"}
            cat_name = category_map.get(node.category, "核心")
            category_base = {"基础": 0.75, "核心": 0.65, "应用": 0.55, "高阶": 0.40}
            base = category_base.get(cat_name, 0.5)
            # 根据学生ID差异化
            variation = rng.gauss(0, 0.12)
            # 受前置知识影响
            parents = graph.reverse_adj.get(nid, [])
            parent_influence = 0
            for p in parents:
                if p in mastery:
                    edge = graph.edges.get(f"{p}->{nid}")
                    if edge:
                        parent_influence += mastery[p] * edge.causal_strength * 0.15
            mastery[nid] = round(max(0.1, min(0.95, base + variation + parent_influence)), 3)

        return mastery

    def _correlation_matrix(self, data: List[List[float]], n: int) -> List[List[float]]:
        """计算相关系数矩阵"""
        n_samples = len(data)
        means = [sum(row[i] for row in data) / n_samples for i in range(n)]
        stds = []
        for i in range(n):
            var = sum((row[i] - means[i]) ** 2 for row in data) / n_samples
            stds.append(math.sqrt(var) if var > 0 else 1.0)

        corr = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr[i][j] = 1.0
                else:
                    cov = sum(
                        (data[k][i] - means[i]) * (data[k][j] - means[j])
                        for k in range(n_samples)
                    ) / n_samples
                    corr[i][j] = cov / (stds[i] * stds[j]) if stds[i] * stds[j] > 0 else 0
        return corr

    def _partial_correlation(self, corr: List[List[float]], i: int, j: int, controls: List[int]) -> float:
        """计算偏相关系数（简化版，仅支持一阶）"""
        if not controls:
            return corr[i][j]
        k = controls[0]
        denom_sq = (1 - corr[i][k] ** 2) * (1 - corr[j][k] ** 2)
        if denom_sq <= 0:
            return 0
        denom = math.sqrt(denom_sq)
        if denom == 0:
            return 0
        return (corr[i][j] - corr[i][k] * corr[j][k]) / denom

    # ============================================================
    # 学习路径优化 (Causal Path Optimization)
    # ============================================================

    def recommend_learning_path(
        self,
        student_id: str,
        target_nodes: List[str],
        subject: str = "math",
        current_mastery: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        基于因果图推荐最优学习路径

        策略：拓扑排序 + 因果效应加权
        1. 找到目标知识点的所有因果前提
        2. 按因果链拓扑排序
        3. 优先学习掌握度低且因果效应大的前提
        """
        graph = self.get_graph(subject)

        # 初始化学生差异化掌握度
        student_mastery = self.get_student_mastery(student_id, graph)
        if current_mastery:
            student_mastery.update(current_mastery)
        for nid, m in student_mastery.items():
            if nid in graph.nodes:
                graph.nodes[nid].mastery = m

        # 收集所有需要学习的节点（目标 + 所有前提）
        all_prerequisites: Set[str] = set(target_nodes)
        for target in target_nodes:
            if target in graph.nodes:
                ancestors = graph.get_all_causes(target)
                for anc_id, _, _ in ancestors:
                    all_prerequisites.add(anc_id)

        # 拓扑排序（基于因果图的偏序关系）
        # 简化：按难度和因果层级排序
        learning_sequence = []
        remaining = set(all_prerequisites)

        # 按层级排序：基础 → 核心 → 进阶
        category_order = {"基础": 0, "核心": 1, "进阶": 2}

        while remaining:
            # 找到当前可学习的节点（所有前提已在序列中或无前提）
            available = []
            for nid in remaining:
                parents = graph.reverse_adj.get(nid, [])
                # 检查是否所有已在remaining中的前提都已学习
                unmet = [p for p in parents if p in remaining and p != nid]
                if not unmet:
                    available.append(nid)

            if not available:
                # 避免死循环
                available = list(remaining)

            # 过滤掉不在图中的节点（防止KeyError）
            available = [nid for nid in available if nid in graph.nodes]
            if not available:
                break

            # 按掌握度（低优先）和难度（低优先）排序
            available.sort(key=lambda nid: (
                category_order.get(graph.nodes[nid].category, 1),
                graph.nodes[nid].mastery,  # 掌握度低的优先
                graph.nodes[nid].difficulty,
            ))

            next_node = available[0]
            learning_sequence.append(next_node)
            remaining.remove(next_node)

        # 生成路径详情
        path_details = []
        for idx, nid in enumerate(learning_sequence):
            node = graph.nodes[nid]
            # 计算该节点对目标的因果效应
            total_effect = 0
            for target in target_nodes:
                paths = graph.find_causal_paths(nid, target)
                if paths:
                    total_effect += paths[0]["avg_causal_strength"]

            path_details.append({
                "step": idx + 1,
                "node_id": nid,
                "node_name": node.name,
                "category": node.category,
                "difficulty": node.difficulty,
                "current_mastery": round(node.mastery, 3),
                "needs_learning": node.mastery < 0.7,
                "causal_effect_to_target": round(min(total_effect, 1.0), 3),
                "description": node.description,
                "is_target": nid in target_nodes,
            })

        # 估算总学习时间
        total_time = sum(
            max(0, (1 - p["current_mastery"])) * p["difficulty"] * 10
            for p in path_details
            if p["needs_learning"]
        )

        return {
            "path_id": f"path_{int(time.time())}_{random.randint(1000, 9999)}",
            "student_id": student_id,
            "subject": subject,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "target_nodes": [graph.nodes[t].name for t in target_nodes if t in graph.nodes],
            "target_node_ids": target_nodes,
            "total_steps": len(path_details),
            "steps_needs_learning": sum(1 for p in path_details if p["needs_learning"]),
            "estimated_hours": round(total_time, 1),
            "learning_path": path_details,
            "summary": (
                f"基于因果图分析，推荐 {len(path_details)} 步学习路径，"
                f"其中 {sum(1 for p in path_details if p['needs_learning'])} 步需要重点学习，"
                f"预计耗时 {total_time:.1f} 小时。"
            ),
        }

    # ============================================================
    # 综合科研报告
    # ============================================================

    def generate_research_report(self, subject: str = "math") -> Dict:
        """生成因果推理科研报告"""
        graph = self.get_graph(subject)

        # 图谱统计
        total_edges = len(graph.edges)
        direct_edges = sum(1 for e in graph.edges.values() if e.edge_type == "direct")
        indirect_edges = total_edges - direct_edges

        # 因果效应分布
        effects = [e.causal_strength for e in graph.edges.values()]
        avg_effect = sum(effects) / len(effects) if effects else 0

        # 关键因果链（影响最广的知识点）
        node_impacts = []
        for nid in graph.nodes:
            downstream = graph.get_all_effects(nid)
            total_impact = sum(eff for _, eff, _ in downstream)
            node_impacts.append({
                "node_id": nid,
                "node_name": graph.nodes[nid].name,
                "downstream_count": len(downstream),
                "total_causal_impact": round(total_impact, 3),
                "category": graph.nodes[nid].category,
            })
        node_impacts.sort(key=lambda x: x["total_causal_impact"], reverse=True)

        # 诊断历史统计
        diagnosis_count = len(self.diagnosis_history)

        return {
            "report_id": f"report_{int(time.time())}",
            "subject": subject,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "graph_statistics": {
                "total_nodes": len(graph.nodes),
                "total_edges": total_edges,
                "direct_edges": direct_edges,
                "indirect_edges": indirect_edges,
                "avg_causal_strength": round(avg_effect, 4),
                "max_causal_strength": round(max(effects), 4) if effects else 0,
                "min_causal_strength": round(min(effects), 4) if effects else 0,
            },
            "key_causal_nodes": node_impacts[:5],
            "diagnosis_count": diagnosis_count,
            "academic_contribution": {
                "innovation": "AI + Education + Causal Inference",
                "method": "因果知识图谱 + do-calculus + PC算法",
                "advantage": "从相关性分析升级为因果推理，能回答'为什么'和'如果...会怎样'",
                "applicable_venues": ["EDM", "LAK", "AIED", "AAAI"],
            },
            "methodology": [
                "因果知识图谱构建（领域知识 + 因果结构学习）",
                "根因分析（因果祖先追溯 + 根因概率计算）",
                "反事实推理（do-calculus + 效应传播）",
                "因果发现（PC算法 + 条件独立性检验）",
                "因果路径优化（拓扑排序 + 效应加权）",
            ],
        }


# 全局实例
causal_engine = CausalInferenceEngine()
