"""
百人一首クイズアプリ - セッション状態管理モジュール
アプリケーションの状態管理、画面遷移、データ永続化を担当
"""

import streamlit as st
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

# ログ設定
logger = logging.getLogger(__name__)

class ScreenType(Enum):
    """画面タイプの定義"""
    START = "start"
    QUIZ = "quiz"
    RESULT = "result"
    SETTINGS = "settings"
    REVIEW = "review"

class QuizMode(Enum):
    """クイズモードの定義"""
    UPPER_TO_LOWER = "upper_to_lower"  # 上の句→下の句
    LOWER_TO_UPPER = "lower_to_upper"  # 下の句→上の句
    AUTHOR_TO_POEM = "author_to_poem"  # 作者→歌
    POEM_TO_AUTHOR = "poem_to_author"  # 歌→作者

class Difficulty(Enum):
    """難易度の定義"""
    BEGINNER = "beginner"    # 初級（有名な歌）
    INTERMEDIATE = "intermediate"  # 中級
    ADVANCED = "advanced"    # 上級（マイナーな歌）

@dataclass
class QuizSettings:
    """クイズ設定のデータクラス"""
    mode: QuizMode = QuizMode.UPPER_TO_LOWER
    difficulty: Difficulty = Difficulty.BEGINNER
    total_questions: int = 10
    enable_hints: bool = True
    show_explanations: bool = True
    time_limit: Optional[int] = None  # 秒単位、Noneは無制限

@dataclass
class QuestionResult:
    """問題の結果データクラス"""
    poem_number: int
    question: str
    correct_answer: str
    user_answer: Optional[str]
    is_correct: bool
    time_taken: Optional[float] = None
    used_hint: bool = False

@dataclass
class QuizSession:
    """クイズセッションのデータクラス"""
    session_id: str
    start_time: datetime = field(default_factory=datetime.now)
    settings: QuizSettings = field(default_factory=QuizSettings)
    current_question: int = 0
    score: int = 0
    results: List[QuestionResult] = field(default_factory=list)
    wrong_answers: List[int] = field(default_factory=list)  # 間違えた歌番号
    question_pool: List[int] = field(default_factory=list)  # 出題する歌番号
    is_completed: bool = False

