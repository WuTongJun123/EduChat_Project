"""
科研评估引擎
支持评分一致性分析、A/B测试、置信度评估、Prompt实验、数据导出
"""
import json
import os
import time
import math
import random
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict


class ResearchEngine:
    """科研评估核心引擎"""

    def __init__(self):
        self.experiments = {}        # A/B测试实验
        self.consistency_records = []  # 一致性评估记录
        self.prompt_variants = {}    # Prompt变体库
        self.export_history = []     # 导出历史

    # ==================== 评分一致性评估 ====================

    def calculate_cohens_kappa(self, rater1_scores: List[int], rater2_scores: List[int]) -> Dict[str, Any]:
        """
        Cohen's Kappa 系数计算
        衡量两个评分者之间的一致性，消除偶然一致的影响
        
        Kappa < 0: 低于偶然一致
        0.0-0.20: 极低一致性
        0.21-0.40: 一般一致性
        0.41-0.60: 中等一致性
        0.61-0.80: 较高一致性
        0.81-1.00: 几乎完全一致
        """
        n = len(rater1_scores)
        if n == 0 or n != len(rater2_scores):
            return {"error": "评分数据长度不匹配或为空"}

        # 构建混淆矩阵
        categories = sorted(set(rater1_scores + rater2_scores))
        matrix = defaultdict(lambda: defaultdict(int))
        for s1, s2 in zip(rater1_scores, rater2_scores):
            matrix[s1][s2] += 1

        # 计算观察到的一致性 Po
        po = sum(matrix[c][c] for c in categories) / n

        # 计算偶然一致性 Pe
        marg_r1 = {c: sum(matrix[c].values()) / n for c in categories}
        marg_r2 = {c: sum(matrix[r][c] for r in categories) / n for c in categories}
        pe = sum(marg_r1[c] * marg_r2[c] for c in categories)

        kappa = (po - pe) / (1 - pe) if (1 - pe) != 0 else 0

        # 判定等级
        if kappa < 0:
            level = "低于偶然一致"
        elif kappa < 0.21:
            level = "极低一致性"
        elif kappa < 0.41:
            level = "一般一致性"
        elif kappa < 0.61:
            level = "中等一致性"
        elif kappa < 0.81:
            level = "较高一致性"
        else:
            level = "几乎完全一致"

        return {
            "kappa": round(kappa, 4),
            "po": round(po, 4),
            "pe": round(pe, 4),
            "level": level,
            "sample_size": n,
            "categories": categories,
            "confusion_matrix": {str(k): dict(v) for k, v in matrix.items()}
        }

    def calculate_pearson_correlation(self, scores1: List[float], scores2: List[float]) -> Dict[str, Any]:
        """
        Pearson 相关系数计算
        衡量两组连续分数之间的线性相关程度
        """
        n = len(scores1)
        if n < 2 or n != len(scores2):
            return {"error": "数据不足或长度不匹配"}

        mean1 = sum(scores1) / n
        mean2 = sum(scores2) / n

        numerator = sum((s1 - mean1) * (s2 - mean2) for s1, s2 in zip(scores1, scores2))
        denom1 = math.sqrt(sum((s - mean1) ** 2 for s in scores1))
        denom2 = math.sqrt(sum((s - mean2) ** 2 for s in scores2))

        if denom1 == 0 or denom2 == 0:
            return {"error": "分数方差为零，无法计算相关系数"}

        r = numerator / (denom1 * denom2)

        # t检验
        t_stat = r * math.sqrt(n - 2) / math.sqrt(1 - r ** 2) if abs(r) < 1 else float('inf')
        p_value_approx = "p < 0.001" if abs(t_stat) > 3.29 else ("p < 0.01" if abs(t_stat) > 2.58 else ("p < 0.05" if abs(t_stat) > 1.96 else "p >= 0.05"))

        # 解释强度
        abs_r = abs(r)
        if abs_r < 0.1:
            strength = "极弱相关"
        elif abs_r < 0.3:
            strength = "弱相关"
        elif abs_r < 0.5:
            strength = "中等相关"
        elif abs_r < 0.7:
            strength = "强相关"
        else:
            strength = "极强相关"

        return {
            "r": round(r, 4),
            "r_squared": round(r ** 2, 4),
            "t_statistic": round(t_stat, 4),
            "p_value": p_value_approx,
            "strength": strength,
            "direction": "正相关" if r > 0 else "负相关" if r < 0 else "无相关",
            "sample_size": n,
            "mean_diff": round(mean1 - mean2, 2),
            "mae": round(sum(abs(s1 - s2) for s1, s2 in zip(scores1, scores2)) / n, 2),
            "rmse": round(math.sqrt(sum((s1 - s2) ** 2 for s1, s2 in zip(scores1, scores2)) / n), 2)
        }

    def run_consistency_evaluation(
        self,
        ai_scores: List[float],
        human_scores: List[float],
        evaluator_name: str = "人工评分",
        task_name: str = "未命名评估"
    ) -> Dict[str, Any]:
        """
        完整的一致性评估流程
        """
        # 将连续分数离散化为等级（用于Kappa）
        def to_grade(score):
            if score >= 90:
                return 5  # 优秀
            elif score >= 80:
                return 4  # 良好
            elif score >= 70:
                return 3  # 中等
            elif score >= 60:
                return 2  # 及格
            else:
                return 1  # 不及格

        ai_grades = [to_grade(s) for s in ai_scores]
        human_grades = [to_grade(s) for s in human_scores]

        kappa_result = self.calculate_cohens_kappa(ai_grades, human_grades)
        pearson_result = self.calculate_pearson_correlation(ai_scores, human_scores)

        # 计算分类一致率（精确匹配）
        exact_match = sum(1 for a, h in zip(ai_scores, human_scores) if abs(a - h) <= 2) / len(ai_scores)
        within_5 = sum(1 for a, h in zip(ai_scores, human_scores) if abs(a - h) <= 5) / len(ai_scores)
        within_10 = sum(1 for a, h in zip(ai_scores, human_scores) if abs(a - h) <= 10) / len(ai_scores)

        # 系统偏差分析
        diffs = [a - h for a, h in zip(ai_scores, human_scores)]
        bias = sum(diffs) / len(diffs)
        bias_std = math.sqrt(sum(d ** 2 for d in diffs) / len(diffs) - bias ** 2) if len(diffs) > 1 else 0

        result = {
            "id": f"eval_{int(time.time())}_{random.randint(1000, 9999)}",
            "task_name": task_name,
            "evaluator_name": evaluator_name,
            "timestamp": datetime.now().isoformat(),
            "sample_size": len(ai_scores),
            "kappa": kappa_result,
            "pearson": pearson_result,
            "agreement_rates": {
                "exact_match_2pts": round(exact_match, 4),
                "within_5pts": round(within_5, 4),
                "within_10pts": round(within_10, 4)
            },
            "bias_analysis": {
                "mean_bias": round(bias, 2),
                "bias_std": round(bias_std, 2),
                "bias_direction": "AI偏高" if bias > 1 else "AI偏低" if bias < -1 else "无显著偏差",
                "bias_interpretation": (
                    f"AI评分平均{'高' if bias > 0 else '低'}于人工评分{abs(bias):.1f}分，"
                    f"{'存在系统偏差' if abs(bias) > 3 else '偏差在可接受范围内'}"
                )
            },
            "score_pairs": list(zip(ai_scores, human_scores)),
            "summary": self._generate_consistency_summary(kappa_result, pearson_result, exact_match, bias)
        }

        self.consistency_records.append(result)
        return result

    def _generate_consistency_summary(self, kappa, pearson, exact_match, bias) -> str:
        """生成一致性评估总结"""
        kappa_val = kappa.get("kappa", 0) if "kappa" in kappa else 0
        r_val = pearson.get("r", 0) if "r" in pearson else 0
        lines = []
        lines.append(f"一致性评估完成，样本量：{kappa.get('sample_size', 0)}")
        lines.append(f"Cohen's Kappa = {kappa_val}（{kappa.get('level', 'N/A')}）")
        lines.append(f"Pearson r = {r_val}（{pearson.get('strength', 'N/A')}，{pearson.get('direction', 'N/A')}）")
        lines.append(f"精确匹配率（±2分）= {exact_match:.1%}")
        lines.append(f"系统偏差 = {bias:.1f}分（{'AI偏高' if bias > 1 else 'AI偏低' if bias < -1 else '无显著偏差'}）")
        return "\n".join(lines)

    def generate_demo_consistency_data(self, count: int = 30) -> Dict[str, Any]:
        """生成演示用一致性评估数据"""
        templates = [
            ("函数求值", "math"),
            ("方程求解", "math"),
            ("几何证明", "math"),
            ("作文批改", "chinese"),
            ("阅读理解", "english"),
            ("编程作业", "coding"),
        ]
        task_name, _ = random.choice(templates)

        ai_scores = []
        human_scores = []
        for _ in range(count):
            base = random.randint(55, 95)
            ai_score = max(0, min(100, base + random.gauss(0, 3)))
            human_score = max(0, min(100, base + random.gauss(0, 4)))
            ai_scores.append(round(ai_score, 1))
            human_scores.append(round(human_score, 1))

        return self.run_consistency_evaluation(ai_scores, human_scores, "教师A", task_name)

    # ==================== A/B 测试框架 ====================

    def create_experiment(
        self,
        name: str,
        description: str,
        config_a: Dict[str, Any],
        config_b: Dict[str, Any],
        test_samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        创建A/B测试实验
        config_a / config_b: 包含 prompt / rubric_id / temperature / max_tokens 等参数
        test_samples: 测试样本 [{"content": "...", "reference_score": 85}]
        """
        exp_id = f"exp_{int(time.time())}_{random.randint(1000, 9999)}"

        # 模拟运行两组实验
        results_a = self._simulate_experiment_run(test_samples, config_a)
        results_b = self._simulate_experiment_run(test_samples, config_b)

        # 计算统计指标
        stats = self._calculate_ab_statistics(results_a, results_b)

        experiment = {
            "id": exp_id,
            "name": name,
            "description": description,
            "config_a": {"label": "对照组 (A)", **config_a},
            "config_b": {"label": "实验组 (B)", **config_b},
            "sample_count": len(test_samples),
            "results_a": results_a,
            "results_b": results_b,
            "statistics": stats,
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }

        self.experiments[exp_id] = experiment
        return experiment

    def _simulate_experiment_run(self, samples: List[Dict], config: Dict) -> List[Dict]:
        """模拟实验运行（演示模式）"""
        results = []
        temperature = config.get("temperature", 0.3)
        # 温度越高，评分波动越大
        noise_base = temperature * 8

        for i, sample in enumerate(samples):
            ref_score = sample.get("reference_score", 80)
            # 模拟AI评分（围绕参考分数波动）
            ai_score = max(0, min(100, ref_score + random.gauss(0, noise_base)))
            ai_score = round(ai_score, 1)

            results.append({
                "sample_id": i + 1,
                "content_preview": sample.get("content", "")[:60],
                "reference_score": ref_score,
                "ai_score": ai_score,
                "error": round(abs(ai_score - ref_score), 1),
                "latency_ms": round(random.uniform(300, 1200), 0),
                "response_length": random.randint(200, 800)
            })
        return results

    def _calculate_ab_statistics(self, results_a: List[Dict], results_b: List[Dict]) -> Dict[str, Any]:
        """计算A/B测试统计指标"""
        errors_a = [r["error"] for r in results_a]
        errors_b = [r["error"] for r in results_b]
        latency_a = [r["latency_ms"] for r in results_a]
        latency_b = [r["latency_ms"] for r in results_b]

        n = len(errors_a)
        mean_a = sum(errors_a) / n
        mean_b = sum(errors_b) / n

        # 配对t检验（近似）
        diff = [a - b for a, b in zip(errors_a, errors_b)]
        mean_diff = sum(diff) / n
        std_diff = math.sqrt(sum(d ** 2 for d in diff) / n - mean_diff ** 2) if n > 1 else 0
        t_stat = mean_diff / (std_diff / math.sqrt(n)) if std_diff > 0 else 0

        if abs(t_stat) > 2.58:
            significance = "极显著 (p<0.01)"
        elif abs(t_stat) > 1.96:
            significance = "显著 (p<0.05)"
        else:
            significance = "不显著 (p>=0.05)"

        # 效果量 Cohen's d
        pooled_std = math.sqrt((sum((e - mean_a) ** 2 for e in errors_a) + sum((e - mean_b) ** 2 for e in errors_b)) / (2 * n))
        cohen_d = (mean_a - mean_b) / pooled_std if pooled_std > 0 else 0

        # 判定哪个更优
        if mean_b < mean_a and "显著" in significance:
            winner = "B（实验组）显著优于A（对照组）"
        elif mean_a < mean_b and "显著" in significance:
            winner = "A（对照组）显著优于B（实验组）"
        else:
            winner = "两组无显著差异"

        return {
            "mean_error_a": round(mean_a, 2),
            "mean_error_b": round(mean_b, 2),
            "improvement": round((mean_a - mean_b) / mean_a * 100, 1) if mean_a > 0 else 0,
            "std_error_a": round(math.sqrt(sum((e - mean_a) ** 2 for e in errors_a) / n), 2),
            "std_error_b": round(math.sqrt(sum((e - mean_b) ** 2 for e in errors_b) / n), 2),
            "mean_latency_a": round(sum(latency_a) / n, 0),
            "mean_latency_b": round(sum(latency_b) / n, 0),
            "t_statistic": round(t_stat, 4),
            "significance": significance,
            "cohens_d": round(cohen_d, 4),
            "effect_size": "小" if abs(cohen_d) < 0.5 else "中" if abs(cohen_d) < 0.8 else "大",
            "winner": winner,
            "sample_size": n
        }

    def list_experiments(self) -> List[Dict]:
        """列出所有实验"""
        return [
            {
                "id": e["id"],
                "name": e["name"],
                "description": e["description"],
                "sample_count": e["sample_count"],
                "created_at": e["created_at"],
                "winner": e["statistics"]["winner"]
            }
            for e in self.experiments.values()
        ]

    def get_experiment(self, exp_id: str) -> Optional[Dict]:
        return self.experiments.get(exp_id)

    # ==================== 置信度评估 ====================

    def calculate_confidence(self, content: str, score: float, rubric_id: Optional[str] = None) -> Dict[str, Any]:
        """
        评分置信度分析
        基于内容长度、复杂度、评分边界等因素计算置信度
        """
        content_len = len(content)
        factors = []

        # 因素1：内容长度
        if content_len < 50:
            length_conf = 0.3
            factors.append({"factor": "内容长度", "value": f"{content_len}字", "confidence": length_conf, "note": "内容过短，评估依据不足"})
        elif content_len < 200:
            length_conf = 0.6
            factors.append({"factor": "内容长度", "value": f"{content_len}字", "confidence": length_conf, "note": "内容偏短"})
        elif content_len < 1000:
            length_conf = 0.9
            factors.append({"factor": "内容长度", "value": f"{content_len}字", "confidence": length_conf, "note": "内容长度适中"})
        else:
            length_conf = 0.85
            factors.append({"factor": "内容长度", "value": f"{content_len}字", "confidence": length_conf, "note": "内容较长，需关注完整性"})

        # 因素2：分数边界
        if score <= 60 or score >= 95:
            boundary_conf = 0.7
            factors.append({"factor": "分数边界", "value": f"{score}分", "confidence": boundary_conf, "note": "接近极端分数，建议人工复核"})
        elif 65 <= score <= 75:
            boundary_conf = 0.75
            factors.append({"factor": "分数边界", "value": f"{score}分", "confidence": boundary_conf, "note": "处于及格线附近，建议人工复核"})
        else:
            boundary_conf = 0.9
            factors.append({"factor": "分数边界", "value": f"{score}分", "confidence": boundary_conf, "note": "分数处于安全区间"})

        # 因素3：内容复杂度（基于特征词密度）
        complexity_markers = ["因为", "所以", "因此", "由于", "证明", "推导", "综上", "分析", "比较", "假设"]
        marker_count = sum(content.count(m) for m in complexity_markers)
        if marker_count < 2:
            complexity_conf = 0.6
            factors.append({"factor": "逻辑复杂度", "value": f"{marker_count}个逻辑标记", "confidence": complexity_conf, "note": "逻辑结构简单"})
        elif marker_count < 5:
            complexity_conf = 0.85
            factors.append({"factor": "逻辑复杂度", "value": f"{marker_count}个逻辑标记", "confidence": complexity_conf, "note": "逻辑结构适中"})
        else:
            complexity_conf = 0.8
            factors.append({"factor": "逻辑复杂度", "value": f"{marker_count}个逻辑标记", "confidence": complexity_conf, "note": "逻辑复杂，需更深入分析"})

        # 因素4：评分标准适用性
        if rubric_id:
            rubric_conf = 0.92
            factors.append({"factor": "评分标准", "value": "已绑定Rubric", "confidence": rubric_conf, "note": "使用结构化评分标准，一致性更高"})
        else:
            rubric_conf = 0.65
            factors.append({"factor": "评分标准", "value": "未绑定Rubric", "confidence": rubric_conf, "note": "使用自由评分，建议绑定评分标准"})

        # 综合置信度
        weights = [0.25, 0.3, 0.2, 0.25]
        confidences = [length_conf, boundary_conf, complexity_conf, rubric_conf]
        overall_confidence = sum(w * c for w, c in zip(weights, confidences))

        # 判定是否需要人工复核
        if overall_confidence < 0.7:
            review_needed = True
            review_reason = "置信度较低，建议人工复核"
        elif any(f["confidence"] < 0.6 for f in factors):
            review_needed = True
            review_reason = "存在低置信度因子，建议人工复核"
        else:
            review_needed = False
            review_reason = "置信度充足"

        return {
            "overall_confidence": round(overall_confidence, 4),
            "confidence_percent": f"{round(overall_confidence * 100, 1)}%",
            "review_needed": review_needed,
            "review_reason": review_reason,
            "factors": factors,
            "score": score,
            "content_length": content_len,
            "recommendation": self._get_confidence_recommendation(overall_confidence, score)
        }

    def _get_confidence_recommendation(self, confidence: float, score: float) -> str:
        if confidence >= 0.85:
            return "评分结果可信，可直接采用"
        elif confidence >= 0.7:
            return "评分结果较为可信，建议教师快速浏览确认"
        elif confidence >= 0.5:
            return "评分结果存疑，建议教师重点复核"
        else:
            return "评分结果不可信，必须由教师重新评分"

    # ==================== Prompt 工程实验台 ====================

    def create_prompt_variant(self, name: str, system_prompt: str, description: str = "") -> Dict[str, Any]:
        """创建Prompt变体"""
        vid = f"prompt_{int(time.time())}_{random.randint(1000, 9999)}"
        variant = {
            "id": vid,
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "created_at": datetime.now().isoformat(),
            "test_results": []
        }
        self.prompt_variants[vid] = variant
        return variant

    def list_prompt_variants(self) -> List[Dict]:
        return list(self.prompt_variants.values())

    def test_prompt(
        self,
        prompt_id: str,
        test_content: str,
        reference_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """测试单个Prompt变体"""
        variant = self.prompt_variants.get(prompt_id)
        if not variant:
            return {"error": "Prompt变体不存在"}

        # 模拟Prompt测试（演示模式）
        prompt_complexity = len(variant["system_prompt"])
        # Prompt越详细，评分越接近参考值（模拟）
        if reference_score:
            noise = max(2, 15 - prompt_complexity / 50)
            ai_score = round(max(0, min(100, reference_score + random.gauss(0, noise))), 1)
            error = round(abs(ai_score - reference_score), 1)
        else:
            ai_score = round(random.uniform(60, 90), 1)
            error = None

        result = {
            "test_id": f"test_{int(time.time())}_{random.randint(100, 999)}",
            "prompt_id": prompt_id,
            "prompt_name": variant["name"],
            "content_preview": test_content[:80],
            "ai_score": ai_score,
            "reference_score": reference_score,
            "error": error,
            "latency_ms": round(random.uniform(400, 1500), 0),
            "response_length": random.randint(300, 1000),
            "timestamp": datetime.now().isoformat()
        }

        variant["test_results"].append(result)
        return result

    def compare_prompts(self, prompt_ids: List[str]) -> Dict[str, Any]:
        """对比多个Prompt变体的表现"""
        comparison = []
        for pid in prompt_ids:
            variant = self.prompt_variants.get(pid)
            if not variant:
                continue
            results = variant["test_results"]
            if not results:
                continue

            errors = [r["error"] for r in results if r["error"] is not None]
            latencies = [r["latency_ms"] for r in results]

            comparison.append({
                "prompt_id": pid,
                "prompt_name": variant["name"],
                "test_count": len(results),
                "mean_error": round(sum(errors) / len(errors), 2) if errors else None,
                "std_error": round(math.sqrt(sum((e - sum(errors) / len(errors)) ** 2 for e in errors) / len(errors)), 2) if errors else None,
                "mean_latency_ms": round(sum(latencies) / len(latencies), 0),
                "prompt_length": len(variant["system_prompt"]),
                "best_error": min(errors) if errors else None,
                "worst_error": max(errors) if errors else None
            })

        # 排序：按平均误差升序
        comparison.sort(key=lambda x: x["mean_error"] if x["mean_error"] is not None else 999)

        return {
            "comparison": comparison,
            "best_prompt": comparison[0]["prompt_name"] if comparison else None,
            "insight": self._generate_prompt_insight(comparison)
        }

    def _generate_prompt_insight(self, comparison: List[Dict]) -> str:
        if not comparison:
            return "暂无对比数据"
        best = comparison[0]
        worst = comparison[-1]
        if best.get("mean_error") and worst.get("mean_error"):
            improvement = round(((worst["mean_error"] - best["mean_error"]) / worst["mean_error"]) * 100, 1)
            return (f"最佳Prompt「{best['prompt_name']}」平均误差{best['mean_error']}分，"
                    f"相比最差Prompt「{worst['prompt_name']}」误差降低{improvement}%。"
                    f"Prompt长度{best['prompt_length']}字符，建议参考其结构优化其他变体。")
        return "数据不足，无法生成分析"

    # ==================== 数据导出 ====================

    def export_experiment_data(self, data_type: str, format: str = "csv") -> Dict[str, Any]:
        """
        导出实验数据
        data_type: consistency / experiments / prompts / all
        format: csv / json
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            return self._export_json(data_type, timestamp)
        else:
            return self._export_csv(data_type, timestamp)

    def _export_csv(self, data_type: str, timestamp: str) -> Dict[str, Any]:
        files = []

        if data_type in ("consistency", "all"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["评估ID", "任务名称", "评估者", "样本量", "Kappa", "Pearson_r",
                             "精确匹配率", "5分内匹配率", "10分内匹配率", "平均偏差", "偏差方向", "时间戳"])
            for r in self.consistency_records:
                writer.writerow([
                    r["id"], r["task_name"], r["evaluator_name"], r["sample_size"],
                    r["kappa"].get("kappa", "N/A"), r["pearson"].get("r", "N/A"),
                    r["agreement_rates"]["exact_match_2pts"],
                    r["agreement_rates"]["within_5pts"],
                    r["agreement_rates"]["within_10pts"],
                    r["bias_analysis"]["mean_bias"],
                    r["bias_analysis"]["bias_direction"],
                    r["timestamp"]
                ])
            files.append({"name": f"consistency_{timestamp}.csv", "content": output.getvalue()})
            output.close()

        if data_type in ("experiments", "all"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["实验ID", "实验名称", "样本量", "A组平均误差", "B组平均误差",
                             "改善率", "t统计量", "显著性", "Cohen_d", "效果量", "胜出组", "创建时间"])
            for exp in self.experiments.values():
                s = exp["statistics"]
                writer.writerow([
                    exp["id"], exp["name"], exp["sample_count"],
                    s["mean_error_a"], s["mean_error_b"], s["improvement"],
                    s["t_statistic"], s["significance"], s["cohens_d"],
                    s["effect_size"], s["winner"], exp["created_at"]
                ])
            files.append({"name": f"experiments_{timestamp}.csv", "content": output.getvalue()})
            output.close()

        if data_type in ("prompts", "all"):
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["PromptID", "名称", "描述", "Prompt长度", "测试次数", "平均误差", "平均延迟ms"])
            for v in self.prompt_variants.values():
                results = v["test_results"]
                errors = [r["error"] for r in results if r["error"] is not None]
                latencies = [r["latency_ms"] for r in results]
                writer.writerow([
                    v["id"], v["name"], v["description"], len(v["system_prompt"]),
                    len(results),
                    round(sum(errors) / len(errors), 2) if errors else "N/A",
                    round(sum(latencies) / len(latencies), 0) if latencies else "N/A"
                ])
            files.append({"name": f"prompts_{timestamp}.csv", "content": output.getvalue()})
            output.close()

        export_record = {
            "id": f"export_{timestamp}",
            "data_type": data_type,
            "format": "csv",
            "file_count": len(files),
            "files": files,
            "timestamp": datetime.now().isoformat()
        }
        self.export_history.append(export_record)
        return export_record

    def _export_json(self, data_type: str, timestamp: str) -> Dict[str, Any]:
        data = {}
        if data_type in ("consistency", "all"):
            data["consistency_records"] = self.consistency_records
        if data_type in ("experiments", "all"):
            data["experiments"] = list(self.experiments.values())
        if data_type in ("prompts", "all"):
            data["prompt_variants"] = list(self.prompt_variants.values())

        content = json.dumps(data, ensure_ascii=False, indent=2)
        return {
            "id": f"export_{timestamp}",
            "data_type": data_type,
            "format": "json",
            "file_count": 1,
            "files": [{"name": f"research_data_{timestamp}.json", "content": content}],
            "timestamp": datetime.now().isoformat()
        }

    def get_research_overview(self) -> Dict[str, Any]:
        """科研数据总览"""
        # 汇总一致性评估
        consistency_summary = {
            "total_evaluations": len(self.consistency_records),
            "avg_kappa": 0,
            "avg_pearson_r": 0,
            "avg_agreement": 0
        }
        if self.consistency_records:
            consistency_summary["avg_kappa"] = round(
                sum(r["kappa"].get("kappa", 0) for r in self.consistency_records) / len(self.consistency_records), 4)
            consistency_summary["avg_pearson_r"] = round(
                sum(r["pearson"].get("r", 0) for r in self.consistency_records) / len(self.consistency_records), 4)
            consistency_summary["avg_agreement"] = round(
                sum(r["agreement_rates"]["within_5pts"] for r in self.consistency_records) / len(self.consistency_records), 4)

        # 汇总A/B测试
        experiment_summary = {
            "total_experiments": len(self.experiments),
            "significant_results": sum(1 for e in self.experiments.values() if "显著" in e["statistics"]["significance"]),
            "avg_improvement": 0
        }
        if self.experiments:
            experiment_summary["avg_improvement"] = round(
                sum(e["statistics"]["improvement"] for e in self.experiments.values()) / len(self.experiments), 1)

        # 汇总Prompt变体
        prompt_summary = {
            "total_variants": len(self.prompt_variants),
            "total_tests": sum(len(v["test_results"]) for v in self.prompt_variants.values())
        }

        return {
            "consistency": consistency_summary,
            "experiments": experiment_summary,
            "prompts": prompt_summary,
            "exports": len(self.export_history),
            "timestamp": datetime.now().isoformat()
        }


# 全局实例
research_engine = ResearchEngine()

# 预置示例Prompt变体
_default_prompts = [
    ("基础批改Prompt", "你是一位教师，请批改以下作业。给出评分和建议。", "最简单的Prompt基线"),
    ("结构化批改Prompt", "你是一位经验丰富的教师。请按以下结构批改作业：\n1. 整体评价\n2. 逐条错误分析\n3. 百分制评分及扣分明细\n4. 针对性学习建议\n5. 鼓励性结尾\n\n保持专业亲切的语气。", "结构化输出，格式规范"),
    ("CoT思维链Prompt", "你是一位资深教师。请逐步思考后批改作业：\n第一步：分析作业类型和考察知识点\n第二步：逐句检查正确性\n第三步：评估解题思路和方法\n第四步：检查格式和规范\n第五步：综合以上分析给出百分制评分\n第六步：撰写详细反馈\n\n请展示你的思考过程。", "Chain-of-Thought思维链，提升推理质量"),
]

for name, prompt, desc in _default_prompts:
    research_engine.create_prompt_variant(name, prompt, desc)
