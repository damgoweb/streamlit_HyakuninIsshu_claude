"""
百人一首クイズ回答判定機能
タスク1-5: 回答判定機能実装

このモジュールは以下の機能を提供します:
- check_answer() - 正誤判定機能
- スコア計算ロジック
- 回答履歴記録機能
- 判定結果の状態更新
- 統計情報の計算
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnswerStatus(Enum):
    """回答状態を定義"""
    CORRECT = "correct"           # 正解
    INCORRECT = "incorrect"       # 不正解
    SKIPPED = "skipped"          # スキップ
    TIMEOUT = "timeout"          # タイムアウト
    HINT_USED = "hint_used"      # ヒント使用後正解


@dataclass
class AnswerResult:
    """回答結果を表すデータクラス"""
    question_id: str                    # 問題ID (poem_number_quiz_type)
    poem_number: int                    # 歌番号
    question_text: str                  # 問題文
    correct_answer: str                 # 正解
    user_answer: Optional[str]          # ユーザーの回答
    answer_index: Optional[int]         # 選択肢のインデックス
    correct_index: int                  # 正解のインデックス
    status: AnswerStatus               # 回答状態
    time_taken: float                  # 回答時間（秒）
    hint_used: bool                    # ヒント使用フラグ
    timestamp: datetime                # 回答日時
    confidence_score: Optional[float] = None  # 信頼度スコア（将来の拡張用）
    
    @property
    def is_correct(self) -> bool:
        """正解かどうかを返す"""
        return self.status in [AnswerStatus.CORRECT, AnswerStatus.HINT_USED]
    
    @property
    def points(self) -> float:
        """獲得ポイントを計算"""
        if self.status == AnswerStatus.CORRECT:
            # 完全正解: 1.0ポイント
            base_points = 1.0
            
            # 回答時間ボーナス（5秒以内で追加ポイント）
            if self.time_taken <= 5.0:
                time_bonus = (5.0 - self.time_taken) * 0.1
                return min(base_points + time_bonus, 1.5)
            
            return base_points
            
        elif self.status == AnswerStatus.HINT_USED:
            # ヒント使用正解: 0.7ポイント
            return 0.7
            
        else:
            # 不正解、スキップ、タイムアウト: 0ポイント
            return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'question_id': self.question_id,
            'poem_number': self.poem_number,
            'question_text': self.question_text,
            'correct_answer': self.correct_answer,
            'user_answer': self.user_answer,
            'answer_index': self.answer_index,
            'correct_index': self.correct_index,
            'status': self.status.value,
            'is_correct': self.is_correct,
            'time_taken': self.time_taken,
            'hint_used': self.hint_used,
            'points': self.points,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class QuizStatistics:
    """クイズ統計情報"""
    total_questions: int = 0
    correct_answers: int = 0
    incorrect_answers: int = 0
    skipped_answers: int = 0
    timeout_answers: int = 0
    hint_used_count: int = 0
    total_time: float = 0.0
    total_points: float = 0.0
    answer_results: List[AnswerResult] = field(default_factory=list)
    
    @property
    def accuracy(self) -> float:
        """正答率を計算"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100
    
    @property
    def average_time(self) -> float:
        """平均回答時間を計算"""
        if self.total_questions == 0:
            return 0.0
        return self.total_time / self.total_questions
    
    @property
    def average_points(self) -> float:
        """平均獲得ポイントを計算"""
        if self.total_questions == 0:
            return 0.0
        return self.total_points / self.total_questions
    
    def get_wrong_poem_numbers(self) -> List[int]:
        """間違えた問題の歌番号リストを返す"""
        return [result.poem_number for result in self.answer_results if not result.is_correct]
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """パフォーマンス分析を返す"""
        analysis = {
            'overall_grade': self._calculate_grade(),
            'time_performance': self._analyze_time_performance(),
            'difficulty_analysis': self._analyze_difficulty(),
            'improvement_suggestions': self._generate_suggestions()
        }
        return analysis
    
    def _calculate_grade(self) -> str:
        """成績評価を計算"""
        if self.accuracy >= 95:
            return "S"
        elif self.accuracy >= 90:
            return "A+"
        elif self.accuracy >= 85:
            return "A"
        elif self.accuracy >= 80:
            return "B+"
        elif self.accuracy >= 75:
            return "B"
        elif self.accuracy >= 70:
            return "C+"
        elif self.accuracy >= 65:
            return "C"
        elif self.accuracy >= 60:
            return "D"
        else:
            return "F"
    
    def _analyze_time_performance(self) -> Dict[str, Any]:
        """時間パフォーマンスを分析"""
        if not self.answer_results:
            return {}
        
        times = [r.time_taken for r in self.answer_results if r.time_taken > 0]
        if not times:
            return {}
        
        return {
            'fastest_answer': min(times),
            'slowest_answer': max(times),
            'average_time': sum(times) / len(times),
            'quick_answers': len([t for t in times if t <= 5.0]),
            'slow_answers': len([t for t in times if t > 15.0])
        }
    
    def _analyze_difficulty(self) -> Dict[str, Any]:
        """難易度別の成績を分析"""
        # 簡易的な難易度分析（歌番号ベース）
        beginner_results = [r for r in self.answer_results if r.poem_number <= 50]
        intermediate_results = [r for r in self.answer_results if 51 <= r.poem_number <= 80]
        advanced_results = [r for r in self.answer_results if r.poem_number > 80]
        
        def calc_accuracy(results):
            if not results:
                return 0.0
            correct = len([r for r in results if r.is_correct])
            return (correct / len(results)) * 100
        
        return {
            'beginner_accuracy': calc_accuracy(beginner_results),
            'intermediate_accuracy': calc_accuracy(intermediate_results),
            'advanced_accuracy': calc_accuracy(advanced_results),
            'beginner_count': len(beginner_results),
            'intermediate_count': len(intermediate_results),
            'advanced_count': len(advanced_results)
        }
    
    def _generate_suggestions(self) -> List[str]:
        """改善提案を生成"""
        suggestions = []
        
        if self.accuracy < 70:
            suggestions.append("基本的な有名歌から復習することをお勧めします")
        
        if self.average_time > 10.0:
            suggestions.append("歌の暗記練習で回答時間を短縮しましょう")
        
        if self.hint_used_count > self.total_questions * 0.5:
            suggestions.append("ヒントに頼らず、まず自力で考える練習をしましょう")
        
        if self.skipped_answers > self.total_questions * 0.3:
            suggestions.append("分からない問題でも推測で回答してみましょう")
        
        wrong_poems = self.get_wrong_poem_numbers()
        if len(wrong_poems) > 0:
            suggestions.append(f"間違えた{len(wrong_poems)}首を重点的に復習しましょう")
        
        return suggestions


