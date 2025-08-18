def show_quiz_screen():
    """クイズ画面（通常版）"""
    sm = get_session_manager()
    screen_manager = get_screen_manager()
    quiz_session = sm.get_quiz_session()
    
    if not quiz_session:
        st.error("クイズセッションが初期化されていません")
        if st.button("🏠 スタート画面に戻る"):
            try:
                screen_manager.navigate_home()
            except:
                pass
            st.rerun()
        return
    
    # answer_validatorの確認
    if not st.session_state.answer_validator:
        st.session_state.answer_validator = AnswerValidator()
    
    # 進捗情報取得
    validator_stats = st.session_state.answer_validator.get_current_score()
    answered_count = validator_stats['total_questions']
    total_questions = quiz_session.settings.total_questions
    
    # クイズが完了している場合
    if answered_count >= total_questions:
        st.success("🎉 クイズ完了！")
        performance = st.session_state.answer_validator.get_statistics().get_performance_analysis()
        st.info(f"🏆 最終成績: {performance['overall_grade']}")
        
        if st.button("結果を見る", type="primary"):
            try:
                screen_manager.navigate_to('result')
            except:
                navigate_with_transition('result', TransitionType.FADE)
            st.rerun()
        return
    
    # current_quiz_questionが存在しない場合は初期化
    if 'current_quiz_question' not in st.session_state:
        st.session_state.current_quiz_question = None
    
    # 現在の問題を取得または生成
    if st.session_state.current_quiz_question is None:
        question = generate_next_question()
        if question:
            st.session_state.current_quiz_question = question
            st.session_state.answered = False
            st.session_state.user_answer = None
            st.session_state.question_start_time = time.time()
            st.session_state.hint_used = False
        else:
            st.error("問題を生成できませんでした")
            return
    
    current_question = st.session_state.current_quiz_question
    
    # ========================================
    # 問題文を最初に表示（UIコンポーネント不使用）
    # ========================================
    
    # タイトル
    st.title(f"問題 {answered_count + 1} / {total_questions}")#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百人一首クイズアプリ - メインアプリケーション
