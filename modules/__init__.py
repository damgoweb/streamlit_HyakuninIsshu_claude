#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百人一首クイズアプリ モジュールパッケージ
循環インポートを避けるため、明示的なインポートは行わない
"""

# モジュール名のみをエクスポート（実際のインポートは各ファイルで行う）
__all__ = [
    'data_manager',
    'session_manager', 
    'quiz_generator',
    'answer_validator',
    'screen_manager',
    'ui_components'
]


"""
百人一首クイズアプリ - モジュールパッケージ

このパッケージには以下のモジュールが含まれます:
- data_manager.py: データ管理機能
- session_manager.py: セッション状態管理機能
- quiz_generator.py: クイズ生成機能（今後実装予定）
- ui_components.py: UI コンポーネント（今後実装予定）
"""

__version__ = "1.1.0"
__author__ = "百人一首クイズアプリ開発チーム"

# # パッケージレベルでのインポート
# from .data_manager import DataManager
# from .session_manager import (
#     SessionManager, get_session_manager, initialize_app_session,
#     get_current_screen, navigate_to, ScreenType, QuizMode, Difficulty,
#     QuizSettings, QuizSession, QuestionResult
# )

# __all__ = [
#     'DataManager',
#     'SessionManager', 'get_session_manager', 'initialize_app_session',
#     'get_current_screen', 'navigate_to', 
#     'ScreenType', 'QuizMode', 'Difficulty',
#     'QuizSettings', 'QuizSession', 'QuestionResult',
#     'UIComponents'
# ]