class AnswerValidator:
    """
    回答判定クラス
    
    主な機能:
    - 回答の正誤判定
    - スコア計算
    - 統計情報の管理
    - 回答履歴の記録
    """
    
    def __init__(self):
        """初期化"""
        self.statistics = QuizStatistics()
        self.session_start_time = time.time()
        logger.info("AnswerValidator initialized")
    
    def check_answer(
        self,
        question_id: str,
        poem_number: int,
        question_text: str,
        correct_answer: str,
        correct_index: int,
        user_answer: Optional[str] = None,
        answer_index: Optional[int] = None,
        time_taken: float = 0.0,
        hint_used: bool = False,
        timeout_seconds: Optional[float] = None
    ) -> AnswerResult:
        """
        回答を判定し、結果を返す
        
        Args:
            question_id: 問題ID
            poem_number: 歌番号
            question_text: 問題文
            correct_answer: 正解テキスト
            correct_index: 正解のインデックス
            user_answer: ユーザーの回答テキスト
            answer_index: ユーザーが選択したインデックス
            time_taken: 回答時間（秒）
            hint_used: ヒントを使用したかどうか
            timeout_seconds: タイムアウト時間
            
        Returns:
            AnswerResult: 判定結果
        """
        try:
            # 回答状態を判定
            status = self._determine_answer_status(
                correct_answer, correct_index, user_answer, answer_index,
                hint_used, timeout_seconds, time_taken
            )
            
            # 結果オブジェクトを作成
            result = AnswerResult(
                question_id=question_id,
                poem_number=poem_number,
                question_text=question_text,
                correct_answer=correct_answer,
                user_answer=user_answer,
                answer_index=answer_index,
                correct_index=correct_index,
                status=status,
                time_taken=time_taken,
                hint_used=hint_used,
                timestamp=datetime.now()
            )
            
            # 統計情報を更新
            self._update_statistics(result)
            
            logger.info(f"Answer validated: {question_id} - {status.value} - {time_taken:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in answer validation: {e}")
            # エラー時はデフォルト結果を返す
            return AnswerResult(
                question_id=question_id,
                poem_number=poem_number,
                question_text=question_text,
                correct_answer=correct_answer,
                user_answer=user_answer,
                answer_index=answer_index,
                correct_index=correct_index,
                status=AnswerStatus.INCORRECT,
                time_taken=time_taken,
                hint_used=hint_used,
                timestamp=datetime.now()
            )
    
    def _determine_answer_status(
        self,
        correct_answer: str,
        correct_index: int,
        user_answer: Optional[str],
        answer_index: Optional[int],
        hint_used: bool,
        timeout_seconds: Optional[float],
        time_taken: float
    ) -> AnswerStatus:
        """回答状態を判定"""
        
        # タイムアウトチェック
        if timeout_seconds and time_taken >= timeout_seconds:
            return AnswerStatus.TIMEOUT
        
        # スキップチェック
        if user_answer is None and answer_index is None:
            return AnswerStatus.SKIPPED
        
        # 正誤判定
        is_correct = False
        
        # インデックスベースの判定を優先
        if answer_index is not None:
            is_correct = answer_index == correct_index
        # テキストベースの判定（バックアップ）
        elif user_answer is not None:
            is_correct = self._compare_answers(correct_answer, user_answer)
        
        # 結果の決定
        if is_correct:
            return AnswerStatus.HINT_USED if hint_used else AnswerStatus.CORRECT
        else:
            return AnswerStatus.INCORRECT
    
    def _compare_answers(self, correct: str, user: str) -> bool:
        """
        回答テキストを比較（柔軟な比較）
        
        Args:
            correct: 正解テキスト
            user: ユーザーの回答
            
        Returns:
            bool: 一致するかどうか
        """
        if not correct or not user:
            return False
        
        # 正規化処理
        correct_normalized = self._normalize_text(correct)
        user_normalized = self._normalize_text(user)
        
        # 完全一致
        if correct_normalized == user_normalized:
            return True
        
        # 部分一致（90%以上の類似度）
        similarity = self._calculate_similarity(correct_normalized, user_normalized)
        return similarity >= 0.9
    
    def _normalize_text(self, text: str) -> str:
        """テキストを正規化"""
        if not text:
            return ""
        
        # 空白、記号を除去し、小文字に変換
        import re
        normalized = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', text)
        return normalized.lower().strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """文字列類似度を計算（簡易版）"""
        if not text1 or not text2:
            return 0.0
        
        # 長い方の文字列を基準にした類似度計算
        longer = text1 if len(text1) >= len(text2) else text2
        shorter = text2 if len(text1) >= len(text2) else text1
        
        if len(longer) == 0:
            return 1.0
        
        # 共通文字数をカウント
        common_chars = 0
        for char in shorter:
            if char in longer:
                common_chars += 1
        
        return common_chars / len(longer)
    
    def _update_statistics(self, result: AnswerResult) -> None:
        """統計情報を更新"""
        self.statistics.total_questions += 1
        self.statistics.total_time += result.time_taken
        self.statistics.total_points += result.points
        
        if result.status == AnswerStatus.CORRECT:
            self.statistics.correct_answers += 1
        elif result.status == AnswerStatus.HINT_USED:
            self.statistics.correct_answers += 1
            self.statistics.hint_used_count += 1
        elif result.status == AnswerStatus.INCORRECT:
            self.statistics.incorrect_answers += 1
        elif result.status == AnswerStatus.SKIPPED:
            self.statistics.skipped_answers += 1
        elif result.status == AnswerStatus.TIMEOUT:
            self.statistics.timeout_answers += 1
        
        if result.hint_used:
            self.statistics.hint_used_count += 1
        
        # 結果を履歴に追加
        self.statistics.answer_results.append(result)
    
    def get_statistics(self) -> QuizStatistics:
        """統計情報を取得"""
        return self.statistics
    
    def get_current_score(self) -> Dict[str, Any]:
        """現在のスコア情報を取得"""
        return {
            'total_questions': self.statistics.total_questions,
            'correct_answers': self.statistics.correct_answers,
            'accuracy': self.statistics.accuracy,
            'total_points': self.statistics.total_points,
            'average_points': self.statistics.average_points,
            'grade': self.statistics._calculate_grade()
        }
    
    def get_question_result(self, question_id: str) -> Optional[AnswerResult]:
        """特定の問題の結果を取得"""
        for result in self.statistics.answer_results:
            if result.question_id == question_id:
                return result
        return None
    
    def get_results_by_status(self, status: AnswerStatus) -> List[AnswerResult]:
        """指定した状態の結果一覧を取得"""
        return [result for result in self.statistics.answer_results if result.status == status]
    
    def get_wrong_answers(self) -> List[AnswerResult]:
        """間違えた問題の結果一覧を取得"""
        return [result for result in self.statistics.answer_results if not result.is_correct]
    
    def reset_statistics(self) -> None:
        """統計情報をリセット"""
        self.statistics = QuizStatistics()
        self.session_start_time = time.time()
        logger.info("Statistics reset")
    
    def export_results(self) -> Dict[str, Any]:
        """結果をエクスポート用形式で取得"""
        return {
            'session_info': {
                'start_time': self.session_start_time,
                'duration': time.time() - self.session_start_time,
                'total_questions': self.statistics.total_questions
            },
            'statistics': {
                'accuracy': self.statistics.accuracy,
                'average_time': self.statistics.average_time,
                'total_points': self.statistics.total_points,
                'grade': self.statistics._calculate_grade()
            },
            'performance_analysis': self.statistics.get_performance_analysis(),
            'detailed_results': [result.to_dict() for result in self.statistics.answer_results]
        }


