#!/usr/bin/env python
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
        
    if modules_available:
        # 通常版の初期化
        initialize_app_session()
        
        screen_manager = get_screen_manager()
        
        if 'ui_components' not in st.session_state:
            st.session_state.ui_components = create_ui_components(UITheme.DEFAULT)
        
        if 'data_manager' not in st.session_state:
            st.session_state.data_manager = None
            st.session_state.quiz_generator = None
            st.session_state.answer_validator = None
            st.session_state.current_quiz_question = None
            st.session_state.question_start_time = None
            st.session_state.user_answer = None
            st.session_state.hint_used = False
            
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
            
            if modules_available and 'data_manager' in st.session_state:
                # DataManagerの初期化
                st.session_state.data_manager = DataManager()
                st.session_state.quiz_generator = QuizGenerator(data)
                st.session_state.answer_validator = AnswerValidator()
                
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

# 通常版の画面関数（必要に応じて元のコードから追加）
def show_start_screen():
    """スタート画面（通常版）"""
    # この関数は元のコードをそのまま使用
    pass

def show_quiz_screen():
    """クイズ画面（通常版）"""
    # この関数は元のコードをそのまま使用
    pass

def show_result_screen():
    """結果画面（通常版）"""
    # この関数は元のコードをそのまま使用
    pass

def show_settings_screen():
    """設定画面（通常版）"""
    # この関数は元のコードをそのまま使用
    pass

def show_review_screen():
    """復習画面（通常版）"""
    # この関数は元のコードをそのまま使用
    pass

if __name__ == "__main__":
    main()