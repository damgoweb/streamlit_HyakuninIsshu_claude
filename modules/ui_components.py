#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百人一首クイズアプリ - UIコンポーネントモジュール
基本的なUIコンポーネントとスタイリング機能を提供
"""

import streamlit as st
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import time


class UITheme(Enum):
    """UIテーマの定義"""
    DEFAULT = "default"
    TRADITIONAL = "traditional"
    MODERN = "modern"


@dataclass
class UIConfig:
    """UI設定クラス"""
    theme: UITheme = UITheme.DEFAULT
    show_progress_bar: bool = True
    show_timer: bool = True
    enable_animations: bool = True
    button_style: str = "primary"
    card_style: str = "default"


class UIComponents:
    """UI コンポーネントクラス"""
    
    def __init__(self, config: UIConfig = None):
        """
        UIコンポーネントの初期化
        
        Args:
            config: UI設定
        """
        self.config = config or UIConfig()
        self._apply_custom_styles()
    
    def _apply_custom_styles(self):
        """カスタムCSSスタイルを適用"""
        if self.config.theme == UITheme.TRADITIONAL:
            css = self._get_traditional_styles()
        elif self.config.theme == UITheme.MODERN:
            css = self._get_modern_styles()
        else:
            css = self._get_default_styles()
        
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    def _get_default_styles(self) -> str:
        """デフォルトスタイルCSS"""
        return """
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {
            .question-card {
                background: #2d3748 !important;
                border-left-color: #48bb78 !important;
            }
            
            .question-card h3 {
                color: #f7fafc !important;
            }
            
            .poem-display {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
                color: #f7fafc !important;
            }
            
            .poem-display h2, .poem-display h3, .poem-display h4 {
                color: #f7fafc !important;
            }
            
            .poem-display p {
                color: #e2e8f0 !important;
            }
            
            .choice-button {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
                color: #f7fafc !important;
            }
            
            .choice-button:hover {
                background: linear-gradient(45deg, #4299e1, #3182ce) !important;
                color: white !important;
            }
        }
        
        .quiz-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 15px;
            margin: 1rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            color: white;
        }
        
        .question-card {
            background: white;
            padding: 2rem;
            border-radius: 10px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
        }
        
        .question-card h3 {
            color: #1a202c !important;
            font-weight: bold;
        }
        
        .poem-display {
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            padding: 1.5rem;
            border-radius: 10px;
            border: 1px solid #cbd5e1;
            font-family: 'Noto Serif JP', serif;
            text-align: center;
            margin: 1rem 0;
        }
        
        .poem-display h2 {
            color: #1a202c !important;
            font-size: 1.5rem !important;
            font-weight: bold !important;
            line-height: 1.8 !important;
            margin: 0.5rem 0 !important;
        }
        
        .poem-display p {
            color: #2d3748 !important;
            font-weight: 500 !important;
        }
        
        .choice-button {
            background: linear-gradient(45deg, #f3f4f6, #e5e7eb);
            border: 2px solid #d1d5db;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #1a202c !important;
            font-weight: 500;
        }
        
        .choice-button:hover {
            background: linear-gradient(45deg, #3b82f6, #1d4ed8);
            color: white !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        }
        
        .correct-answer {
            background: linear-gradient(45deg, #10b981, #059669) !important;
            color: white !important;
            border-color: #059669 !important;
        }
        
        .wrong-answer {
            background: linear-gradient(45deg, #ef4444, #dc2626) !important;
            color: white !important;
            border-color: #dc2626 !important;
        }
        
        .score-display {
            background: linear-gradient(135deg, #fbbf24, #f59e0b);
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            color: white;
            font-weight: bold;
            margin: 1rem 0;
        }
        
        .progress-container {
            background: #f3f4f6;
            border-radius: 20px;
            padding: 5px;
            margin: 1rem 0;
        }
        
        .result-card {
            padding: 2rem;
            border-radius: 15px;
            margin: 1rem 0;
            text-align: center;
        }
        
        .result-excellent {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
        }
        
        .result-good {
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
        }
        
        .result-average {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
        }
        
        .result-poor {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
        }
        
        /* モバイル対応 */
        @media (max-width: 768px) {
            .question-card {
                padding: 1rem;
            }
            
            .poem-display h2 {
                font-size: 1.2rem !important;
            }
            
            .choice-button {
                padding: 0.8rem;
                font-size: 0.95rem;
            }
        }
        """
    
    def _get_traditional_styles(self) -> str:
        """和風スタイルCSS"""
        return """
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {
            .quiz-card {
                background: linear-gradient(135deg, #5d4037, #6d4c41) !important;
                border-color: #8d6e63 !important;
                color: #fff3e0 !important;
            }
            
            .question-card {
                background: #37474f !important;
                border-color: #8d6e63 !important;
                color: #fff3e0 !important;
            }
            
            .question-card h3 {
                color: #fff3e0 !important;
            }
            
            .poem-display {
                background: #455a64 !important;
                border-color: #8d6e63 !important;
                color: #fff3e0 !important;
            }
            
            .poem-display h2, .poem-display p {
                color: #fff3e0 !important;
            }
            
            .choice-button {
                background: #455a64 !important;
                border-color: #8d6e63 !important;
                color: #fff3e0 !important;
            }
            
            .choice-button:hover {
                background: #8d6e63 !important;
                color: #fff3e0 !important;
            }
        }
        
        .quiz-card {
            background: linear-gradient(135deg, #8b4513, #a0522d);
            padding: 2rem;
            border-radius: 5px;
            margin: 1rem 0;
            border: 3px solid #daa520;
            color: #fff8dc;
        }
        
        .question-card {
            background: #fff8dc;
            padding: 2rem;
            border-radius: 5px;
            border: 2px solid #daa520;
            box-shadow: 0 2px 10px rgba(139, 69, 19, 0.3);
            margin: 1rem 0;
        }
        
        .question-card h3 {
            color: #5d4037 !important;
            font-weight: bold;
        }
        
        .choice-button {
            background: #fff8dc;
            border: 2px solid #daa520;
            border-radius: 5px;
            padding: 1rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #5d4037 !important;
            font-weight: 500;
        }
        
        .choice-button:hover {
            background: #daa520;
            color: #fff8dc !important;
        }
        
        .poem-display {
            background: #fff8dc;
            padding: 2rem;
            border-radius: 5px;
            border: 3px solid #daa520;
            font-family: 'Noto Serif JP', serif;
            text-align: center;
            margin: 1rem 0;
            font-size: 1.1rem;
        }
        
        .poem-display h2 {
            color: #5d4037 !important;
            font-weight: bold !important;
        }
        
        .poem-display p {
            color: #6d4c41 !important;
        }
        
        /* モバイル対応 */
        @media (max-width: 768px) {
            .quiz-card {
                padding: 1.5rem;
            }
            
            .question-card {
                padding: 1rem;
            }
            
            .poem-display {
                padding: 1.5rem;
                font-size: 1rem;
            }
            
            .choice-button {
                padding: 0.8rem;
            }
        }
        """
    
    def _get_modern_styles(self) -> str:
        """モダンスタイルCSS"""
        return """
        /* ダークモード対応 */
        @media (prefers-color-scheme: dark) {
            .question-card {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
            }
            
            .question-card h3, .question-card h2, .question-card p {
                color: #f7fafc !important;
            }
            
            .poem-display {
                background: #1a202c !important;
                border-color: #4a5568 !important;
            }
            
            .poem-display h2, .poem-display h3, .poem-display p {
                color: #f7fafc !important;
            }
            
            .choice-button {
                background: #2d3748 !important;
                border-color: #4a5568 !important;
                color: #f7fafc !important;
            }
            
            .choice-button:hover {
                background: #6366f1 !important;
                color: white !important;
                box-shadow: 0 6px 20px rgba(99, 102, 241, 0.5) !important;
            }
        }
        
        .quiz-card {
            background: linear-gradient(135deg, #1e293b, #334155);
            padding: 2rem;
            border-radius: 20px;
            margin: 1rem 0;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
            color: white;
        }
        
        .question-card {
            background: white;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            margin: 1rem 0;
            border: 1px solid #e2e8f0;
        }
        
        .question-card h3 {
            color: #1a202c !important;
            font-weight: 600;
        }
        
        .poem-display {
            background: linear-gradient(135deg, #f8fafc, #e2e8f0);
            padding: 2rem;
            border-radius: 12px;
            border: 1px solid #cbd5e1;
            margin: 1rem 0;
        }
        
        .poem-display h2 {
            color: #0f172a !important;
            font-size: 1.5rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.025em;
        }
        
        .choice-button {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
            color: #1a202c !important;
            font-weight: 500;
        }
        
        .choice-button:hover {
            background: #6366f1;
            color: white !important;
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.3);
        }
        
        /* モバイル最適化 */
        @media (max-width: 768px) {
            .quiz-card {
                padding: 1.5rem;
            }
            
            .question-card {
                padding: 1rem;
            }
            
            .poem-display {
                padding: 1.5rem;
            }
            
            .poem-display h2 {
                font-size: 1.25rem !important;
            }
            
            .choice-button {
                padding: 1rem;
            }
        }
        """

    # ===== スタート画面UI =====
    
    def render_start_screen_header(self, title: str = "🎌 百人一首クイズアプリ") -> None:
        """
        スタート画面のヘッダーを描画
        
        Args:
            title: アプリタイトル
        """
        st.markdown(f"""
        <div class="quiz-card">
            <h1 style="text-align: center; margin-bottom: 1rem;">{title}</h1>
            <p style="text-align: center; opacity: 0.9;">
                日本古典文学の傑作「百人一首」で遊びながら学びましょう
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_game_stats(self, 
                         total_poems: int,
                         total_authors: int, 
                         quiz_questions: int = 10,
                         difficulty: str = "初級") -> None:
        """
        ゲーム統計情報を表示
        
        Args:
            total_poems: 総歌数
            total_authors: 作者数
            quiz_questions: クイズ問題数
            difficulty: 難易度
        """
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📚 収録歌数", f"{total_poems}首")
        
        with col2:
            st.metric("👤 作者数", f"{total_authors}人")
        
        with col3:
            st.metric("❓ 出題数", f"{quiz_questions}問")
        
        with col4:
            st.metric("📊 難易度", difficulty)
    
    def render_game_mode_selector(self,
                                 modes: Dict[str, str],
                                 default_mode: str = "upper_to_lower") -> str:
        """
        ゲームモード選択UI
        
        Args:
            modes: モード選択肢の辞書
            default_mode: デフォルトモード
            
        Returns:
            選択されたモード
        """
        st.markdown("### 🎯 クイズモードを選択")
        
        selected_mode = st.selectbox(
            "出題形式:",
            options=list(modes.keys()),
            format_func=lambda x: modes[x],
            help="クイズの出題形式を選択してください"
        )
        
        return selected_mode
    
    def render_difficulty_selector(self,
                                  difficulties: Dict[str, str],
                                  default: str = "beginner") -> str:
        """
        難易度選択UI
        
        Args:
            difficulties: 難易度選択肢の辞書
            default: デフォルト難易度
            
        Returns:
            選択された難易度
        """
        st.markdown("### 📊 難易度を選択")
        
        selected_difficulty = st.selectbox(
            "問題の難しさ:",
            options=list(difficulties.keys()),
            format_func=lambda x: difficulties[x],
            help="出題する歌の難易度を選択してください"
        )
        
        return selected_difficulty
    
    def render_quiz_settings(self) -> Dict[str, Any]:
        """
        クイズ設定UI
        
        Returns:
            設定値の辞書
        """
        st.markdown("### ⚙️ 詳細設定")
        
        col1, col2 = st.columns(2)
        
        with col1:
            question_count = st.selectbox(
                "出題数",
                [5, 10, 20, 50, 100],
                index=1,
                help="クイズの問題数を選択してください"
            )
            
            enable_hints = st.checkbox(
                "ヒント機能を有効にする",
                value=True,
                help="問題でヒントを表示できるようになります"
            )
        
        with col2:
            enable_timer = st.checkbox(
                "制限時間を設定",
                value=False,
                help="各問題に制限時間を設けます"
            )
            
            if enable_timer:
                time_limit = st.slider(
                    "制限時間（秒）",
                    min_value=10,
                    max_value=60,
                    value=30,
                    step=5
                )
            else:
                time_limit = None
            
            show_explanations = st.checkbox(
                "解説を表示する",
                value=True,
                help="回答後に詳しい解説を表示します"
            )
        
        return {
            'question_count': question_count,
            'enable_hints': enable_hints,
            'enable_timer': enable_timer,
            'time_limit': time_limit,
            'show_explanations': show_explanations
        }
    
    def render_start_button(self, 
                           on_click: Optional[Callable] = None,
                           text: str = "🚀 クイズを開始") -> bool:
        """
        スタートボタンを描画
        
        Args:
            on_click: クリック時のコールバック関数
            text: ボタンテキスト
            
        Returns:
            ボタンがクリックされたかどうか
        """
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            clicked = st.button(
                text,
                type="primary",
                use_container_width=True,
                help="クイズを開始します"
            )
            
            if clicked and on_click:
                on_click()
            
            return clicked

    # ===== クイズ画面UI =====
    
    def render_quiz_header(self,
                          current_question: int,
                          total_questions: int,
                          score: int,
                          accuracy: float = 0.0) -> None:
        """
        クイズ画面のヘッダー（進捗・スコア表示）
        
        Args:
            current_question: 現在の問題番号
            total_questions: 総問題数
            score: 現在のスコア
            accuracy: 正答率
        """
        st.markdown("### 🎯 クイズ進行中")
        
        # 進捗表示
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("問題", f"{current_question}/{total_questions}")
        
        with col2:
            st.metric("スコア", f"{score}")
        
        with col3:
            st.metric("正答率", f"{accuracy:.1f}%")
        
        with col4:
            remaining = total_questions - current_question + 1
            st.metric("残り", f"{remaining}問")
        
        # プログレスバー
        if self.config.show_progress_bar:
            progress = (current_question - 1) / total_questions if total_questions > 0 else 0
            st.progress(progress)
    
    def render_question_display(self,
                               question_text: str,
                               poem_number: int = None,
                               additional_info: str = None) -> None:
        """
        問題文表示UI
        
        Args:
            question_text: 問題文
            poem_number: 歌番号
            additional_info: 追加情報
        """
        st.markdown("---")
        
        poem_info = f" ({poem_number}番)" if poem_number else ""
        
        # ダークモード対応の改善されたHTML
        st.markdown(f"""
        <div class="question-card">
            <h3 style="margin-bottom: 1rem;">
                📝 問題{poem_info}
            </h3>
            <div class="poem-display">
                <h2 style="margin: 0;">
                    {question_text}
                </h2>
            </div>
            {f"<p style='text-align: center; opacity: 0.8; margin-top: 1rem;'>{additional_info}</p>" if additional_info else ""}
        </div>
        """, unsafe_allow_html=True)
    
    def render_choice_buttons(self,
                             choices: List[str],
                             correct_index: int = None,
                             user_answer_index: int = None,
                             answered: bool = False,
                             on_select: Optional[Callable[[int], None]] = None) -> Optional[int]:
        """
        選択肢ボタンUI
        
        Args:
            choices: 選択肢リスト
            correct_index: 正解のインデックス
            user_answer_index: ユーザーの回答インデックス  
            answered: 回答済みかどうか
            on_select: 選択時のコールバック関数
            
        Returns:
            選択された選択肢のインデックス
        """
        st.markdown("### 🔤 回答を選択してください")
        
        if not answered:
            # 回答前 - ラジオボタンで選択
            choice_labels = [f"{chr(65 + i)}. {choice}" for i, choice in enumerate(choices)]
            
            selected = st.radio(
                "選択肢:",
                options=list(range(len(choices))),
                format_func=lambda x: choice_labels[x],
                key="quiz_choice"
            )
            
            return selected
        
        else:
            # 回答後 - 結果表示
            for i, choice in enumerate(choices):
                label = f"{chr(65 + i)}. {choice}"
                
                if i == correct_index:
                    # 正解選択肢
                    st.markdown(f"""
                    <div class="choice-button correct-answer">
                        ✅ {label} <strong>(正解)</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                elif i == user_answer_index and i != correct_index:
                    # ユーザーの間違った選択
                    st.markdown(f"""
                    <div class="choice-button wrong-answer">
                        ❌ {label} <strong>(あなたの回答)</strong>
                    </div>
                    """, unsafe_allow_html=True)
                
                else:
                    # その他の選択肢
                    st.markdown(f"""
                    <div class="choice-button">
                        {label}
                    </div>
                    """, unsafe_allow_html=True)
        
        return None
    
    def render_answer_buttons(self,
                             enable_hint: bool = True,
                             enable_skip: bool = True,
                             on_answer: Optional[Callable] = None,
                             on_hint: Optional[Callable] = None,
                             on_skip: Optional[Callable] = None) -> str:
        """
        回答操作ボタン群
        
        Args:
            enable_hint: ヒントボタンを有効にするか
            enable_skip: スキップボタンを有効にするか
            on_answer: 回答ボタンクリック時のコールバック
            on_hint: ヒントボタンクリック時のコールバック
            on_skip: スキップボタンクリック時のコールバック
            
        Returns:
            クリックされたボタンの種類 ('answer', 'hint', 'skip', None)
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ 回答する", type="primary", use_container_width=True):
                if on_answer:
                    on_answer()
                return 'answer'
        
        with col2:
            if enable_hint:
                if st.button("💡 ヒント", use_container_width=True):
                    if on_hint:
                        on_hint()
                    return 'hint'
            else:
                st.empty()
        
        with col3:
            if enable_skip:
                if st.button("⏭ スキップ", use_container_width=True):
                    if on_skip:
                        on_skip()
                    return 'skip'
            else:
                st.empty()
        
        return None
    
    def render_answer_result(self,
                            is_correct: bool,
                            user_answer: str,
                            correct_answer: str,
                            points: float = 0,
                            time_taken: float = 0,
                            explanation: str = None) -> None:
        """
        回答結果表示UI
        
        Args:
            is_correct: 正解かどうか
            user_answer: ユーザーの回答
            correct_answer: 正しい回答
            points: 獲得ポイント
            time_taken: 回答時間
            explanation: 解説
        """
        st.markdown("---")
        st.markdown("### 📖 回答結果")
        
        if is_correct:
            st.markdown(f"""
            <div class="result-card result-excellent">
                <h3>🎉 正解です！</h3>
                <p>あなたの回答: <strong>{user_answer}</strong></p>
                <p>獲得ポイント: <strong>{points:.1f}点</strong> | 
                   回答時間: <strong>{time_taken:.1f}秒</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            if self.config.enable_animations:
                st.balloons()
        
        else:
            st.markdown(f"""
            <div class="result-card result-poor">
                <h3>❌ 不正解</h3>
                <p>あなたの回答: <strong>{user_answer or '未回答'}</strong></p>
                <p>正解: <strong>{correct_answer}</strong></p>
                <p>回答時間: <strong>{time_taken:.1f}秒</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        # 解説表示（改善版）
        if explanation:
            with st.expander("📚 詳しい解説", expanded=True):
                # 解説を整形して表示
                lines = explanation.split('\n')
                for line in lines:
                    if line.startswith('【'):
                        # セクションヘッダーは強調表示
                        st.markdown(f"**{line}**")
                    elif line.strip() and not line.startswith('※'):
                        # 通常のテキスト
                        if '】' not in line:  # ヘッダー行でない場合
                            st.markdown(f"{line}")
                    elif line.startswith('※'):
                        # 補足情報は斜体で表示
                        st.markdown(f"*{line}*")
                    else:
                        # 空行
                        st.write("")
    
    def render_hint_display(self, hint_text: str) -> None:
        """
        ヒント表示UI
        
        Args:
            hint_text: ヒントテキスト
        """
        st.info(f"💡 **ヒント**: {hint_text}")
    
    def render_next_question_button(self,
                                   is_last_question: bool = False,
                                   on_next: Optional[Callable] = None) -> bool:
        """
        次の問題ボタン
        
        Args:
            is_last_question: 最後の問題かどうか
            on_next: 次へ進む時のコールバック
            
        Returns:
            ボタンがクリックされたかどうか
        """
        button_text = "🏁 クイズ完了 - 結果を見る" if is_last_question else "➡️ 次の問題へ"
        
        clicked = st.button(
            button_text,
            type="primary",
            use_container_width=True
        )
        
        if clicked and on_next:
            on_next()
        
        return clicked

    # ===== 結果画面UI =====
    
    def render_result_header(self,
                            total_questions: int,
                            correct_answers: int,
                            total_points: float,
                            accuracy: float,
                            grade: str) -> None:
        """
        結果画面ヘッダー
        
        Args:
            total_questions: 総問題数
            correct_answers: 正解数
            total_points: 総ポイント
            accuracy: 正答率
            grade: 成績評価
        """
        st.markdown("### 🏆 クイズ結果")
        
        # 成績に応じたスタイル
        if grade in ['S', 'A+', 'A']:
            result_class = "result-excellent"
            message = "🎉 素晴らしい！百人一首マスターです！"
        elif grade in ['B+', 'B']:
            result_class = "result-good"
            message = "🥇 とても良くできました！"
        elif grade in ['C+', 'C']:
            result_class = "result-average"
            message = "🥈 よく頑張りました！"
        else:
            result_class = "result-poor"
            message = "🥉 復習して再挑戦しましょう！"
        
        st.markdown(f"""
        <div class="result-card {result_class}">
            <h2>{message}</h2>
            <h3>最終成績: {grade}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # 基本統計
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("総問題数", total_questions)
        
        with col2:
            st.metric("正解数", correct_answers)
        
        with col3:
            st.metric("正答率", f"{accuracy:.1f}%")
        
        with col4:
            st.metric("総ポイント", f"{total_points:.1f}")
    
    def render_detailed_stats(self,
                             stats: Dict[str, Any]) -> None:
        """
        詳細統計表示
        
        Args:
            stats: 統計データ
        """
        with st.expander("📈 詳細統計"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**回答パフォーマンス**")
                st.write(f"- 平均回答時間: {stats.get('average_time', 0):.1f}秒")
                st.write(f"- 最速回答: {stats.get('fastest_time', 0):.1f}秒")
                st.write(f"- 最遅回答: {stats.get('slowest_time', 0):.1f}秒")
                st.write(f"- ヒント使用: {stats.get('hint_used', 0)}回")
            
            with col2:
                st.write("**問題別統計**")
                st.write(f"- 不正解: {stats.get('incorrect_answers', 0)}問")
                st.write(f"- スキップ: {stats.get('skipped_answers', 0)}問")
                st.write(f"- 平均ポイント: {stats.get('average_points', 0):.2f}")
    
    def render_wrong_answers_list(self,
                                 wrong_answers: List[Dict[str, Any]]) -> None:
        """
        間違えた問題一覧
        
        Args:
            wrong_answers: 間違えた問題のリスト
        """
        if not wrong_answers:
            st.success("🎉 全問正解！素晴らしい成績です！")
            return
        
        st.subheader("📋 復習推奨問題")
        st.write(f"間違えた問題: {len(wrong_answers)}問")
        
        for i, answer in enumerate(wrong_answers, 1):
            with st.expander(f"問題 {i}: {answer.get('poem_number', '不明')}番"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**問題情報**")
                    st.write(f"**問題**: {answer.get('question', '不明')}")
                    st.write(f"**正解**: {answer.get('correct_answer', '不明')}")
                    st.write(f"**あなたの回答**: {answer.get('user_answer', '未回答')}")
                
                with col2:
                    st.write("**詳細情報**")
                    st.write(f"**状態**: {answer.get('status', '不明')}")
                    st.write(f"**回答時間**: {answer.get('time_taken', 0):.1f}秒")
                    if answer.get('hint_used'):
                        st.write("💡 **ヒントを使用**")
    
    def render_action_buttons(self,
                             has_wrong_answers: bool = False,
                             on_restart: Optional[Callable] = None,
                             on_review: Optional[Callable] = None,
                             on_home: Optional[Callable] = None) -> str:
        """
        結果画面のアクションボタン群
        
        Args:
            has_wrong_answers: 間違えた問題があるか
            on_restart: 再開始コールバック
            on_review: 復習コールバック  
            on_home: ホームに戻るコールバック
            
        Returns:
            クリックされたボタンの種類
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏠 スタート画面に戻る", use_container_width=True):
                if on_home:
                    on_home()
                return 'home'
        
        with col2:
            if st.button("🔄 新しいクイズを開始", use_container_width=True):
                if on_restart:
                    on_restart()
                return 'restart'
        
        with col3:
            if has_wrong_answers:
                if st.button("📚 復習モードで再挑戦", type="primary", use_container_width=True):
                    if on_review:
                        on_review()
                    return 'review'
            else:
                if st.button("🎯 難易度を上げて挑戦", type="primary", use_container_width=True):
                    if on_home:
                        on_home()
                    return 'challenge'
        
        return None

    # ===== 共通UIコンポーネント =====
    
    def render_navigation_bar(self,
                             current_screen: str,
                             on_navigate: Optional[Callable[[str], None]] = None) -> None:
        """
        ナビゲーションバー
        
        Args:
            current_screen: 現在の画面
            on_navigate: ナビゲーション時のコールバック
        """
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        screens = {
            'start': ('🏠', 'スタート'),
            'quiz': ('🎯', 'クイズ'),
            'result': ('📊', '結果'),
            'settings': ('⚙️', '設定')
        }
        
        for screen, (icon, label) in screens.items():
            col = [col1, col2, col3, col4][list(screens.keys()).index(screen)]
            
            with col:
                is_current = screen == current_screen
                button_type = "primary" if is_current else "secondary"
                disabled = is_current
                
                if st.button(
                    f"{icon} {label}",
                    type=button_type,
                    disabled=disabled,
                    use_container_width=True
                ):
                    if on_navigate and not is_current:
                        on_navigate(screen)
    
    def render_timer_display(self,
                            remaining_time: int,
                            total_time: int) -> None:
        """
        タイマー表示
        
        Args:
            remaining_time: 残り時間（秒）
            total_time: 総時間（秒）
        """
        if not self.config.show_timer:
            return
        
        progress = remaining_time / total_time if total_time > 0 else 0
        
        # 残り時間に応じて色を変更
        if progress > 0.5:
            color = "#10b981"  # 緑
        elif progress > 0.25:
            color = "#f59e0b"  # 黄
        else:
            color = "#ef4444"  # 赤
        
        st.markdown(f"""
        <div style="
            background: {color};
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            text-align: center;
            font-weight: bold;
            margin: 1rem 0;
        ">
            ⏰ 残り時間: {remaining_time}秒
        </div>
        """, unsafe_allow_html=True)
        
        # プログレスバーも表示
        st.progress(progress)
    
    def render_loading_spinner(self,
                              message: str = "読み込み中...") -> None:
        """
        ローディングスピナー
        
        Args:
            message: 表示メッセージ
        """
        with st.spinner(message):
            time.sleep(0.1)  # 最小表示時間
    
    def render_error_message(self,
                            error_message: str,
                            show_details: bool = False,
                            details: str = None) -> None:
        """
        エラーメッセージ表示
        
        Args:
            error_message: エラーメッセージ
            show_details: 詳細を表示するか
            details: 詳細情報
        """
        st.error(f"❌ {error_message}")
        
        if show_details and details:
            with st.expander("📝 詳細情報"):
                st.code(details)
    
    def render_success_message(self,
                              message: str,
                              show_balloons: bool = False) -> None:
        """
        成功メッセージ表示
        
        Args:
            message: 成功メッセージ
            show_balloons: バルーン演出を表示するか
        """
        st.success(f"✅ {message}")
        
        if show_balloons and self.config.enable_animations:
            st.balloons()
    
    def render_info_message(self,
                           message: str,
                           icon: str = "ℹ️") -> None:
        """
        情報メッセージ表示
        
        Args:
            message: 情報メッセージ
            icon: アイコン
        """
        st.info(f"{icon} {message}")
    
    def render_warning_message(self,
                              message: str) -> None:
        """
        警告メッセージ表示
        
        Args:
            message: 警告メッセージ
        """
        st.warning(f"⚠️ {message}")

    # ===== データ表示コンポーネント =====
    
    def render_poem_card(self,
                        poem_data: Dict[str, Any],
                        show_full_info: bool = False) -> None:
        """
        歌カード表示
        
        Args:
            poem_data: 歌のデータ
            show_full_info: 詳細情報を表示するか
        """
        number = poem_data.get('number', poem_data.get('id', '不明'))
        upper = poem_data.get('upper', '不明')
        lower = poem_data.get('lower', '不明')
        author = poem_data.get('author', '不明')
        
        # 全文（上の句 + 下の句）
        full_poem = f"{upper} {lower}"
        
        st.markdown(f"""
        <div class="poem-display">
            <h4 style="margin-bottom: 0.5rem; color: #6b7280;">
                {number}番
            </h4>
            <p style="font-size: 1.3rem; margin: 0.5rem 0; line-height: 1.8; font-weight: bold;">
                {full_poem}
            </p>
            <p style="margin-top: 1rem; font-size: 0.9rem; color: #6b7280;">
                — {author}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if show_full_info:
            with st.expander("📚 詳細情報"):
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'reading' in poem_data and poem_data['reading']:
                        st.write(f"**読み**: {poem_data['reading']}")
                    if 'season' in poem_data and poem_data['season']:
                        st.write(f"**季節**: {poem_data['season']}")
                    if 'theme' in poem_data and poem_data['theme']:
                        st.write(f"**主題**: {poem_data['theme']}")
                
                with col2:
                    if 'period' in poem_data and poem_data['period']:
                        st.write(f"**時代**: {poem_data['period']}")
                    if 'collection' in poem_data and poem_data['collection']:
                        st.write(f"**出典**: {poem_data['collection']}")
                    if 'technique' in poem_data and poem_data['technique']:
                        st.write(f"**技法**: {poem_data['technique']}")
                
                if 'translation' in poem_data and poem_data['translation']:
                    st.write(f"**現代語訳**: {poem_data['translation']}")
                
                if 'description' in poem_data and poem_data['description']:
                    st.write(f"**解説**: {poem_data['description']}")
                
                if 'explanation' in poem_data and poem_data['explanation']:
                    st.write(f"**補足**: {poem_data['explanation']}")
    
    def render_statistics_dashboard(self,
                                   stats: Dict[str, Any]) -> None:
        """
        統計ダッシュボード
        
        Args:
            stats: 統計データ
        """
        st.markdown("### 📊 統計ダッシュボード")
        
        # 主要指標
        col1, col2, col3, col4 = st.columns(4)
        
        metrics = [
            ("総プレイ回数", stats.get('total_games', 0), "🎮"),
            ("平均正答率", f"{stats.get('average_accuracy', 0):.1f}%", "🎯"),
            ("最高スコア", stats.get('best_score', 0), "🏆"),
            ("学習済み歌数", stats.get('learned_poems', 0), "📚")
        ]
        
        for i, (label, value, icon) in enumerate(metrics):
            col = [col1, col2, col3, col4][i]
            with col:
                st.metric(f"{icon} {label}", value)
        
        # 進捗グラフ（簡易版）
        if stats.get('progress_data'):
            st.markdown("#### 📈 学習進捗")
            progress_data = stats['progress_data']
            
            # 簡易的な進捗表示
            for difficulty, progress in progress_data.items():
                st.write(f"**{difficulty}**: {progress}%")
                st.progress(progress / 100)
    
    def render_achievement_badges(self,
                                 achievements: List[Dict[str, Any]]) -> None:
        """
        達成バッジ表示
        
        Args:
            achievements: 達成項目のリスト
        """
        if not achievements:
            return
        
        st.markdown("### 🏅 達成バッジ")
        
        cols = st.columns(4)
        
        for i, achievement in enumerate(achievements):
            col_index = i % 4
            
            with cols[col_index]:
                badge_icon = achievement.get('icon', '🏅')
                badge_name = achievement.get('name', '不明')
                badge_description = achievement.get('description', '')
                is_earned = achievement.get('earned', False)
                
                if is_earned:
                    st.markdown(f"""
                    <div style="
                        background: linear-gradient(135deg, #fbbf24, #f59e0b);
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: white;
                        margin: 0.5rem 0;
                    ">
                        <div style="font-size: 2rem;">{badge_icon}</div>
                        <div style="font-weight: bold; margin: 0.5rem 0;">{badge_name}</div>
                        <div style="font-size: 0.8rem; opacity: 0.9;">{badge_description}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="
                        background: #f3f4f6;
                        padding: 1rem;
                        border-radius: 10px;
                        text-align: center;
                        color: #6b7280;
                        margin: 0.5rem 0;
                        border: 2px dashed #d1d5db;
                    ">
                        <div style="font-size: 2rem; opacity: 0.5;">{badge_icon}</div>
                        <div style="font-weight: bold; margin: 0.5rem 0;">{badge_name}</div>
                        <div style="font-size: 0.8rem;">未達成</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ===== レスポンシブ対応 =====
    
    def render_mobile_optimized_layout(self,
                                      content_func: Callable,
                                      *args, **kwargs) -> None:
        """
        モバイル最適化レイアウト
        
        Args:
            content_func: コンテンツ描画関数
            *args, **kwargs: content_funcに渡す引数
        """
        # モバイル検出（簡易版）
        is_mobile = st.get_option("browser.gatherUsageStats")  # 代替的な検出方法
        
        if is_mobile:
            # モバイル用の縦レイアウト
            st.markdown("""
            <style>
            .stButton button {
                width: 100%;
                margin: 0.25rem 0;
            }
            .stColumns {
                gap: 0.5rem;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # コンテンツを描画
        content_func(*args, **kwargs)

    # ===== カスタマイズ機能 =====
    
    def set_theme(self, theme: UITheme) -> None:
        """
        UIテーマを変更
        
        Args:
            theme: 新しいテーマ
        """
        self.config.theme = theme
        self._apply_custom_styles()
    
    def update_config(self, **kwargs) -> None:
        """
        UI設定を更新
        
        Args:
            **kwargs: 更新する設定項目
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self._apply_custom_styles()


# ===== ユーティリティ関数 =====

def create_ui_components(theme: UITheme = UITheme.DEFAULT) -> UIComponents:
    """
    UIコンポーネントインスタンスを作成
    
    Args:
        theme: UIテーマ
        
    Returns:
        UIComponentsインスタンス
    """
    config = UIConfig(theme=theme)
    return UIComponents(config)


def format_time(seconds: float) -> str:
    """
    時間を読みやすい形式でフォーマット
    
    Args:
        seconds: 秒数
        
    Returns:
        フォーマット済み時間文字列
    """
    if seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds:.0f}秒"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}時間{remaining_minutes}分"


def format_score(score: float, max_score: float = None) -> str:
    """
    スコアを読みやすい形式でフォーマット
    
    Args:
        score: スコア
        max_score: 最大スコア
        
    Returns:
        フォーマット済みスコア文字列
    """
    if max_score:
        percentage = (score / max_score) * 100
        return f"{score:.1f}/{max_score:.1f} ({percentage:.1f}%)"
    else:
        return f"{score:.1f}点"


def generate_grade_color(grade: str) -> str:
    """
    成績に応じた色を生成
    
    Args:
        grade: 成績評価
        
    Returns:
        色コード
    """
    grade_colors = {
        'S': '#10b981',   # エメラルドグリーン
        'A+': '#059669',  # 濃いグリーン
        'A': '#34d399',   # ライトグリーン
        'B+': '#3b82f6',  # ブルー
        'B': '#60a5fa',   # ライトブルー
        'C+': '#f59e0b',  # オレンジ
        'C': '#fbbf24',   # ライトオレンジ
        'D': '#ef4444',   # レッド
        'F': '#dc2626'    # ダークレッド
    }
    
    return grade_colors.get(grade, '#6b7280')  # デフォルトはグレー