# 使用例とテスト関数
def test_answer_validator():
    """AnswerValidatorのテスト関数"""
    
    print("=== AnswerValidator Test ===")
    
    # バリデータを初期化
    validator = AnswerValidator()
    
    # テストケース1: 正解
    result1 = validator.check_answer(
        question_id="1_upper_to_lower",
        poem_number=1,
        question_text="あきの田の",
        correct_answer="かりほの庵の苫をあらみ",
        correct_index=0,
        user_answer="かりほの庵の苫をあらみ",
        answer_index=0,
        time_taken=3.5,
        hint_used=False
    )
    
    print(f"Test 1 - Correct: {result1.status.value}, Points: {result1.points}")
    
    # テストケース2: 不正解
    result2 = validator.check_answer(
        question_id="2_upper_to_lower",
        poem_number=2,
        question_text="春すぎて",
        correct_answer="夏来にけらし白妙の",
        correct_index=1,
        user_answer="違う回答",
        answer_index=2,
        time_taken=5.0,
        hint_used=False
    )
    
    print(f"Test 2 - Incorrect: {result2.status.value}, Points: {result2.points}")
    
    # テストケース3: ヒント使用正解
    result3 = validator.check_answer(
        question_id="3_upper_to_lower",
        poem_number=3,
        question_text="あしびきの",
        correct_answer="山鳥の尾のしだり尾の",
        correct_index=2,
        user_answer="山鳥の尾のしだり尾の",
        answer_index=2,
        time_taken=8.0,
        hint_used=True
    )
    
    print(f"Test 3 - Hint Used: {result3.status.value}, Points: {result3.points}")
    
    # 統計情報の確認
    stats = validator.get_statistics()
    print(f"\n=== Statistics ===")
    print(f"Total Questions: {stats.total_questions}")
    print(f"Correct Answers: {stats.correct_answers}")
    print(f"Accuracy: {stats.accuracy:.1f}%")
    print(f"Total Points: {stats.total_points:.1f}")
    print(f"Grade: {stats._calculate_grade()}")
    
    # 現在のスコア
    score = validator.get_current_score()
    print(f"\n=== Current Score ===")
    print(f"Score: {score}")
    
    # パフォーマンス分析
    analysis = stats.get_performance_analysis()
    print(f"\n=== Performance Analysis ===")
    print(f"Overall Grade: {analysis['overall_grade']}")
    print(f"Suggestions: {analysis['improvement_suggestions']}")


if __name__ == "__main__":
    test_answer_validator()