class SessionManager:
    """セッション状態管理クラス"""
    
    # セッションステートのキー定義
    KEYS = {
        'initialized': 'session_initialized',
        'current_screen': 'current_screen',
        'quiz_session': 'quiz_session',
        'data_manager': 'data_manager',
        'current_poem': 'current_poem',
        'choices': 'current_choices',
        'answered': 'question_answered',
        'user_answer': 'user_answer',
        'show_result': 'show_question_result'
    }
    
    def __init__(self):
        """初期化"""
        self.session_id = self._generate_session_id()
    
    @staticmethod
    def _generate_session_id() -> str:
        """セッションIDの生成"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def initialize_session(self) -> None:
        """
        セッションステートの初期化
        アプリケーション開始時に一度だけ実行
        """
        if not self._is_initialized():
            logger.info("セッションを初期化しています...")
            
            # 基本的な状態初期化
            st.session_state[self.KEYS['initialized']] = True
            st.session_state[self.KEYS['current_screen']] = ScreenType.START.value
            st.session_state[self.KEYS['data_manager']] = None
            
            # クイズセッション初期化
            quiz_session = QuizSession(session_id=self.session_id)
            st.session_state[self.KEYS['quiz_session']] = quiz_session
            
            # 問題関連の状態初期化
            st.session_state[self.KEYS['current_poem']] = None
            st.session_state[self.KEYS['choices']] = []
            st.session_state[self.KEYS['answered']] = False
            st.session_state[self.KEYS['user_answer']] = None
            st.session_state[self.KEYS['show_result']] = False
            
            logger.info(f"セッション初期化完了 - ID: {self.session_id}")
    
    def _is_initialized(self) -> bool:
        """セッションが初期化済みかチェック"""
        return self.KEYS['initialized'] in st.session_state and \
               st.session_state[self.KEYS['initialized']]
    
    def get_current_screen(self) -> ScreenType:
        """現在の画面タイプを取得"""
        screen_value = st.session_state.get(self.KEYS['current_screen'], ScreenType.START.value)
        try:
            return ScreenType(screen_value)
        except ValueError:
            logger.warning(f"不正な画面タイプ: {screen_value}")
            return ScreenType.START
    
    def set_current_screen(self, screen: ScreenType) -> None:
        """現在の画面タイプを設定"""
        logger.info(f"画面遷移: {self.get_current_screen().value} -> {screen.value}")
        st.session_state[self.KEYS['current_screen']] = screen.value
    
    def get_quiz_session(self) -> QuizSession:
        """現在のクイズセッションを取得"""
        return st.session_state.get(self.KEYS['quiz_session'])
    
    def update_quiz_settings(self, **kwargs) -> None:
        """クイズ設定を更新"""
        quiz_session = self.get_quiz_session()
        if quiz_session:
            for key, value in kwargs.items():
                if hasattr(quiz_session.settings, key):
                    setattr(quiz_session.settings, key, value)
                    logger.info(f"設定更新: {key} = {value}")
    
    def start_new_quiz(self, settings: Optional[QuizSettings] = None) -> None:
        """新しいクイズを開始"""
        quiz_session = self.get_quiz_session()
        if quiz_session:
            # 設定を更新
            if settings:
                quiz_session.settings = settings
            
            # セッション状態をリセット
            quiz_session.current_question = 0
            quiz_session.score = 0
            quiz_session.results = []
            quiz_session.wrong_answers = []
            quiz_session.question_pool = []
            quiz_session.is_completed = False
            quiz_session.start_time = datetime.now()
            
            # 問題関連の状態リセット
            st.session_state[self.KEYS['current_poem']] = None
            st.session_state[self.KEYS['choices']] = []
            st.session_state[self.KEYS['answered']] = False
            st.session_state[self.KEYS['user_answer']] = None
            st.session_state[self.KEYS['show_result']] = False
            
            logger.info("新しいクイズセッションを開始")
    
    def reset_quiz(self) -> None:
        """クイズを完全リセット"""
        logger.info("クイズをリセットしています...")
        
        # 新しいセッションIDを生成
        self.session_id = self._generate_session_id()
        
        # 新しいクイズセッションを作成
        quiz_session = QuizSession(session_id=self.session_id)
        st.session_state[self.KEYS['quiz_session']] = quiz_session
        
        # 画面をスタート画面に戻す
        self.set_current_screen(ScreenType.START)
        
        # 問題関連の状態リセット
        self._reset_question_state()
        
        logger.info(f"クイズリセット完了 - 新しいセッションID: {self.session_id}")
    
    def _reset_question_state(self) -> None:
        """問題関連の状態をリセット"""
        st.session_state[self.KEYS['current_poem']] = None
        st.session_state[self.KEYS['choices']] = []
        st.session_state[self.KEYS['answered']] = False
        st.session_state[self.KEYS['user_answer']] = None
        st.session_state[self.KEYS['show_result']] = False
    
    def record_answer(self, poem_number: int, question: str, correct_answer: str, 
                     user_answer: Optional[str], time_taken: Optional[float] = None,
                     used_hint: bool = False) -> None:
        """回答を記録"""
        quiz_session = self.get_quiz_session()
        if quiz_session:
            is_correct = user_answer == correct_answer if user_answer else False
            
            # 結果を記録
            result = QuestionResult(
                poem_number=poem_number,
                question=question,
                correct_answer=correct_answer,
                user_answer=user_answer,
                is_correct=is_correct,
                time_taken=time_taken,
                used_hint=used_hint
            )
            
            quiz_session.results.append(result)
            
            # スコア更新
            if is_correct:
                quiz_session.score += 1
            else:
                quiz_session.wrong_answers.append(poem_number)
            
            logger.info(f"回答記録: 問題{poem_number} - {'正解' if is_correct else '不正解'}")
    
    def advance_question(self) -> None:
        """次の問題に進む"""
        quiz_session = self.get_quiz_session()
        if quiz_session:
            quiz_session.current_question += 1
            
            # 最後の問題かチェック
            if quiz_session.current_question >= quiz_session.settings.total_questions:
                quiz_session.is_completed = True
                self.set_current_screen(ScreenType.RESULT)
                logger.info("クイズ完了 - 結果画面に遷移")
            else:
                # 次の問題の状態をリセット
                self._reset_question_state()
                logger.info(f"次の問題に進行: {quiz_session.current_question + 1}")
    
    def get_progress_info(self) -> Dict[str, Any]:
        """進捗情報を取得"""
        quiz_session = self.get_quiz_session()
        if not quiz_session:
            return {}
        
        total = quiz_session.settings.total_questions
        current = quiz_session.current_question
        
        return {
            'current_question': current + 1,  # 1始まりで表示
            'total_questions': total,
            'progress_ratio': current / total if total > 0 else 0,
            'score': quiz_session.score,
            'accuracy': quiz_session.score / max(current, 1) * 100,
            'remaining': total - current,
            'is_completed': quiz_session.is_completed
        }
    
    def get_quiz_results(self) -> Dict[str, Any]:
        """クイズ結果の詳細を取得"""
        quiz_session = self.get_quiz_session()
        if not quiz_session:
            return {}
        
        total_questions = len(quiz_session.results)
        correct_answers = sum(1 for r in quiz_session.results if r.is_correct)
        
        # 時間統計
        times = [r.time_taken for r in quiz_session.results if r.time_taken]
        avg_time = sum(times) / len(times) if times else 0
        
        return {
            'session_id': quiz_session.session_id,
            'total_questions': total_questions,
            'correct_answers': correct_answers,
            'wrong_answers': total_questions - correct_answers,
            'accuracy': (correct_answers / max(total_questions, 1)) * 100,
            'wrong_poem_numbers': quiz_session.wrong_answers.copy(),
            'average_time': avg_time,
            'start_time': quiz_session.start_time,
            'settings': quiz_session.settings,
            'results': quiz_session.results.copy()
        }
    
    def get_session_debug_info(self) -> Dict[str, Any]:
        """デバッグ用セッション情報"""
        quiz_session = self.get_quiz_session()
        
        return {
            'session_manager_id': self.session_id,
            'current_screen': self.get_current_screen().value,
            'quiz_session_id': quiz_session.session_id if quiz_session else None,
            'is_initialized': self._is_initialized(),
            'has_data_manager': self.KEYS['data_manager'] in st.session_state,
            'session_state_keys': list(st.session_state.keys()),
            'quiz_progress': self.get_progress_info(),
        }
    
    def validate_session_state(self) -> List[str]:
        """セッション状態の検証"""
        issues = []
        
        if not self._is_initialized():
            issues.append("セッションが初期化されていません")
        
        quiz_session = self.get_quiz_session()
        if not quiz_session:
            issues.append("クイズセッションが存在しません")
        else:
            if quiz_session.current_question < 0:
                issues.append("現在の問題番号が不正です")
            
            if quiz_session.score < 0:
                issues.append("スコアが不正です")
            
            if len(quiz_session.results) != quiz_session.current_question:
                issues.append("結果記録と進行状況が一致しません")
        
        return issues

# グローバルなセッションマネージャーインスタンス
_session_manager = None

def get_session_manager() -> SessionManager:
    """セッションマネージャーのシングルトンインスタンスを取得"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

# 便利関数
def initialize_app_session():
    """アプリケーションセッションの初期化（便利関数）"""
    sm = get_session_manager()
    sm.initialize_session()

def get_current_screen() -> ScreenType:
    """現在の画面を取得（便利関数）"""
    sm = get_session_manager()
    return sm.get_current_screen()

def navigate_to(screen: ScreenType):
    """画面遷移（便利関数）"""
    sm = get_session_manager()
    sm.set_current_screen(screen)

# 使用例とテスト用コード
if __name__ == "__main__":
    print("=== セッション管理モジュールのテスト ===")
    
    # SessionManagerインスタンス作成
    sm = SessionManager()
    
    # デバッグ情報表示
    debug_info = sm.get_session_debug_info()
    print("デバッグ情報:")
    for key, value in debug_info.items():
        print(f"  {key}: {value}")
    
    # 進捗情報テスト
    progress = sm.get_progress_info()
    print(f"\n進捗情報: {progress}")
    
    print("\nテスト完了")