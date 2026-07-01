"""
教师自定义 Rubric 评分标准模块
支持评分标准的创建、编辑、管理和基于标准的智能批改
"""
import json
import os
import time
import uuid
import random
import re
from datetime import datetime
from typing import List, Dict, Any, Optional


class RubricCriterion:
    """评分维度（准则）"""
    def __init__(self, name: str, weight: float, description: str = "", levels: List[Dict] = None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.weight = weight          # 权重 0.0~1.0
        self.description = description
        self.levels = levels or []    # 评分等级列表


class Rubric:
    """评分标准"""
    def __init__(self, name: str, subject: str, description: str = "", criteria: List[Dict] = None):
        self.id = f"rubric_{int(time.time())}_{random.randint(1000, 9999)}"
        self.name = name
        self.subject = subject
        self.description = description
        self.criteria = criteria or []
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "description": self.description,
            "criteria": self.criteria,
            "total_weight": sum(c.get("weight", 0) for c in self.criteria),
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def validate(self) -> Dict[str, Any]:
        """校验评分标准合法性"""
        errors = []
        if not self.name:
            errors.append("评分标准名称不能为空")
        if not self.criteria:
            errors.append("至少需要一个评分维度")
        
        total_weight = sum(c.get("weight", 0) for c in self.criteria)
        if abs(total_weight - 1.0) > 0.001:
            errors.append(f"权重总和必须为1.0，当前为{total_weight:.2f}")
        
        for i, c in enumerate(self.criteria):
            if not c.get("name"):
                errors.append(f"第{i+1}个维度名称不能为空")
            if not c.get("levels") or len(c.get("levels", [])) < 2:
                errors.append(f"维度「{c.get('name', f'第{i+1}个')}」至少需要2个评分等级")
        
        return {"valid": len(errors) == 0, "errors": errors}


class RubricGradingEngine:
    """基于 Rubric 的评分引擎"""
    
    def __init__(self):
        self.rubrics: Dict[str, Rubric] = {}
        self._load_preset_templates()
    
    def _load_preset_templates(self):
        """加载预设评分标准模板"""
        templates = self._get_preset_templates()
        for template in templates:
            rubric = Rubric(
                name=template["name"],
                subject=template["subject"],
                description=template["description"],
                criteria=template["criteria"]
            )
            rubric.id = template["id"]
            self.rubrics[rubric.id] = rubric
    
    def _get_preset_templates(self) -> List[Dict]:
        """预设模板"""
        return [
            {
                "id": "preset_math_general",
                "name": "数学作业通用评分标准",
                "subject": "math",
                "description": "适用于数学计算题、证明题的通用评分标准",
                "criteria": [
                    {
                        "id": "c1",
                        "name": "答案正确性",
                        "weight": 0.4,
                        "description": "最终答案是否正确",
                        "levels": [
                            {"score": 100, "description": "完全正确"},
                            {"score": 80, "description": "基本正确，有轻微计算错误"},
                            {"score": 60, "description": "思路正确但结果错误"},
                            {"score": 30, "description": "答案错误"}
                        ]
                    },
                    {
                        "id": "c2",
                        "name": "解题过程",
                        "weight": 0.3,
                        "description": "解题步骤是否完整清晰",
                        "levels": [
                            {"score": 100, "description": "步骤完整，逻辑清晰"},
                            {"score": 80, "description": "步骤基本完整，有少量跳跃"},
                            {"score": 60, "description": "步骤不完整，关键步骤缺失"},
                            {"score": 30, "description": "几乎无过程"}
                        ]
                    },
                    {
                        "id": "c3",
                        "name": "方法选择",
                        "weight": 0.2,
                        "description": "是否选择了合适的解题方法",
                        "levels": [
                            {"score": 100, "description": "方法最优，简洁高效"},
                            {"score": 75, "description": "方法合适但不够简洁"},
                            {"score": 50, "description": "方法可行但过于复杂"}
                        ]
                    },
                    {
                        "id": "c4",
                        "name": "表达规范",
                        "weight": 0.1,
                        "description": "数学符号和格式是否规范",
                        "levels": [
                            {"score": 100, "description": "符号规范，格式标准"},
                            {"score": 70, "description": "基本规范，个别不规范"},
                            {"score": 40, "description": "格式混乱"}
                        ]
                    }
                ]
            },
            {
                "id": "preset_chinese_essay",
                "name": "语文作文评分标准",
                "subject": "chinese",
                "description": "适用于语文议论文、记叙文作文评分",
                "criteria": [
                    {
                        "id": "c1",
                        "name": "立意与主题",
                        "weight": 0.3,
                        "description": "文章主题是否明确，立意是否深刻",
                        "levels": [
                            {"score": 100, "description": "立意深刻，主题鲜明"},
                            {"score": 80, "description": "主题明确，立意一般"},
                            {"score": 60, "description": "主题模糊"},
                            {"score": 30, "description": "偏题或无主题"}
                        ]
                    },
                    {
                        "id": "c2",
                        "name": "结构与逻辑",
                        "weight": 0.25,
                        "description": "文章结构是否合理，逻辑是否清晰",
                        "levels": [
                            {"score": 100, "description": "结构严谨，逻辑清晰"},
                            {"score": 80, "description": "结构合理，逻辑通顺"},
                            {"score": 60, "description": "结构松散"},
                            {"score": 30, "description": "结构混乱"}
                        ]
                    },
                    {
                        "id": "c3",
                        "name": "语言表达",
                        "weight": 0.25,
                        "description": "语言是否流畅，用词是否准确",
                        "levels": [
                            {"score": 100, "description": "语言优美，表达精准"},
                            {"score": 80, "description": "语言流畅，表达清晰"},
                            {"score": 60, "description": "语言基本通顺"},
                            {"score": 30, "description": "语病较多"}
                        ]
                    },
                    {
                        "id": "c4",
                        "name": "素材与论证",
                        "weight": 0.2,
                        "description": "素材是否丰富，论证是否有力",
                        "levels": [
                            {"score": 100, "description": "素材丰富，论证有力"},
                            {"score": 75, "description": "有素材，论证基本充分"},
                            {"score": 50, "description": "素材单一，论证不足"}
                        ]
                    }
                ]
            },
            {
                "id": "preset_programming",
                "name": "编程作业评分标准",
                "subject": "programming",
                "description": "适用于Python/Java等编程作业评分",
                "criteria": [
                    {
                        "id": "c1",
                        "name": "功能正确性",
                        "weight": 0.4,
                        "description": "代码是否能正确实现需求",
                        "levels": [
                            {"score": 100, "description": "功能完全正确"},
                            {"score": 80, "description": "基本功能正确，边界情况有误"},
                            {"score": 60, "description": "部分功能正确"},
                            {"score": 20, "description": "功能未实现"}
                        ]
                    },
                    {
                        "id": "c2",
                        "name": "代码质量",
                        "weight": 0.25,
                        "description": "代码结构、命名、注释",
                        "levels": [
                            {"score": 100, "description": "结构清晰，命名规范，注释完整"},
                            {"score": 75, "description": "结构合理，有基本注释"},
                            {"score": 50, "description": "结构一般，缺少注释"},
                            {"score": 25, "description": "结构混乱"}
                        ]
                    },
                    {
                        "id": "c3",
                        "name": "算法效率",
                        "weight": 0.2,
                        "description": "时间/空间复杂度是否合理",
                        "levels": [
                            {"score": 100, "description": "最优复杂度"},
                            {"score": 75, "description": "复杂度合理"},
                            {"score": 50, "description": "复杂度偏高"}
                        ]
                    },
                    {
                        "id": "c4",
                        "name": "异常处理",
                        "weight": 0.15,
                        "description": "是否考虑异常和边界情况",
                        "levels": [
                            {"score": 100, "description": "异常处理完善"},
                            {"score": 70, "description": "有基本异常处理"},
                            {"score": 30, "description": "无异常处理"}
                        ]
                    }
                ]
            },
            {
                "id": "preset_english_writing",
                "name": "英语作文评分标准",
                "subject": "english",
                "description": "适用于英语议论文、说明文写作评分",
                "criteria": [
                    {
                        "id": "c1",
                        "name": "Content & Ideas",
                        "weight": 0.3,
                        "description": "内容是否充实，观点是否明确",
                        "levels": [
                            {"score": 100, "description": "Excellent ideas, well-developed"},
                            {"score": 80, "description": "Good ideas, adequately developed"},
                            {"score": 60, "description": "Limited ideas"},
                            {"score": 30, "description": "Off-topic or irrelevant"}
                        ]
                    },
                    {
                        "id": "c2",
                        "name": "Organization",
                        "weight": 0.25,
                        "description": "文章组织和结构",
                        "levels": [
                            {"score": 100, "description": "Well-organized, clear structure"},
                            {"score": 75, "description": "Generally organized"},
                            {"score": 50, "description": "Poorly organized"}
                        ]
                    },
                    {
                        "id": "c3",
                        "name": "Language Use",
                        "weight": 0.25,
                        "description": "语法、词汇使用",
                        "levels": [
                            {"score": 100, "description": "Excellent grammar and vocabulary"},
                            {"score": 75, "description": "Good language use, minor errors"},
                            {"score": 50, "description": "Frequent errors"}
                        ]
                    },
                    {
                        "id": "c4",
                        "name": "Mechanics",
                        "weight": 0.2,
                        "description": "拼写、标点、格式",
                        "levels": [
                            {"score": 100, "description": "Perfect mechanics"},
                            {"score": 70, "description": "Minor errors"},
                            {"score": 40, "description": "Numerous errors"}
                        ]
                    }
                ]
            }
        ]
    
    # ==================== CRUD 操作 ====================
    
    def create_rubric(self, name: str, subject: str, description: str, criteria: List[Dict]) -> Dict:
        """创建评分标准"""
        rubric = Rubric(name=name, subject=subject, description=description, criteria=criteria)
        
        validation = rubric.validate()
        if not validation["valid"]:
            return {"success": False, "errors": validation["errors"]}
        
        self.rubrics[rubric.id] = rubric
        return {"success": True, "rubric": rubric.to_dict()}
    
    def get_rubric(self, rubric_id: str) -> Optional[Dict]:
        """获取单个评分标准"""
        rubric = self.rubrics.get(rubric_id)
        return rubric.to_dict() if rubric else None
    
    def list_rubrics(self, subject: Optional[str] = None) -> List[Dict]:
        """列出所有评分标准"""
        rubrics = list(self.rubrics.values())
        if subject:
            rubrics = [r for r in rubrics if r.subject == subject]
        return [r.to_dict() for r in rubrics]
    
    def update_rubric(self, rubric_id: str, name: str, subject: str, description: str, criteria: List[Dict]) -> Dict:
        """更新评分标准"""
        rubric = self.rubrics.get(rubric_id)
        if not rubric:
            return {"success": False, "errors": ["评分标准不存在"]}
        
        rubric.name = name
        rubric.subject = subject
        rubric.description = description
        rubric.criteria = criteria
        rubric.updated_at = datetime.now().isoformat()
        
        # 校验
        validation = rubric.validate()
        if not validation["valid"]:
            return {"success": False, "errors": validation["errors"]}
        
        return {"success": True, "rubric": rubric.to_dict()}
    
    def delete_rubric(self, rubric_id: str) -> Dict:
        """删除评分标准"""
        if rubric_id.startswith("preset_"):
            return {"success": False, "errors": ["预设模板不可删除"]}
        
        if rubric_id in self.rubrics:
            del self.rubrics[rubric_id]
            return {"success": True}
        return {"success": False, "errors": ["评分标准不存在"]}
    
    def get_templates(self) -> List[Dict]:
        """获取预设模板列表"""
        return [r.to_dict() for r in self.rubrics.values() if r.id.startswith("preset_")]
    
    def clone_template(self, template_id: str, new_name: str) -> Dict:
        """克隆预设模板为自定义标准"""
        template = self.rubrics.get(template_id)
        if not template:
            return {"success": False, "errors": ["模板不存在"]}
        
        # 深拷贝 criteria
        import copy
        cloned_criteria = copy.deepcopy(template.criteria)
        
        result = self.create_rubric(
            name=new_name,
            subject=template.subject,
            description=template.description,
            criteria=cloned_criteria
        )
        return result
    
    # ==================== 评分引擎 ====================
    
    def grade_with_rubric(self, rubric_id: str, content: str, student_id: str = None) -> Dict:
        """
        使用评分标准批改作业
        
        Args:
            rubric_id: 评分标准ID
            content: 学生作业内容
            student_id: 学生ID（可选）
        
        Returns:
            详细评分结果
        """
        rubric = self.rubrics.get(rubric_id)
        if not rubric:
            return {"success": False, "errors": ["评分标准不存在"]}
        
        criterion_scores = []
        total_score = 0
        
        for criterion in rubric.criteria:
            # 对每个维度进行评分
            level_index, level_score, reasoning = self._evaluate_criterion(
                content, criterion, rubric.subject
            )
            
            weighted_score = level_score * criterion["weight"]
            total_score += weighted_score
            
            selected_level = criterion["levels"][level_index]
            
            criterion_scores.append({
                "criterion_id": criterion["id"],
                "criterion_name": criterion["name"],
                "weight": criterion["weight"],
                "level_index": level_index,
                "level_score": level_score,
                "weighted_score": round(weighted_score, 1),
                "level_description": selected_level["description"],
                "reasoning": reasoning
            })
        
        # 生成总评
        overall_feedback = self._generate_feedback(total_score, criterion_scores, rubric)
        
        return {
            "success": True,
            "rubric_id": rubric_id,
            "rubric_name": rubric.name,
            "student_id": student_id or "anonymous",
            "content_preview": content[:100] + "..." if len(content) > 100 else content,
            "total_score": round(total_score, 1),
            "criterion_scores": criterion_scores,
            "overall_feedback": overall_feedback,
            "graded_at": datetime.now().isoformat()
        }
    
    def _evaluate_criterion(self, content: str, criterion: Dict, subject: str) -> tuple:
        """
        评估单个维度（演示模式：基于内容特征模拟评分）
        
        Returns:
            (level_index, level_score, reasoning)
        """
        levels = criterion["levels"]
        content_len = len(content.strip())
        
        # 基于内容特征的分析
        score = self._analyze_content_quality(content, criterion, subject)
        
        # 匹配到最接近的等级
        best_index = 0
        best_diff = float('inf')
        for i, level in enumerate(levels):
            diff = abs(level["score"] - score)
            if diff < best_diff:
                best_diff = diff
                best_index = i
        
        selected_score = levels[best_index]["score"]
        reasoning = self._generate_criterion_reasoning(criterion, best_index, content, subject)
        
        return best_index, selected_score, reasoning
    
    def _analyze_content_quality(self, content: str, criterion: Dict, subject: str) -> float:
        """分析内容质量，返回0-100的分数（演示模式）"""
        content = content.strip()
        base_score = 75  # 基础分
        
        # 1. 内容长度影响
        if len(content) < 20:
            base_score -= 25
        elif len(content) < 50:
            base_score -= 15
        elif len(content) < 100:
            base_score -= 5
        elif len(content) > 300:
            base_score += 5
        
        # 2. 结构化特征（关键词检测）
        structure_keywords = ["因为", "所以", "因此", "首先", "其次", "最后", "综上", "解", "证明", "答"]
        found_structure = sum(1 for kw in structure_keywords if kw in content)
        base_score += min(found_structure * 3, 12)
        
        # 3. 学科特定特征
        if subject == "math":
            math_patterns = [r'\d+', r'[+\-*/=]', r'[a-zA-Z]\(', r'\therefore', r'\because']
            found_math = sum(1 for p in math_patterns if re.search(p, content))
            base_score += min(found_math * 2, 8)
        elif subject == "programming":
            code_patterns = [r'def\s', r'class\s', r'import\s', r'if\s', r'for\s', r'return\s', r'print\(']
            found_code = sum(1 for p in code_patterns if re.search(p, content))
            base_score += min(found_code * 3, 12)
        elif subject == "chinese":
            if len(content) > 200:
                base_score += 5
            if "。" in content or "！" in content or "？" in content:
                base_score += 3
        elif subject == "english":
            word_count = len(content.split())
            if word_count > 50:
                base_score += 5
            if any(c.isupper() for c in content):
                base_score += 2
        
        # 4. 维度名称匹配
        crit_name = criterion["name"]
        if "正确" in crit_name or "Correct" in crit_name:
            # 正确性维度 - 加入随机性模拟
            base_score += random.randint(-10, 10)
        elif "结构" in crit_name or "Organization" in crit_name or "过程" in crit_name:
            if found_structure > 0:
                base_score += 5
        elif "表达" in crit_name or "Language" in crit_name or "规范" in crit_name or "Mechanics" in crit_name:
            if content.count('\n') > 2:
                base_score += 3
        
        # 添加适度随机性
        base_score += random.randint(-8, 8)
        
        # 限制范围
        return max(20, min(100, base_score))
    
    def _generate_criterion_reasoning(self, criterion: Dict, level_index: int, content: str, subject: str) -> str:
        """生成维度评语"""
        levels = criterion["levels"]
        selected = levels[level_index]
        crit_name = criterion["name"]
        
        reasoning_templates = {
            0: [  # 最高等级
                f"在「{crit_name}」方面表现优秀，{selected['description']}。",
                f"该维度评分理由：学生作业在{crit_name}上展现了较高水平，{selected['description']}。"
            ],
            1: [  # 中上等级
                f"在「{crit_name}」方面表现良好，{selected['description']}。建议进一步提升。",
                f"该维度评分理由：{crit_name}方面整体不错，{selected['description']}。"
            ],
            2: [  # 中下等级
                f"在「{crit_name}」方面有待加强，{selected['description']}。需要重点关注。",
                f"该维度评分理由：{crit_name}存在不足，{selected['description']}。建议针对性练习。"
            ],
            3: [  # 最低等级
                f"在「{crit_name}」方面存在明显不足，{selected['description']}。亟需改进。",
                f"该维度评分理由：{crit_name}方面问题较多，{selected['description']}。"
            ]
        }
        
        templates = reasoning_templates.get(level_index, reasoning_templates[1])
        return random.choice(templates)
    
    def _generate_feedback(self, total_score: float, criterion_scores: List[Dict], rubric: Rubric) -> str:
        """生成总评反馈"""
        # 确定等级
        if total_score >= 90:
            level = "优秀"
            comment = "作业完成质量优秀，各维度均表现突出，继续保持！"
        elif total_score >= 80:
            level = "良好"
            comment = "作业整体质量良好，部分维度仍有提升空间。"
        elif total_score >= 70:
            level = "中等"
            comment = "作业完成度一般，建议重点加强薄弱维度。"
        elif total_score >= 60:
            level = "及格"
            comment = "作业基本合格，但多个维度需要改进。"
        else:
            level = "不及格"
            comment = "作业未达标，建议重新学习相关知识点后重做。"
        
        # 找出最强和最弱的维度
        sorted_criteria = sorted(criterion_scores, key=lambda x: x["level_score"], reverse=True)
        strongest = sorted_criteria[0]
        weakest = sorted_criteria[-1]
        
        feedback = f"""## 评分总览

**总分：{total_score:.1f}分** | **等级：{level}**

{comment}

## 维度得分详情

"""
        for cs in criterion_scores:
            feedback += f"### {cs['criterion_name']}（权重{cs['weight']*100:.0f}%）\n"
            feedback += f"- 得分：{cs['level_score']}分（加权后{cs['weighted_score']}分）\n"
            feedback += f"- 等级：{cs['level_description']}\n"
            feedback += f"- 评语：{cs['reasoning']}\n\n"
        
        feedback += f"""## 改进建议

**优势维度**：{strongest['criterion_name']}（{strongest['level_score']}分）
{strongest['reasoning']}

**薄弱维度**：{weakest['criterion_name']}（{weakest['level_score']}分）
{weakest['reasoning']}

### 下一步学习建议
1. 针对薄弱维度「{weakest['criterion_name']}」进行专项练习
2. 巩固优势维度「{strongest['criterion_name']}」的掌握
3. 参考评分标准中各等级的描述，明确提升方向

---
*本评分基于教师自定义Rubric评分标准「{rubric.name}」自动生成*"""
        
        return feedback


# 全局实例
rubric_engine = RubricGradingEngine()