Streamlit Cloud対応版 - 最小依存関係
"""

import streamlit as st
import json
import random
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# ページ設定（最初に実行する必要がある）
st.set_page_config(
    page_title="百人一首クイズアプリ",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# モジュールのインポート試行
modules_available = True
try:
    # 基本モジュールから順にインポート
    from modules.data_manager import DataManager
    from modules.quiz_generator import QuizGenerator, QuizType, QuizQuestion
    from modules.answer_validator import AnswerValidator, AnswerStatus, AnswerResult
    from modules.session_manager import (
        get_session_manager, initialize_app_session, 
        ScreenType, QuizMode, Difficulty, QuizSettings
    )
    from modules.ui_components import (
        UIComponents, UITheme, UIConfig,
        create_ui_components, format_time, format_score
    )
    from modules.screen_manager import (
        QuizScreenManager, TransitionType, UpdateStrategy,
        get_screen_manager, navigate_with_transition,
        optimized_update, track_screen_time
    )
except ImportError as e:
    modules_available = False
    st.warning(f"⚠️ モジュールのインポートに失敗しました: {e}")
    st.info("📝 簡易版モードで動作します")

# モジュールが利用できない場合の簡易実装
if not modules_available:
    # Enum風クラスの定義
    class SimpleEnum:
        def __init__(self, value):
            self.value = value
            self.name = value
    
    class QuizType:
        UPPER_TO_LOWER = SimpleEnum('上の句→下の句')
        LOWER_TO_UPPER = SimpleEnum('下の句→上の句')
        AUTHOR_TO_POEM = SimpleEnum('作者→歌')
        POEM_TO_AUTHOR = SimpleEnum('歌→作者')
    
    class QuizMode:
        UPPER_TO_LOWER = SimpleEnum('upper_to_lower')
        LOWER_TO_UPPER = SimpleEnum('lower_to_upper')
        AUTHOR_TO_POEM = SimpleEnum('author_to_poem')
        POEM_TO_AUTHOR = SimpleEnum('poem_to_author')
    
    class Difficulty:
        BEGINNER = SimpleEnum('beginner')
        INTERMEDIATE = SimpleEnum('intermediate')
        ADVANCED = SimpleEnum('advanced')
    
    class ScreenType:
        START = SimpleEnum('start')
        QUIZ = SimpleEnum('quiz')
        RESULT = SimpleEnum('result')
        SETTINGS = SimpleEnum('settings')
        REVIEW = SimpleEnum('review')
    
    class TransitionType:
        NONE = SimpleEnum('none')
        FADE = SimpleEnum('fade')
        SLIDE = SimpleEnum('slide')
        ZOOM = SimpleEnum('zoom')
    
    class UpdateStrategy:
        FULL = SimpleEnum('full')
        PARTIAL = SimpleEnum('partial')
        CACHED = SimpleEnum('cached')

# クイズモードのマッピング
QUIZ_MODE_MAPPING = {
    QuizMode.UPPER_TO_LOWER: QuizType.UPPER_TO_LOWER,
    QuizMode.LOWER_TO_UPPER: QuizType.LOWER_TO_UPPER,
    QuizMode.AUTHOR_TO_POEM: QuizType.AUTHOR_TO_POEM,
    QuizMode.POEM_TO_AUTHOR: QuizType.POEM_TO_AUTHOR
} if modules_available else {}

# 難易度マッピング
DIFFICULTY_MAPPING = {
    Difficulty.BEGINNER: "beginner",
    Difficulty.INTERMEDIATE: "intermediate",
    Difficulty.ADVANCED: "advanced"
} if modules_available else {}

def initialize_session():
    """セッション状態の初期化"""
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.poems_data = None
        st.session_state.current_screen = 'start'
        st.session_state.quiz_mode = 'upper_to_lower'
        st.session_state.difficulty = 'beginner'
        st.session_state.total_questions = 10
        st.session_state.current_question_index = 0
        st.session_state.score = 0
        st.session_state.quiz_active = False
        st.session_state.quiz_questions = []
        st.session_state.user_answers = []
        st.session_state.answered = False
        st.session_state.selected_answer = None
        # 通常版でも必要な変数を初期化
        st.session_state.data_manager = None
        st.session_state.quiz_generator = None
        st.session_state.answer_validator = None
        st.session_state.current_quiz_question = None
        st.session_state.question_start_time = None
        st.session_state.user_answer = None
        st.session_state.hint_used = False
        
    if modules_available:
        # 通常版の初期化
        initialize_app_session()
        
        screen_manager = get_screen_manager()
        
        if 'ui_components' not in st.session_state:
            st.session_state.ui_components = create_ui_components(UITheme.DEFAULT)
            
        if not screen_manager.get_current_screen():
            screen_manager.navigate_to('start')

def load_app_data():
    """アプリケーションデータの読み込み"""
    try:
        # JSONファイルの読み込み
        json_path = Path(__file__).parent / 'data' / 'hyakunin_isshu.json'
        
        # ファイルが存在しない場合は、デフォルトパスも試す
        if not json_path.exists():
            json_path = Path('data/hyakunin_isshu.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            st.session_state.poems_data = data
            
            if modules_available:
                # DataManagerの初期化
                if 'data_manager' not in st.session_state or st.session_state.data_manager is None:
                    st.session_state.data_manager = DataManager()
                    
                if 'quiz_generator' not in st.session_state or st.session_state.quiz_generator is None:
                    st.session_state.quiz_generator = QuizGenerator(data)
                    
                if 'answer_validator' not in st.session_state or st.session_state.answer_validator is None:
                    st.session_state.answer_validator = AnswerValidator()
                
                # DataManagerにデータをロード
                if hasattr(st.session_state.data_manager, 'load_poem_data'):
                    st.session_state.data_manager.load_poem_data()
                
            return True, f"✅ {len(data)}首の歌を読み込みました"
    except FileNotFoundError:
        return False, "❌ データファイル (hyakunin_isshu.json) が見つかりません"
    except json.JSONDecodeError:
        return False, "❌ JSONファイルの形式が不正です"
    except Exception as e:
        return False, f"❌ データの読み込みに失敗しました: {e}"

def generate_simple_quiz(poems_data, quiz_type='upper_to_lower', difficulty='beginner'):
    """簡易版のクイズ生成"""
    if not poems_data:
        return None
    
    # 難易度に応じて出題範囲を制限
    if difficulty == 'beginner':
        # 有名な歌（1-20番）
        filtered_poems = [p for p in poems_data if p['number'] <= 20]
    elif difficulty == 'intermediate':
        # 中級（1-50番）
        filtered_poems = [p for p in poems_data if p['number'] <= 50]
    else:
        # 上級（全ての歌）
        filtered_poems = poems_data
    
    if not filtered_poems:
        return None
    
    # ランダムに1首選択
    correct_poem = random.choice(filtered_poems)
    
    # 問題と正解を設定
    if quiz_type == 'upper_to_lower':
        question = f"上の句：{correct_poem['upper']}"
        correct_answer = correct_poem['lower']
        # 選択肢を生成（他の歌の下の句を混ぜる）
        other_poems = [p for p in filtered_poems if p['number'] != correct_poem['number']]
        random.shuffle(other_poems)
        choices = [correct_answer]
        for p in other_poems[:3]:
            if p['lower'] not in choices:
                choices.append(p['lower'])
                if len(choices) >= 4:
                    break
    elif quiz_type == 'lower_to_upper':
        question = f"下の句：{correct_poem['lower']}"
        correct_answer = correct_poem['upper']
        other_poems = [p for p in filtered_poems if p['number'] != correct_poem['number']]
        random.shuffle(other_poems)
        choices = [correct_answer]
        for p in other_poems[:3]:
            if p['upper'] not in choices:
                choices.append(p['upper'])
                if len(choices) >= 4:
                    break
    elif quiz_type == 'author_to_poem':
        question = f"作者：{correct_poem['author']}"
        correct_answer = f"{correct_poem['upper']} {correct_poem['lower']}"
        other_poems = [p for p in filtered_poems if p['number'] != correct_poem['number']]
        random.shuffle(other_poems)
        choices = [correct_answer]
        for p in other_poems[:3]:
            choice = f"{p['upper']} {p['lower']}"
            if choice not in choices:
                choices.append(choice)
                if len(choices) >= 4:
                    break
    else:  # poem_to_author
        question = f"{correct_poem['upper']}\n{correct_poem['lower']}"
        correct_answer = correct_poem['author']
        other_poems = [p for p in filtered_poems if p['number'] != correct_poem['number']]
        random.shuffle(other_poems)
        choices = [correct_answer]
        for p in other_poems[:3]:
            if p['author'] not in choices:
                choices.append(p['author'])
                if len(choices) >= 4:
                    break
    
    # 選択肢が4つに満たない場合の処理
    while len(choices) < 4:
        choices.append(f"選択肢{len(choices) + 1}")
    
    # 選択肢をシャッフル
    random.shuffle(choices)
    correct_index = choices.index(correct_answer)
    
    return {
        'poem_number': correct_poem['number'],
        'question': question,
        'choices': choices,
        'correct_answer': correct_answer,
        'correct_index': correct_index,
        'poem': correct_poem
    }

def show_simple_start_screen():
    """簡易版のスタート画面"""
    st.title("🎌 百人一首クイズアプリ")
    
    st.markdown("""
    このアプリは百人一首を楽しく学習できるクイズアプリです。
    上の句と下の句の対応や、作者と歌の関係を覚えることができます。
    """)
    
    # データの状態を表示
    if st.session_state.poems_data:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("収録歌数", f"{len(st.session_state.poems_data)}首")
        with col2:
            st.metric("問題数", f"{st.session_state.total_questions}問")
        with col3:
            difficulty_text = {
                'beginner': '初級',
                'intermediate': '中級',
                'advanced': '上級'
            }
            st.metric("難易度", difficulty_text.get(st.session_state.difficulty, '初級'))
    
    st.markdown("---")
    
    # 設定セクション
    st.subheader("⚙️ クイズ設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # クイズモード選択
        mode_options = {
            'upper_to_lower': '上の句→下の句',
            'lower_to_upper': '下の句→上の句',
            'author_to_poem': '作者→歌',
            'poem_to_author': '歌→作者'
        }
        st.session_state.quiz_mode = st.selectbox(
            "出題形式",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            key='mode_selector'
        )
        
        # 問題数設定
        st.session_state.total_questions = st.slider(
            "問題数",
            min_value=5,
            max_value=30,
            value=10,
            step=5,
            key='question_count_slider'
        )
    
    with col2:
        # 難易度選択
        difficulty_options = {
            'beginner': '初級（有名な歌）',
            'intermediate': '中級（一般的な歌）',
            'advanced': '上級（全ての歌）'
        }
        st.session_state.difficulty = st.selectbox(
            "難易度",
            options=list(difficulty_options.keys()),
            format_func=lambda x: difficulty_options[x],
            key='difficulty_selector'
        )
    
    # スタートボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 クイズを開始", type="primary", use_container_width=True):
            # クイズの初期化
            st.session_state.current_screen = 'quiz'
            st.session_state.quiz_active = True
            st.session_state.current_question_index = 0
            st.session_state.score = 0
            st.session_state.quiz_questions = []
            st.session_state.user_answers = []
            st.rerun()

def show_simple_quiz_screen():
    """簡易版のクイズ画面"""
    # ヘッダー
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header(f"問題 {st.session_state.current_question_index + 1} / {st.session_state.total_questions}")
    with col2:
        st.metric("スコア", f"{st.session_state.score}点")
    with col3:
        accuracy = (st.session_state.score / max(st.session_state.current_question_index, 1) * 100) if st.session_state.current_question_index > 0 else 0
        st.metric("正答率", f"{accuracy:.0f}%")
    
    # プログレスバー
    progress = st.session_state.current_question_index / st.session_state.total_questions
    st.progress(progress)
    
    st.markdown("---")
    
    # クイズ完了チェック
    if st.session_state.current_question_index >= st.session_state.total_questions:
        st.session_state.current_screen = 'result'
        st.rerun()
        return
    
    # 現在の問題を生成または取得
    if len(st.session_state.quiz_questions) <= st.session_state.current_question_index:
        question_data = generate_simple_quiz(
            st.session_state.poems_data,
            st.session_state.quiz_mode,
            st.session_state.difficulty
        )
        if question_data:
            st.session_state.quiz_questions.append(question_data)
        else:
            st.error("問題の生成に失敗しました")
            return
    
    current_question = st.session_state.quiz_questions[st.session_state.current_question_index]
    
    # 問題表示
    st.subheader("📝 問題")
    st.info(current_question['question'])
    
    # 選択肢表示
    st.subheader("選択肢")
    
    if not st.session_state.answered:
        # 回答前：選択肢ボタン
        for i, choice in enumerate(current_question['choices']):
            if st.button(f"{i+1}. {choice}", key=f"choice_{i}", use_container_width=True):
                st.session_state.selected_answer = i
                st.session_state.answered = True
                
                # 正解判定
                if i == current_question['correct_index']:
                    st.session_state.score += 1
                    st.session_state.user_answers.append({
                        'question': current_question['question'],
                        'user_answer': choice,
                        'correct_answer': current_question['correct_answer'],
                        'is_correct': True
                    })
                else:
                    st.session_state.user_answers.append({
                        'question': current_question['question'],
                        'user_answer': choice,
                        'correct_answer': current_question['correct_answer'],
                        'is_correct': False
                    })
                st.rerun()
    else:
        # 回答後：結果表示
        for i, choice in enumerate(current_question['choices']):
            if i == current_question['correct_index']:
                st.success(f"✅ {i+1}. {choice} (正解)")
            elif i == st.session_state.selected_answer:
                st.error(f"❌ {i+1}. {choice} (あなたの回答)")
            else:
                st.write(f"{i+1}. {choice}")
        
        # 詳細情報表示
        st.markdown("---")
        poem = current_question['poem']
        st.info(f"""
        **{poem['number']}番の歌**
        
        {poem['upper']}  
        {poem['lower']}
        
        **作者**: {poem['author']}
        """)
        
        # 次へボタン
        if st.button("次の問題へ →", type="primary", use_container_width=True):
            st.session_state.current_question_index += 1
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()

def show_simple_result_screen():
    """簡易版の結果画面"""
    st.title("🏆 クイズ結果")
    
    # スコア表示
    total = st.session_state.total_questions
    score = st.session_state.score
    accuracy = (score / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("合計問題数", f"{total}問")
    with col2:
        st.metric("正解数", f"{score}問")
    with col3:
        st.metric("正答率", f"{accuracy:.1f}%")
    
    # 成績評価
    if accuracy >= 90:
        st.success("🎉 素晴らしい！百人一首マスターです！")
    elif accuracy >= 70:
        st.info("😊 よくできました！もう少しで完璧です！")
    elif accuracy >= 50:
        st.warning("📚 まずまずです。もう少し練習しましょう！")
    else:
        st.error("💪 がんばりましょう！繰り返し挑戦してみてください！")
    
    # 間違えた問題の表示
    wrong_answers = [a for a in st.session_state.user_answers if not a['is_correct']]
    if wrong_answers:
        st.markdown("---")
        st.subheader("❌ 間違えた問題")
        for i, answer in enumerate(wrong_answers, 1):
            with st.expander(f"問題 {i}"):
                st.write(f"**問題**: {answer['question']}")
                st.write(f"**あなたの回答**: {answer['user_answer']}")
                st.write(f"**正解**: {answer['correct_answer']}")
    
    # アクションボタン
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏠 ホームに戻る", use_container_width=True):
            st.session_state.current_screen = 'start'
            st.session_state.quiz_active = False
            st.rerun()
    with col2:
        if st.button("🔄 もう一度挑戦", use_container_width=True):
            st.session_state.current_screen = 'quiz'
            st.session_state.current_question_index = 0
            st.session_state.score = 0
            st.session_state.quiz_questions = []
            st.session_state.user_answers = []
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()
    with col3:
        if wrong_answers and st.button("📚 間違えた問題を復習", use_container_width=True):
            st.session_state.current_screen = 'review'
            st.rerun()

def show_simple_review_screen():
    """簡易版の復習画面"""
    st.title("📚 復習モード")
    
    wrong_answers = [a for a in st.session_state.user_answers if not a['is_correct']]
    
    if not wrong_answers:
        st.success("全問正解でした！復習する問題はありません。")
    else:
        st.info(f"間違えた問題を復習しましょう（{len(wrong_answers)}問）")
        
        for i, answer in enumerate(wrong_answers, 1):
            st.markdown(f"### 復習問題 {i}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.error("❌ 間違い")
                st.write(f"**問題**: {answer['question']}")
                st.write(f"**あなたの回答**: {answer['user_answer']}")
            
            with col2:
                st.success("✅ 正解")
                st.write(f"**正しい答え**: {answer['correct_answer']}")
            
            st.markdown("---")
    
    # ナビゲーション
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 ホームに戻る", use_container_width=True):
            st.session_state.current_screen = 'start'
            st.rerun()
    with col2:
        if st.button("🔄 もう一度クイズに挑戦", use_container_width=True):
            st.session_state.current_screen = 'quiz'
            st.session_state.current_question_index = 0
            st.session_state.score = 0
            st.session_state.quiz_questions = []
            st.session_state.user_answers = []
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()

# 以下、通常版の関数は元のコードから必要な部分のみ抜粋
def generate_next_question() -> Optional[Any]:
    """次の問題を生成する（通常版）"""
    if not modules_available:
        return None
    
    sm = get_session_manager()
    quiz_session = sm.get_quiz_session()
    
    if not quiz_session or not st.session_state.quiz_generator:
        return None
    
    quiz_type = QUIZ_MODE_MAPPING.get(quiz_session.settings.mode, QuizType.UPPER_TO_LOWER)
    difficulty = DIFFICULTY_MAPPING.get(quiz_session.settings.difficulty, "beginner")
    
    exclude_numbers = []
    if st.session_state.answer_validator:
        answered_results = st.session_state.answer_validator.get_statistics().answer_results
        exclude_numbers = [result.poem_number for result in answered_results]
    
    question = st.session_state.quiz_generator.generate_question(
        quiz_type=quiz_type,
        difficulty=difficulty,
        exclude_numbers=exclude_numbers
    )
    
    return question

def generate_hint(question) -> str:
    """問題に応じたヒントを生成（通常版）"""
    if not modules_available:
        return "頑張って考えてみてください！"
    
    if question.quiz_type == QuizType.UPPER_TO_LOWER:
        return f"下の句の最初の文字は「{question.correct_answer[0]}」です"
    elif question.quiz_type == QuizType.LOWER_TO_UPPER:
        return f"上の句の最初の文字は「{question.correct_answer[0]}」です"
    elif question.quiz_type == QuizType.AUTHOR_TO_POEM:
        return f"この歌は{question.poem_number}番の歌です"
    elif question.quiz_type == QuizType.POEM_TO_AUTHOR:
        if question.poem_number <= 20:
            return "平安時代前期の歌人です"
        elif question.poem_number <= 50:
            return "平安時代中期の歌人です"
        else:
            return "平安時代後期以降の歌人です"
    else:
        return "頑張って考えてみてください！"

def main():
    """メインアプリケーション"""
    # セッション初期化
    initialize_session()
    
    # データの読み込み
    data_success, data_message = load_app_data()
    
    if not data_success:
        st.error(data_message)
        st.info("""
        データファイルが必要です。以下の形式でJSONファイルを作成してください：
        
        ```json
        [
            {
                "number": 1,
                "upper": "秋の田の",
                "lower": "かりほの庵の苫をあらみ",
                "author": "天智天皇",
                "reading": "あきのたの かりほのいほの とまをあらみ",
                "translation": "秋の田の仮小屋の屋根の苫が粗いので"
            }
        ]
        ```
        """)
        return
    
    st.success(data_message)
    
    # モジュールが利用できない場合は簡易版を使用
    if not modules_available:
        # 簡易版の画面遷移
        if st.session_state.current_screen == 'start':
            show_simple_start_screen()
        elif st.session_state.current_screen == 'quiz':
            show_simple_quiz_screen()
        elif st.session_state.current_screen == 'result':
            show_simple_result_screen()
        elif st.session_state.current_screen == 'review':
            show_simple_review_screen()
        else:
            show_simple_start_screen()
    else:
        # 通常版の処理（元のコードと同じ）
        ui = st.session_state.ui_components
        sm = get_session_manager()
        screen_manager = get_screen_manager()
        
        # 現在の画面を取得
        current_screen = screen_manager.get_current_screen()
        
        # 画面マッピング
        screen_map = {
            'start': (ScreenType.START, show_start_screen),
            'quiz': (ScreenType.QUIZ, show_quiz_screen),
            'result': (ScreenType.RESULT, show_result_screen),
            'settings': (ScreenType.SETTINGS, show_settings_screen),
            'review': (ScreenType.REVIEW, show_review_screen)
        }
        
        # ナビゲーションバー表示
        if current_screen:
            screen_type = screen_map.get(current_screen, (ScreenType.START, None))[0]
            
            def safe_navigate(screen: str):
                if screen == 'result' and current_screen != 'quiz':
                    st.warning("結果画面はクイズ完了後のみ表示できます")
                    return
                navigate_with_transition(screen, TransitionType.FADE)
            
            ui.render_navigation_bar(
                current_screen=screen_type.value,
                on_navigate=safe_navigate
            )
        
        # 各画面の表示
        if current_screen in screen_map:
            _, show_func = screen_map[current_screen]
            if show_func:
                show_func()
        else:
            show_start_screen()

# 通常版の画面関数
def show_start_screen():
    """スタート画面（通常版）"""
    ui = st.session_state.ui_components
    sm = get_session_manager()
    screen_manager = get_screen_manager()
    quiz_session = sm.get_quiz_session()
    dm = st.session_state.data_manager
    
    # 画面滞在時間を記録
    screen_time = track_screen_time('start')
    
    # ヘッダー表示（キャッシュ利用）
    optimized_update('start_header', ui.render_start_screen_header, strategy=UpdateStrategy.CACHED)
    
    # 基本情報表示
    if dm and dm.is_loaded:
        stats = dm.get_data_stats()
        
        # 難易度テキストの取得
        difficulty_text = "初級"
        if quiz_session:
            diff_map = {
                Difficulty.BEGINNER: "初級",
                Difficulty.INTERMEDIATE: "中級", 
                Difficulty.ADVANCED: "上級"
            }
            difficulty_text = diff_map.get(quiz_session.settings.difficulty, difficulty_text)
        
        # 統計情報表示（部分更新）
        optimized_update('game_stats', 
                        lambda: ui.render_game_stats(
                            total_poems=stats['total_poems'],
                            total_authors=stats['unique_authors'],
                            quiz_questions=quiz_session.settings.total_questions if quiz_session else 10,
                            difficulty=difficulty_text
                        ),
                        data=stats,
                        strategy=UpdateStrategy.PARTIAL)
    
    # 設定セクション
    st.markdown("---")
    settings = ui.render_quiz_settings()
    
    # モード選択
    mode_options = {
        "upper_to_lower": "上の句→下の句",
        "lower_to_upper": "下の句→上の句",
        "author_to_poem": "作者→歌",
        "poem_to_author": "歌→作者"
    }
    
    selected_mode = ui.render_game_mode_selector(mode_options, "upper_to_lower")
    
    # 難易度選択
    difficulty_options = {
        "beginner": "初級（有名な歌）",
        "intermediate": "中級（一般的な歌）",
        "advanced": "上級（全ての歌）"
    }
    
    selected_difficulty = ui.render_difficulty_selector(difficulty_options, "beginner")
    
    # 設定を更新
    if quiz_session:
        mode_enum_map = {
            "upper_to_lower": QuizMode.UPPER_TO_LOWER,
            "lower_to_upper": QuizMode.LOWER_TO_UPPER,
            "author_to_poem": QuizMode.AUTHOR_TO_POEM,
            "poem_to_author": QuizMode.POEM_TO_AUTHOR
        }
        
        diff_enum_map = {
            "beginner": Difficulty.BEGINNER,
            "intermediate": Difficulty.INTERMEDIATE,
            "advanced": Difficulty.ADVANCED
        }
        
        sm.update_quiz_settings(
            total_questions=settings['question_count'],
            mode=mode_enum_map[selected_mode],
            difficulty=diff_enum_map[selected_difficulty],
            enable_hints=settings['enable_hints'],
            show_explanations=settings['show_explanations']
        )
    
    # スタートボタン
    if ui.render_start_button():
        sm.start_new_quiz()
        if st.session_state.quiz_generator:
            st.session_state.quiz_generator.reset_used_questions()
        if st.session_state.answer_validator:
            st.session_state.answer_validator.reset_statistics()
        
        # 画面遷移（スライドエフェクト付き）
        navigate_with_transition('quiz', TransitionType.SLIDE)
        st.rerun()

def show_quiz_screen():
    """クイズ画面（通常版）"""
    ui = st.session_state.ui_components
    sm = get_session_manager()
    screen_manager = get_screen_manager()
    quiz_session = sm.get_quiz_session()
    
    if not quiz_session:
        ui.render_error_message("クイズセッションが初期化されていません")
        if st.button("🏠 スタート画面に戻る"):
            screen_manager.navigate_home()
            st.rerun()
        return
    
    # answer_validatorの確認
    if not st.session_state.answer_validator:
        st.session_state.answer_validator = AnswerValidator()
    
    # 進捗情報取得
    validator_stats = st.session_state.answer_validator.get_current_score()
    answered_count = validator_stats['total_questions']
    total_questions = quiz_session.settings.total_questions
    
    # クイズが完了している場合
    if answered_count >= total_questions:
        ui.render_success_message("クイズ完了！", show_balloons=True)
        
        performance = st.session_state.answer_validator.get_statistics().get_performance_analysis()
        st.info(f"🏆 最終成績: {performance['overall_grade']}")
        
        if ui.render_next_question_button(is_last_question=True):
            try:
                screen_manager.navigate_to('result')
            except:
                navigate_with_transition('result', TransitionType.FADE)
            st.rerun()
        return
    
    # current_quiz_questionが存在しない場合は初期化
    if 'current_quiz_question' not in st.session_state:
        st.session_state.current_quiz_question = None
    
    # 現在の問題を取得または生成
    if st.session_state.current_quiz_question is None:
        question = generate_next_question()
        if question:
            st.session_state.current_quiz_question = question
            st.session_state.answered = False
            st.session_state.user_answer = None
            st.session_state.question_start_time = time.time()
            st.session_state.hint_used = False
            try:
                screen_manager.mark_screen_dirty('quiz')
            except:
                pass
        else:
            ui.render_error_message("問題を生成できませんでした")
            return
    
    current_question = st.session_state.current_quiz_question
    
    # ========================================
    # レイアウト：問題文 → ヘッダー → 選択肢の順
    # ========================================
    
    # 1. まず問題文を表示（これが最上部）
    ui.render_question_display(
        question_text=current_question.question_text,
        poem_number=current_question.poem_number,
        additional_info=f"問題タイプ: {current_question.quiz_type.value}"
    )
    
    # 2. その後にヘッダー（進捗）を表示
    ui.render_quiz_header(
        current_question=answered_count + 1,
        total_questions=total_questions,
        score=validator_stats['correct_answers'],
        accuracy=validator_stats['accuracy']
    )
    
    st.markdown("---")
    
    # 3. 回答エリア
    if not st.session_state.answered:
        # 回答前の表示
        selected_choice = ui.render_choice_buttons(
            choices=current_question.choices,
            answered=False
        )
        
        if selected_choice is not None:
            st.session_state.user_answer = selected_choice
        
        # 回答ボタン
        button_action = ui.render_answer_buttons(
            enable_hint=quiz_session.settings.enable_hints and not st.session_state.hint_used,
            enable_skip=True
        )
        
        if button_action == 'answer' and st.session_state.user_answer is not None:
            # 回答処理
            time_taken = time.time() - st.session_state.question_start_time
            question_id = f"{current_question.poem_number}_{current_question.quiz_type.value}"
            
            result = st.session_state.answer_validator.check_answer(
                question_id=question_id,
                poem_number=current_question.poem_number,
                question_text=current_question.question_text,
                correct_answer=current_question.correct_answer,
                correct_index=current_question.correct_answer_index,
                user_answer=current_question.choices[st.session_state.user_answer],
                answer_index=st.session_state.user_answer,
                time_taken=time_taken,
                hint_used=st.session_state.hint_used
            )
            
            sm.record_answer(
                poem_number=current_question.poem_number,
                question=current_question.question_text,
                correct_answer=current_question.correct_answer,
                user_answer=current_question.choices[st.session_state.user_answer],
                time_taken=time_taken
            )
            
            st.session_state.answered = True
            st.session_state.current_answer_result = result
            st.rerun()
            
        elif button_action == 'hint':
            hint_text = generate_hint(current_question)
            ui.render_hint_display(hint_text)
            st.session_state.hint_used = True
            
        elif button_action == 'skip':
            # スキップ処理
            time_taken = time.time() - st.session_state.question_start_time
            question_id = f"{current_question.poem_number}_{current_question.quiz_type.value}"
            
            result = st.session_state.answer_validator.check_answer(
                question_id=question_id,
                poem_number=current_question.poem_number,
                question_text=current_question.question_text,
                correct_answer=current_question.correct_answer,
                correct_index=current_question.correct_answer_index,
                user_answer=None,
                answer_index=None,
                time_taken=time_taken,
                hint_used=False
            )
            
            sm.record_answer(
                poem_number=current_question.poem_number,
                question=current_question.question_text,
                correct_answer=current_question.correct_answer,
                user_answer=None,
                time_taken=time_taken
            )
            
            st.session_state.answered = True
            st.session_state.user_answer = None
            st.session_state.current_answer_result = result
            st.rerun()
    
    # 回答済みの場合
    else:
        # 選択肢を結果表示モードで表示
        ui.render_choice_buttons(
            choices=current_question.choices,
            correct_index=current_question.correct_answer_index,
            user_answer_index=st.session_state.user_answer,
            answered=True
        )
        
        if hasattr(st.session_state, 'current_answer_result'):
            result = st.session_state.current_answer_result
            
            # 結果表示
            ui.render_answer_result(
                is_correct=result.is_correct,
                user_answer=result.user_answer if result.user_answer else "未回答",
                correct_answer=result.correct_answer,
                points=result.points,
                time_taken=result.time_taken,
                explanation=current_question.explanation if quiz_session.settings.show_explanations else None
            )
            
            # 次へ進むボタン
            if ui.render_next_question_button(is_last_question=(answered_count + 1 >= total_questions)):
                # 状態をリセット
                st.session_state.current_quiz_question = None
                st.session_state.answered = False
                st.session_state.user_answer = None
                st.session_state.hint_used = False
                if hasattr(st.session_state, 'current_answer_result'):
                    delattr(st.session_state, 'current_answer_result')
                
                # 最後の問題の場合は結果画面へ
                if answered_count + 1 >= total_questions:
                    try:
                        screen_manager.navigate_to('result')
                    except:
                        navigate_with_transition('result', TransitionType.FADE)
                
                st.rerun()
    
    # クイズ中断ボタン
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🚪 クイズを中断", type="secondary"):
            try:
                if screen_manager.handle_quiz_interruption():
                    st.rerun()
            except:
                navigate_with_transition('start', TransitionType.FADE)
                st.rerun()

def show_result_screen():
    """結果画面（通常版）"""
    ui = st.session_state.ui_components
    screen_manager = get_screen_manager()
    
    if not st.session_state.answer_validator:
        ui.render_error_message("結果データがありません")
        if st.button("🏠 スタート画面に戻る"):
            try:
                screen_manager.navigate_home()
            except:
                navigate_with_transition('start', TransitionType.FADE)
            st.rerun()
        return
    
    # 統計情報取得（エラーハンドリング追加）
    try:
        stats = st.session_state.answer_validator.get_statistics()
        score_info = st.session_state.answer_validator.get_current_score()
    except Exception as e:
        st.error(f"統計情報の取得に失敗しました: {e}")
        if st.button("🏠 スタート画面に戻る"):
            navigate_with_transition('start', TransitionType.FADE)
            st.rerun()
        return
    
    # ヘッダー表示
    try:
        optimized_update('result_header',
                        lambda: ui.render_result_header(
                            total_questions=stats.total_questions,
                            correct_answers=stats.correct_answers,
                            total_points=stats.total_points,
                            accuracy=stats.accuracy,
                            grade=score_info['grade']
                        ),
                        data=score_info,
                        strategy=UpdateStrategy.CACHED)
    except:
        # optimized_updateが使えない場合は直接表示
        ui.render_result_header(
            total_questions=stats.total_questions,
            correct_answers=stats.correct_answers,
            total_points=stats.total_points,
            accuracy=stats.accuracy,
            grade=score_info['grade']
        )
    
    # 詳細統計
    detailed_stats = {
        'average_time': stats.average_time,
        'fastest_time': min([r.time_taken for r in stats.answer_results], default=0),
        'slowest_time': max([r.time_taken for r in stats.answer_results], default=0),
        'hint_used': stats.hint_used_count,
        'incorrect_answers': stats.incorrect_answers,
        'skipped_answers': stats.skipped_answers,
        'average_points': stats.average_points
    }
    
    ui.render_detailed_stats(detailed_stats)
    
    # 間違えた問題リスト
    wrong_answers = []
    for result in stats.answer_results:
        if not result.is_correct:
            wrong_answers.append({
                'poem_number': result.poem_number,
                'question': result.question_text,
                'correct_answer': result.correct_answer,
                'user_answer': result.user_answer if result.user_answer else "未回答",
                'status': result.status.value,
                'time_taken': result.time_taken,
                'hint_used': result.hint_used
            })
    
    ui.render_wrong_answers_list(wrong_answers)
    
    # アクションボタン
    has_wrong = len(wrong_answers) > 0
    
    action = ui.render_action_buttons(has_wrong_answers=has_wrong)
    
    if action == 'home':
        try:
            screen_manager.navigate_home()
        except:
            navigate_with_transition('start', TransitionType.FADE)
        st.rerun()
    elif action == 'restart':
        try:
            screen_manager.restart_quiz()
        except:
            # 手動でリスタート
            st.session_state.current_quiz_question = None
            st.session_state.answered = False
            st.session_state.user_answer = None
            st.session_state.hint_used = False
            if st.session_state.answer_validator:
                st.session_state.answer_validator.reset_statistics()
            navigate_with_transition('quiz', TransitionType.SLIDE)
        st.rerun()
    elif action == 'review':
        navigate_with_transition('review', TransitionType.FADE)
        st.rerun()
    elif action == 'challenge':
        navigate_with_transition('start', TransitionType.ZOOM)
        st.rerun()

def show_settings_screen():
    """設定画面（通常版）"""
    ui = st.session_state.ui_components
    screen_manager = get_screen_manager()
    
    st.header("⚙️ 設定")
    
    # テーマ選択
    st.subheader("🎨 テーマ設定")
    theme_options = {
        "デフォルト": UITheme.DEFAULT,
        "和風": UITheme.TRADITIONAL,
        "モダン": UITheme.MODERN
    }
    
    selected_theme = st.selectbox(
        "UIテーマを選択",
        list(theme_options.keys()),
        help="アプリの見た目を変更できます"
    )
    
    if st.button("テーマを適用"):
        ui.set_theme(theme_options[selected_theme])
        ui.render_success_message("テーマを変更しました")
        st.rerun()
    
    # その他の設定
    st.subheader("🔧 その他の設定")
    
    col1, col2 = st.columns(2)
    with col1:
        show_progress = st.checkbox("プログレスバーを表示", value=ui.config.show_progress_bar)
        show_timer = st.checkbox("タイマーを表示", value=ui.config.show_timer)
    
    with col2:
        enable_animations = st.checkbox("アニメーションを有効化", value=ui.config.enable_animations)
    
    if st.button("設定を保存"):
        ui.update_config(
            show_progress_bar=show_progress,
            show_timer=show_timer,
            enable_animations=enable_animations
        )
        ui.render_success_message("設定を保存しました")
    
    # 画面遷移デバッグ情報
    if st.checkbox("🔧 開発者モード"):
        screen_manager.render_debug_panel()
    
    # ナビゲーション
    st.markdown("---")
    if st.button("🏠 スタート画面に戻る"):
        screen_manager.navigate_home()
        st.rerun()

def show_review_screen():
    """復習画面（通常版）"""
    ui = st.session_state.ui_components
    screen_manager = get_screen_manager()
    
    st.header("📚 復習モード")
    
    if not st.session_state.answer_validator:
        ui.render_info_message("復習データがありません")
        if st.button("🏠 スタート画面に戻る"):
            screen_manager.navigate_home()
            st.rerun()
        return
    
    # 間違えた問題を取得
    wrong_answers = st.session_state.answer_validator.get_wrong_answers()
    
    if wrong_answers:
        st.subheader("📝 復習対象の問題")
        st.write(f"間違えた問題: {len(wrong_answers)}問")
        
        # 間違えた歌の詳細を表示
        dm = st.session_state.data_manager
        if dm and dm.is_loaded:
            for result in wrong_answers[:5]:  # 最初の5問のみ表示
                poem = dm.get_poem_by_number(result.poem_number)
                if poem:
                    poem_data = {
                        'number': poem['number'],
                        'upper': poem['upper'],
                        'lower': poem['lower'],
                        'author': poem['author'],
                        'reading': poem.get('reading', ''),
                        'translation': poem.get('translation', ''),
                        'explanation': f"あなたの回答: {result.user_answer if result.user_answer else '未回答'}"
                    }
                    ui.render_poem_card(poem_data, show_full_info=True)
            
            if len(wrong_answers) > 5:
                ui.render_info_message(f"他に {len(wrong_answers) - 5}首の間違えた歌があります")
    else:
        ui.render_success_message("全問正解でした！", show_balloons=True)
    
    # ナビゲーション
    st.markdown("---")
    if st.button("🏠 スタート画面に戻る"):
        screen_manager.navigate_home()
        st.rerun()

if __name__ == "__main__":
    main()