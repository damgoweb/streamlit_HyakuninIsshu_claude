#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百人一首クイズアプリ - メインアプリケーション
UIコンポーネント・画面遷移ロジック統合版
"""

import streamlit as st
import json
import random
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# モジュールのインポート（循環インポートを避けるため順序を調整）
try:
    # 基本モジュールから順にインポート
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # データ管理とクイズ生成
    from modules.data_manager import DataManager
    from modules.quiz_generator import QuizGenerator, QuizType, QuizQuestion
    from modules.answer_validator import AnswerValidator, AnswerStatus, AnswerResult
    
    # セッション管理（他のモジュールに依存する可能性）
    from modules.session_manager import (
        get_session_manager, initialize_app_session, 
        ScreenType, QuizMode, Difficulty, QuizSettings
    )
    
    # UI関連（他のモジュールに依存）
    from modules.ui_components import (
        UIComponents, UITheme, UIConfig,
        create_ui_components, format_time, format_score
    )
    
    # 画面遷移管理（最も依存関係が多い）
    from modules.screen_manager import (
        QuizScreenManager, TransitionType, UpdateStrategy,
        get_screen_manager, navigate_with_transition,
        optimized_update, track_screen_time
    )
    
except ImportError as e:
    st.error(f"⚠️ 必要なモジュールが見つかりません: {e}")
    st.info("📝 必要なファイルを配置してください。")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# ページ設定
st.set_page_config(
    page_title="百人一首クイズアプリ",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# クイズモードのマッピング
QUIZ_MODE_MAPPING = {
    QuizMode.UPPER_TO_LOWER: QuizType.UPPER_TO_LOWER,
    QuizMode.LOWER_TO_UPPER: QuizType.LOWER_TO_UPPER,
    QuizMode.AUTHOR_TO_POEM: QuizType.AUTHOR_TO_POEM,
    QuizMode.POEM_TO_AUTHOR: QuizType.POEM_TO_AUTHOR
}

# 難易度マッピング
DIFFICULTY_MAPPING = {
    Difficulty.BEGINNER: "beginner",
    Difficulty.INTERMEDIATE: "intermediate",
    Difficulty.ADVANCED: "advanced"
}

def initialize_session():
    """セッション状態の初期化"""
    # 新しいセッション管理システムを初期化
    initialize_app_session()
    
    # 画面遷移マネージャーの初期化
    screen_manager = get_screen_manager()
    
    # UIコンポーネントの初期化
    if 'ui_components' not in st.session_state:
        st.session_state.ui_components = create_ui_components(UITheme.DEFAULT)
    
    # その他の初期化
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = True
        st.session_state.poems_data = None
        st.session_state.data_manager = None
        st.session_state.quiz_generator = None
        st.session_state.answer_validator = None
        st.session_state.current_quiz_question = None
        st.session_state.question_start_time = None
        st.session_state.answered = False
        st.session_state.user_answer = None
        st.session_state.hint_used = False
        
        # 初期画面を設定
        if not screen_manager.get_current_screen():
            screen_manager.navigate_to('start')

def load_app_data():
    """アプリケーションデータの読み込み"""
    sm = get_session_manager()
    
    # DataManagerの取得または作成
    if 'data_manager' not in st.session_state or st.session_state.data_manager is None:
        st.session_state.data_manager = DataManager()
    
    dm = st.session_state.data_manager
    
    # AnswerValidatorの初期化
    if 'answer_validator' not in st.session_state or st.session_state.answer_validator is None:
        st.session_state.answer_validator = AnswerValidator()
    
    # データがまだ読み込まれていない場合
    if not dm.is_loaded:
        with st.spinner("📚 百人一首データを読み込み中..."):
            success, data, message = dm.load_poem_data()
            
            if success:
                st.session_state.poems_data = data
                st.session_state.quiz_generator = QuizGenerator(data)
                return True, message
            else:
                return False, message
    else:
        st.session_state.poems_data = dm.get_all_poems()
        if st.session_state.quiz_generator is None:
            st.session_state.quiz_generator = QuizGenerator(st.session_state.poems_data)
        return True, "データは既に読み込まれています"

def generate_next_question() -> Optional[QuizQuestion]:
    """次の問題を生成する"""
    sm = get_session_manager()
    quiz_session = sm.get_quiz_session()
    
    if not quiz_session or not st.session_state.quiz_generator:
        return None
    
    # 設定から問題タイプと難易度を取得
    quiz_type = QUIZ_MODE_MAPPING.get(quiz_session.settings.mode, QuizType.UPPER_TO_LOWER)
    difficulty = DIFFICULTY_MAPPING.get(quiz_session.settings.difficulty, "beginner")
    
    # 既に回答済みの問題は除外
    exclude_numbers = []
    if st.session_state.answer_validator:
        answered_results = st.session_state.answer_validator.get_statistics().answer_results
        exclude_numbers = [result.poem_number for result in answered_results]
    
    # 問題を生成
    question = st.session_state.quiz_generator.generate_question(
        quiz_type=quiz_type,
        difficulty=difficulty,
        exclude_numbers=exclude_numbers
    )
    
    return question

def generate_hint(question: QuizQuestion) -> str:
    """問題に応じたヒントを生成"""
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

def show_start_screen():
    """スタート画面（UIコンポーネント・画面遷移管理使用）"""
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
    """クイズ画面（画面遷移管理統合版）"""
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
    
    # 進捗情報取得
    validator_stats = st.session_state.answer_validator.get_current_score()
    answered_count = validator_stats['total_questions']
    total_questions = quiz_session.settings.total_questions
    
    # ヘッダー表示（部分更新）
    optimized_update('quiz_header',
                    lambda: ui.render_quiz_header(
                        current_question=answered_count + 1,
                        total_questions=total_questions,
                        score=validator_stats['correct_answers'],
                        accuracy=validator_stats['accuracy']
                    ),
                    data={'count': answered_count, 'score': validator_stats['correct_answers']},
                    strategy=UpdateStrategy.PARTIAL)
    
    # クイズが完了している場合
    if answered_count >= total_questions:
        ui.render_success_message("クイズ完了！", show_balloons=True)
        
        performance = st.session_state.answer_validator.get_statistics().get_performance_analysis()
        st.info(f"🏆 最終成績: {performance['overall_grade']}")
        
        if ui.render_next_question_button(is_last_question=True):
            # クイズ完了処理
            screen_manager.complete_quiz()
            st.rerun()
        return
    
    # 現在の問題を取得または生成
    if st.session_state.current_quiz_question is None:
        question = generate_next_question()
        if question:
            st.session_state.current_quiz_question = question
            st.session_state.answered = False
            st.session_state.user_answer = None
            st.session_state.question_start_time = time.time()
            st.session_state.hint_used = False
            # 画面を更新必要としてマーク
            screen_manager.mark_screen_dirty('quiz')
        else:
            ui.render_error_message("問題を生成できませんでした")
            return
    
    current_question = st.session_state.current_quiz_question
    
    # 問題表示
    ui.render_question_display(
        question_text=current_question.question_text,
        poem_number=current_question.poem_number,
        additional_info=f"問題タイプ: {current_question.quiz_type.value}"
    )
    
    # 回答済みでない場合
    if not st.session_state.answered:
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
            
            # SessionManagerにも記録
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
                # 次の問題へ遷移
                screen_manager.navigate_to_next_question()
                
                # 状態をリセット
                st.session_state.current_quiz_question = None
                st.session_state.answered = False
                st.session_state.user_answer = None
                st.session_state.hint_used = False
                if hasattr(st.session_state, 'current_answer_result'):
                    delattr(st.session_state, 'current_answer_result')
                
                # 最後の問題の場合は結果画面へ
                if answered_count + 1 >= total_questions:
                    screen_manager.complete_quiz()
                
                st.rerun()
    
    # クイズ中断ボタン
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("🚪 クイズを中断", type="secondary"):
            if screen_manager.handle_quiz_interruption():
                st.rerun()

def show_result_screen():
    """結果画面（画面遷移管理統合版）"""
    ui = st.session_state.ui_components
    screen_manager = get_screen_manager()
    
    if not st.session_state.answer_validator:
        ui.render_error_message("結果データがありません")
        if st.button("🏠 スタート画面に戻る"):
            screen_manager.navigate_home()
            st.rerun()
        return
    
    # 統計情報取得
    stats = st.session_state.answer_validator.get_statistics()
    score_info = st.session_state.answer_validator.get_current_score()
    
    # ヘッダー表示（キャッシュ利用）
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
        screen_manager.navigate_home()
        st.rerun()
    elif action == 'restart':
        screen_manager.restart_quiz()
        st.rerun()
    elif action == 'review':
        navigate_with_transition('review', TransitionType.FADE)
        st.rerun()
    elif action == 'challenge':
        navigate_with_transition('start', TransitionType.ZOOM)
        st.rerun()

def show_settings_screen():
    """設定画面"""
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
    """復習画面"""
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

def main():
    """メインアプリケーション"""
    # セッション初期化
    initialize_session()
    
    # UIコンポーネント取得
    ui = st.session_state.ui_components
    
    # マネージャー取得
    sm = get_session_manager()
    screen_manager = get_screen_manager()
    
    # データの読み込み
    data_success, data_message = load_app_data()
    
    if not data_success:
        ui.render_error_message(data_message, show_details=True, details="""
        考えられる原因:
        1. data/hyakunin_isshu.json ファイルが存在しない
        2. JSONファイルの形式が不正
        3. ファイルの文字エンコーディングが UTF-8 でない
        4. 必須フィールドが不足している
        """)
        return
    
    # 現在の画面を取得（画面遷移マネージャーから）
    current_screen = screen_manager.get_current_screen()
    
    # 画面マッピング
    screen_map = {
        'start': (ScreenType.START, show_start_screen),
        'quiz': (ScreenType.QUIZ, show_quiz_screen),
        'result': (ScreenType.RESULT, show_result_screen),
        'settings': (ScreenType.SETTINGS, show_settings_screen),
        'review': (ScreenType.REVIEW, show_review_screen)
    }
    
    # ナビゲーションバー表示（結果画面への直接遷移は制限）
    if current_screen:
        screen_type = screen_map.get(current_screen, (ScreenType.START, None))[0]
        
        def safe_navigate(screen: str):
            # 結果画面への直接遷移は制限
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
        show_func()
    else:
        # デフォルトはスタート画面
        show_start_screen()

if __name__ == "__main__":
    main()