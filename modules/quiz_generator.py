#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
クイズ生成モジュール
百人一首のクイズ問題を生成する機能を提供
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class QuizType(Enum):
    """クイズタイプ"""
    UPPER_TO_LOWER = "上の句→下の句"
    LOWER_TO_UPPER = "下の句→上の句"
    AUTHOR_TO_POEM = "作者→歌"
    POEM_TO_AUTHOR = "歌→作者"


@dataclass
class QuizQuestion:
    """クイズ問題のデータクラス"""
    poem_number: int
    quiz_type: QuizType
    question_text: str
    choices: List[str]
    correct_answer: str
    correct_answer_index: int
    explanation: str
    difficulty: str
    poem_data: Dict[str, Any]


class QuizGenerator:
    """クイズ問題を生成するクラス"""
    
    def __init__(self, poems_data: List[Dict[str, Any]]):
        """
        初期化
        
        Args:
            poems_data: 百人一首データのリスト
        """
        self.poems_data = poems_data
        self.used_questions: set = set()
        
        # 難易度別に歌を分類
        self.difficulty_poems = {
            'beginner': self._get_beginner_poems(),
            'intermediate': self._get_intermediate_poems(),
            'advanced': self.poems_data  # 全ての歌
        }
    
    def _get_beginner_poems(self) -> List[Dict[str, Any]]:
        """初級レベルの歌を取得（有名な歌）"""
        famous_numbers = [1, 2, 5, 7, 9, 13, 17, 20, 23, 24, 
                         33, 35, 43, 48, 51, 57, 66, 77, 83, 99]
        return [p for p in self.poems_data 
                if p.get('number', p.get('id', 0)) in famous_numbers]
    
    def _get_intermediate_poems(self) -> List[Dict[str, Any]]:
        """中級レベルの歌を取得"""
        return [p for p in self.poems_data 
                if 21 <= p.get('number', p.get('id', 0)) <= 60]
    
    def generate_question(self,
                         quiz_type: QuizType = QuizType.UPPER_TO_LOWER,
                         difficulty: str = "beginner",
                         exclude_numbers: List[int] = None) -> Optional[QuizQuestion]:
        """
        クイズ問題を生成
        
        Args:
            quiz_type: クイズタイプ
            difficulty: 難易度
            exclude_numbers: 除外する歌番号のリスト
            
        Returns:
            生成されたクイズ問題
        """
        # 利用可能な歌を取得
        available_poems = self.difficulty_poems.get(difficulty, self.poems_data).copy()
        
        # 除外する歌を削除
        if exclude_numbers:
            available_poems = [p for p in available_poems 
                             if p.get('number', p.get('id', 0)) not in exclude_numbers]
        
        # 使用済みの問題を除外
        question_ids = [f"{p.get('number', p.get('id', 0))}_{quiz_type.value}" 
                       for p in available_poems]
        available_poems = [p for i, p in enumerate(available_poems) 
                          if question_ids[i] not in self.used_questions]
        
        if not available_poems:
            return None
        
        # ランダムに歌を選択
        poem_data = random.choice(available_poems)
        poem_number = poem_data.get('number', poem_data.get('id', 0))
        
        # クイズタイプに応じて問題を生成
        if quiz_type == QuizType.UPPER_TO_LOWER:
            question = self._generate_upper_to_lower(poem_data)
        elif quiz_type == QuizType.LOWER_TO_UPPER:
            question = self._generate_lower_to_upper(poem_data)
        elif quiz_type == QuizType.AUTHOR_TO_POEM:
            question = self._generate_author_to_poem(poem_data)
        elif quiz_type == QuizType.POEM_TO_AUTHOR:
            question = self._generate_poem_to_author(poem_data)
        else:
            return None
        
        # 解説を生成（descriptionフィールドと全文を含む）
        explanation = self._generate_explanation(poem_data, quiz_type)
        
        # 問題を使用済みに追加
        question_id = f"{poem_number}_{quiz_type.value}"
        self.used_questions.add(question_id)
        
        return QuizQuestion(
            poem_number=poem_number,
            quiz_type=quiz_type,
            question_text=question['question'],
            choices=question['choices'],
            correct_answer=question['correct'],
            correct_answer_index=question['correct_index'],
            explanation=explanation,
            difficulty=difficulty,
            poem_data=poem_data
        )
    
    def _generate_upper_to_lower(self, poem_data: Dict[str, Any]) -> Dict[str, Any]:
        """上の句から下の句を答える問題を生成"""
        question = poem_data['upper']
        correct = poem_data['lower']
        
        # 他の歌から間違い選択肢を生成
        wrong_choices = []
        other_poems = [p for p in self.poems_data 
                      if p.get('number', p.get('id', 0)) != poem_data.get('number', poem_data.get('id', 0))]
        
        while len(wrong_choices) < 3 and other_poems:
            wrong_poem = random.choice(other_poems)
            wrong_answer = wrong_poem['lower']
            if wrong_answer not in wrong_choices and wrong_answer != correct:
                wrong_choices.append(wrong_answer)
            other_poems.remove(wrong_poem)
        
        # 選択肢をシャッフル
        choices = wrong_choices + [correct]
        random.shuffle(choices)
        
        return {
            'question': question,
            'choices': choices,
            'correct': correct,
            'correct_index': choices.index(correct)
        }
    
    def _generate_lower_to_upper(self, poem_data: Dict[str, Any]) -> Dict[str, Any]:
        """下の句から上の句を答える問題を生成"""
        question = poem_data['lower']
        correct = poem_data['upper']
        
        # 他の歌から間違い選択肢を生成
        wrong_choices = []
        other_poems = [p for p in self.poems_data 
                      if p.get('number', p.get('id', 0)) != poem_data.get('number', poem_data.get('id', 0))]
        
        while len(wrong_choices) < 3 and other_poems:
            wrong_poem = random.choice(other_poems)
            wrong_answer = wrong_poem['upper']
            if wrong_answer not in wrong_choices and wrong_answer != correct:
                wrong_choices.append(wrong_answer)
            other_poems.remove(wrong_poem)
        
        # 選択肢をシャッフル
        choices = wrong_choices + [correct]
        random.shuffle(choices)
        
        return {
            'question': question,
            'choices': choices,
            'correct': correct,
            'correct_index': choices.index(correct)
        }
    
    def _generate_author_to_poem(self, poem_data: Dict[str, Any]) -> Dict[str, Any]:
        """作者から歌を答える問題を生成"""
        question = f"「{poem_data['author']}」が詠んだ歌は？"
        correct = f"{poem_data['upper']} {poem_data['lower']}"
        
        # 他の歌から間違い選択肢を生成
        wrong_choices = []
        other_poems = [p for p in self.poems_data 
                      if p.get('number', p.get('id', 0)) != poem_data.get('number', poem_data.get('id', 0))]
        
        while len(wrong_choices) < 3 and other_poems:
            wrong_poem = random.choice(other_poems)
            wrong_answer = f"{wrong_poem['upper']} {wrong_poem['lower']}"
            if wrong_answer not in wrong_choices:
                wrong_choices.append(wrong_answer)
            other_poems.remove(wrong_poem)
        
        # 選択肢をシャッフル
        choices = wrong_choices + [correct]
        random.shuffle(choices)
        
        return {
            'question': question,
            'choices': choices,
            'correct': correct,
            'correct_index': choices.index(correct)
        }
    
    def _generate_poem_to_author(self, poem_data: Dict[str, Any]) -> Dict[str, Any]:
        """歌から作者を答える問題を生成"""
        question = f"{poem_data['upper']} {poem_data['lower']}"
        correct = poem_data['author']
        
        # 他の作者から間違い選択肢を生成
        all_authors = list(set(p['author'] for p in self.poems_data))
        wrong_choices = []
        
        while len(wrong_choices) < 3:
            wrong_author = random.choice(all_authors)
            if wrong_author != correct and wrong_author not in wrong_choices:
                wrong_choices.append(wrong_author)
        
        # 選択肢をシャッフル
        choices = wrong_choices + [correct]
        random.shuffle(choices)
        
        return {
            'question': question,
            'choices': choices,
            'correct': correct,
            'correct_index': choices.index(correct)
        }
    
    def _generate_explanation(self, poem_data: Dict[str, Any], quiz_type: QuizType) -> str:
        """
        問題の解説を生成
        
        Args:
            poem_data: 歌データ
            quiz_type: クイズタイプ
            
        Returns:
            解説文
        """
        # 歌番号を取得（idまたはnumber）
        poem_number = poem_data.get('number', poem_data.get('id', '不明'))
        
        # 全文（上の句 + 下の句）
        full_poem = f"{poem_data['upper']} {poem_data['lower']}"
        
        # 基本情報
        explanation_parts = [
            f"【歌番号】{poem_number}番",
            f"【作者】{poem_data['author']}",
            "",
            "【全文】",
            full_poem,
            ""
        ]
        
        # 読みがある場合
        if poem_data.get('reading'):
            explanation_parts.extend([
                "【読み】",
                poem_data['reading'],
                ""
            ])
        
        # 現代語訳がある場合
        if poem_data.get('translation'):
            explanation_parts.extend([
                "【現代語訳】",
                poem_data['translation'],
                ""
            ])
        
        # descriptionフィールドがある場合
        if poem_data.get('description'):
            explanation_parts.extend([
                "【解説】",
                poem_data['description'],
                ""
            ])
        
        # その他の情報がある場合
        additional_info = []
        
        # 季節
        if poem_data.get('season'):
            additional_info.append(f"季節: {poem_data['season']}")
        
        # 主題
        if poem_data.get('theme'):
            additional_info.append(f"主題: {poem_data['theme']}")
        
        # 修辞技法
        if poem_data.get('technique'):
            additional_info.append(f"技法: {poem_data['technique']}")
        
        # 出典
        if poem_data.get('source'):
            additional_info.append(f"出典: {poem_data['source']}")
        
        if additional_info:
            explanation_parts.extend([
                "【その他の情報】",
                " / ".join(additional_info),
                ""
            ])
        
        # クイズタイプに応じた追加説明
        if quiz_type == QuizType.UPPER_TO_LOWER:
            explanation_parts.append("※この歌は上の句から下の句を導く問題でした。")
        elif quiz_type == QuizType.LOWER_TO_UPPER:
            explanation_parts.append("※この歌は下の句から上の句を導く問題でした。")
        elif quiz_type == QuizType.AUTHOR_TO_POEM:
            explanation_parts.append(f"※この歌の作者は「{poem_data['author']}」です。")
        elif quiz_type == QuizType.POEM_TO_AUTHOR:
            explanation_parts.append(f"※この歌を詠んだのは「{poem_data['author']}」です。")
        
        return "\n".join(explanation_parts)
    
    def get_random_questions(self,
                            count: int = 10,
                            quiz_type: QuizType = None,
                            difficulty: str = "beginner") -> List[QuizQuestion]:
        """
        複数のランダムな問題を生成
        
        Args:
            count: 生成する問題数
            quiz_type: クイズタイプ（Noneの場合はランダム）
            difficulty: 難易度
            
        Returns:
            生成された問題のリスト
        """
        questions = []
        exclude_numbers = []
        
        for _ in range(count):
            # クイズタイプをランダムに選択（指定がない場合）
            current_type = quiz_type or random.choice(list(QuizType))
            
            # 問題を生成
            question = self.generate_question(
                quiz_type=current_type,
                difficulty=difficulty,
                exclude_numbers=exclude_numbers
            )
            
            if question:
                questions.append(question)
                exclude_numbers.append(question.poem_number)
            else:
                break  # 生成できる問題がなくなった
        
        return questions
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        return {
            'available_questions': len(self.poems_data),
            'used_questions': len(self.used_questions),
            'quiz_types': [t.value for t in QuizType],
            'difficulty_levels': list(self.difficulty_poems.keys())
        }
    
    def reset_used_questions(self):
        """使用済み問題をリセット"""
        self.used_questions.clear()


# ユーティリティ関数
def create_quiz_generator(poems_data: List[Dict[str, Any]]) -> QuizGenerator:
    """
    QuizGeneratorインスタンスを作成
    
    Args:
        poems_data: 歌データのリスト
        
    Returns:
        QuizGeneratorインスタンス
    """
    return QuizGenerator(poems_data)