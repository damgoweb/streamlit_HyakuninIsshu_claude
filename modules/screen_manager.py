#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
画面遷移ロジック管理モジュール
画面間の遷移、状態管理、更新最適化を担当
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable, List, Tuple
from enum import Enum
from dataclasses import dataclass, field
import time
from datetime import datetime
import hashlib
import json


class TransitionType(Enum):
    """画面遷移タイプ"""
    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"


class UpdateStrategy(Enum):
    """画面更新戦略"""
    FULL = "full"  # 全体更新
    PARTIAL = "partial"  # 部分更新
    LAZY = "lazy"  # 遅延更新
    CACHED = "cached"  # キャッシュ利用


@dataclass
class ScreenState:
    """画面状態を管理するクラス"""
    screen_id: str
    entered_at: datetime
    previous_screen: Optional[str] = None
    next_screen: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    update_strategy: UpdateStrategy = UpdateStrategy.FULL
    transition_type: TransitionType = TransitionType.NONE
    is_dirty: bool = False  # 更新が必要かどうか
    cache_key: Optional[str] = None


@dataclass
class NavigationRule:
    """画面遷移ルール"""
    from_screen: str
    to_screen: str
    condition: Optional[Callable[[], bool]] = None
    on_transition: Optional[Callable[[], None]] = None
    transition_type: TransitionType = TransitionType.NONE
    confirmation_required: bool = False
    confirmation_message: str = ""


class ScreenManager:
    """画面遷移を管理するマネージャークラス"""
    
    def __init__(self):
        """初期化"""
        self._initialize_session_state()
        self.navigation_rules: List[NavigationRule] = []
        self.screen_stack: List[str] = []
        self.transition_callbacks: Dict[str, List[Callable]] = {}
        self.update_callbacks: Dict[str, Callable] = {}
        
    def _initialize_session_state(self):
        """セッション状態の初期化"""
        if 'screen_manager' not in st.session_state:
            st.session_state.screen_manager = {
                'current_screen': None,
                'screen_states': {},
                'navigation_history': [],
                'transition_in_progress': False,
                'last_update': time.time(),
                'update_count': 0,
                'cache': {}
            }
    
    # ===== 画面状態管理 =====
    
    def get_current_screen(self) -> Optional[str]:
        """現在の画面IDを取得"""
        return st.session_state.screen_manager.get('current_screen')
    
    def get_screen_state(self, screen_id: str = None) -> Optional[ScreenState]:
        """画面状態を取得"""
        if screen_id is None:
            screen_id = self.get_current_screen()
        
        if screen_id:
            return st.session_state.screen_manager['screen_states'].get(screen_id)
        return None
    
    def set_screen_state(self, screen_id: str, state: ScreenState):
        """画面状態を設定"""
        st.session_state.screen_manager['screen_states'][screen_id] = state
    
    def update_screen_data(self, screen_id: str, data: Dict[str, Any], merge: bool = True):
        """画面データを更新"""
        state = self.get_screen_state(screen_id)
        if state:
            if merge:
                state.data.update(data)
            else:
                state.data = data
            state.is_dirty = True
            self.set_screen_state(screen_id, state)
    
    def mark_screen_dirty(self, screen_id: str = None):
        """画面を更新必要としてマーク"""
        if screen_id is None:
            screen_id = self.get_current_screen()
        
        state = self.get_screen_state(screen_id)
        if state:
            state.is_dirty = True
            self.set_screen_state(screen_id, state)
    
    def is_screen_dirty(self, screen_id: str = None) -> bool:
        """画面が更新必要かチェック"""
        state = self.get_screen_state(screen_id)
        return state.is_dirty if state else False
    
    # ===== 画面遷移制御 =====
    
    def navigate_to(self, 
                   target_screen: str, 
                   data: Dict[str, Any] = None,
                   transition_type: TransitionType = TransitionType.NONE,
                   force: bool = False) -> bool:
        """
        指定画面への遷移
        
        Args:
            target_screen: 遷移先画面ID
            data: 遷移時に渡すデータ
            transition_type: 遷移アニメーションタイプ
            force: 強制遷移フラグ
            
        Returns:
            遷移成功の可否
        """
        current_screen = self.get_current_screen()
        
        # 同じ画面への遷移は基本的にスキップ
        if current_screen == target_screen and not force:
            return False
        
        # 遷移中フラグチェック
        if st.session_state.screen_manager['transition_in_progress'] and not force:
            return False
        
        # 遷移ルールのチェック
        if not self._check_navigation_rules(current_screen, target_screen):
            return False
        
        # 遷移開始
        st.session_state.screen_manager['transition_in_progress'] = True
        
        try:
            # 遷移前コールバック実行
            self._execute_transition_callbacks('before', current_screen, target_screen)
            
            # 現在の画面状態を保存
            if current_screen:
                self._save_current_screen_state(current_screen)
            
            # 新しい画面状態を作成
            new_state = ScreenState(
                screen_id=target_screen,
                entered_at=datetime.now(),
                previous_screen=current_screen,
                data=data or {},
                transition_type=transition_type
            )
            
            # 画面遷移実行
            self.set_screen_state(target_screen, new_state)
            st.session_state.screen_manager['current_screen'] = target_screen
            
            # 履歴に追加
            self._add_to_history(current_screen, target_screen)
            
            # スタック管理
            self._update_screen_stack(target_screen)
            
            # 遷移後コールバック実行
            self._execute_transition_callbacks('after', current_screen, target_screen)
            
            # 遷移エフェクト
            if transition_type != TransitionType.NONE:
                self._apply_transition_effect(transition_type)
            
            return True
            
        finally:
            st.session_state.screen_manager['transition_in_progress'] = False
    
    def navigate_back(self) -> bool:
        """前の画面に戻る"""
        current_state = self.get_screen_state()
        if current_state and current_state.previous_screen:
            return self.navigate_to(current_state.previous_screen)
        
        # スタックから前の画面を取得
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()  # 現在の画面を削除
            previous_screen = self.screen_stack[-1]
            return self.navigate_to(previous_screen)
        
        return False
    
    def navigate_home(self) -> bool:
        """ホーム画面に戻る"""
        return self.navigate_to('start', force=True)
    
    # ===== 遷移ルール管理 =====
    
    def add_navigation_rule(self, rule: NavigationRule):
        """画面遷移ルールを追加"""
        self.navigation_rules.append(rule)
    
    def _check_navigation_rules(self, from_screen: str, to_screen: str) -> bool:
        """遷移ルールのチェック"""
        for rule in self.navigation_rules:
            if rule.from_screen == from_screen and rule.to_screen == to_screen:
                if rule.condition and not rule.condition():
                    return False
                
                if rule.confirmation_required:
                    # 確認ダイアログが必要な場合
                    if not self._show_confirmation(rule.confirmation_message):
                        return False
                
                if rule.on_transition:
                    rule.on_transition()
        
        return True
    
    def _show_confirmation(self, message: str) -> bool:
        """確認ダイアログ表示（簡易版）"""
        # Streamlitの制限により、モーダルダイアログは使用できない
        # セッション状態で管理する必要がある
        if 'confirmation_pending' not in st.session_state:
            st.session_state.confirmation_pending = message
            return False
        else:
            result = st.session_state.get('confirmation_result', False)
            del st.session_state.confirmation_pending
            if 'confirmation_result' in st.session_state:
                del st.session_state.confirmation_result
            return result
    
    # ===== コールバック管理 =====
    
    def register_transition_callback(self, 
                                    event: str, 
                                    callback: Callable,
                                    screen_id: Optional[str] = None):
        """画面遷移時のコールバックを登録"""
        key = f"{event}:{screen_id}" if screen_id else event
        if key not in self.transition_callbacks:
            self.transition_callbacks[key] = []
        self.transition_callbacks[key].append(callback)
    
    def _execute_transition_callbacks(self, 
                                     event: str, 
                                     from_screen: str, 
                                     to_screen: str):
        """遷移コールバックを実行"""
        # グローバルコールバック
        for callback in self.transition_callbacks.get(event, []):
            callback(from_screen, to_screen)
        
        # 画面固有のコールバック
        if event == 'before':
            for callback in self.transition_callbacks.get(f"leave:{from_screen}", []):
                callback(from_screen, to_screen)
        elif event == 'after':
            for callback in self.transition_callbacks.get(f"enter:{to_screen}", []):
                callback(from_screen, to_screen)
    
    # ===== 履歴管理 =====
    
    def _add_to_history(self, from_screen: str, to_screen: str):
        """遷移履歴に追加"""
        history = st.session_state.screen_manager['navigation_history']
        history.append({
            'from': from_screen,
            'to': to_screen,
            'timestamp': datetime.now().isoformat()
        })
        
        # 履歴の最大数を制限（メモリ節約）
        max_history = 50
        if len(history) > max_history:
            st.session_state.screen_manager['navigation_history'] = history[-max_history:]
    
    def get_navigation_history(self) -> List[Dict[str, Any]]:
        """遷移履歴を取得"""
        return st.session_state.screen_manager['navigation_history']
    
    def _update_screen_stack(self, screen_id: str):
        """画面スタックを更新"""
        if screen_id in self.screen_stack:
            # 既にスタックにある場合は削除
            self.screen_stack.remove(screen_id)
        self.screen_stack.append(screen_id)
        
        # スタックの最大数を制限
        max_stack = 10
        if len(self.screen_stack) > max_stack:
            self.screen_stack = self.screen_stack[-max_stack:]
    
    # ===== 更新最適化 =====
    
    def should_update(self, 
                     component_id: str, 
                     data: Any = None,
                     strategy: UpdateStrategy = UpdateStrategy.FULL) -> bool:
        """
        コンポーネントの更新が必要かチェック
        
        Args:
            component_id: コンポーネントID
            data: チェック対象データ
            strategy: 更新戦略
            
        Returns:
            更新が必要かどうか
        """
        if strategy == UpdateStrategy.FULL:
            return True
        
        cache = st.session_state.screen_manager['cache']
        cache_key = self._generate_cache_key(component_id, data)
        
        if strategy == UpdateStrategy.CACHED:
            # キャッシュがあれば更新不要
            if cache_key in cache:
                cache_data = cache[cache_key]
                if time.time() - cache_data['timestamp'] < 60:  # 60秒キャッシュ
                    return False
        
        elif strategy == UpdateStrategy.PARTIAL:
            # データが変更された場合のみ更新
            if cache_key in cache:
                if cache[cache_key]['hash'] == self._hash_data(data):
                    return False
        
        elif strategy == UpdateStrategy.LAZY:
            # 一定時間経過後のみ更新
            last_update = cache.get(cache_key, {}).get('timestamp', 0)
            if time.time() - last_update < 1.0:  # 1秒以内は更新しない
                return False
        
        # キャッシュを更新
        cache[cache_key] = {
            'hash': self._hash_data(data),
            'timestamp': time.time()
        }
        
        return True
    
    def _generate_cache_key(self, component_id: str, data: Any) -> str:
        """キャッシュキーを生成"""
        screen_id = self.get_current_screen()
        return f"{screen_id}:{component_id}:{type(data).__name__}"
    
    def _hash_data(self, data: Any) -> str:
        """データのハッシュ値を生成"""
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.md5(data_str.encode()).hexdigest()
        except:
            return hashlib.md5(str(data).encode()).hexdigest()
    
    def clear_cache(self, screen_id: str = None):
        """キャッシュをクリア"""
        if screen_id:
            # 特定画面のキャッシュのみクリア
            cache = st.session_state.screen_manager['cache']
            keys_to_delete = [k for k in cache.keys() if k.startswith(f"{screen_id}:")]
            for key in keys_to_delete:
                del cache[key]
        else:
            # 全キャッシュクリア
            st.session_state.screen_manager['cache'] = {}
    
    # ===== 状態管理 =====
    
    def _save_current_screen_state(self, screen_id: str):
        """現在の画面状態を保存"""
        state = self.get_screen_state(screen_id)
        if state:
            state.is_dirty = False
            self.set_screen_state(screen_id, state)
    
    def reset_screen_state(self, screen_id: str = None):
        """画面状態をリセット"""
        if screen_id:
            if screen_id in st.session_state.screen_manager['screen_states']:
                del st.session_state.screen_manager['screen_states'][screen_id]
        else:
            st.session_state.screen_manager['screen_states'] = {}
    
    # ===== 遷移エフェクト =====
    
    def _apply_transition_effect(self, transition_type: TransitionType):
        """画面遷移エフェクトを適用"""
        if transition_type == TransitionType.FADE:
            # フェードエフェクト用のCSS
            st.markdown("""
            <style>
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            .stApp > div {
                animation: fadeIn 0.3s ease-in;
            }
            </style>
            """, unsafe_allow_html=True)
        
        elif transition_type == TransitionType.SLIDE:
            # スライドエフェクト用のCSS
            st.markdown("""
            <style>
            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
            .stApp > div {
                animation: slideIn 0.3s ease-out;
            }
            </style>
            """, unsafe_allow_html=True)
        
        elif transition_type == TransitionType.ZOOM:
            # ズームエフェクト用のCSS
            st.markdown("""
            <style>
            @keyframes zoomIn {
                from { transform: scale(0.9); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            .stApp > div {
                animation: zoomIn 0.3s ease-out;
            }
            </style>
            """, unsafe_allow_html=True)
    
    # ===== デバッグ機能 =====
    
    def get_debug_info(self) -> Dict[str, Any]:
        """デバッグ情報を取得"""
        return {
            'current_screen': self.get_current_screen(),
            'screen_stack': self.screen_stack,
            'screen_states': list(st.session_state.screen_manager['screen_states'].keys()),
            'history_count': len(st.session_state.screen_manager['navigation_history']),
            'cache_size': len(st.session_state.screen_manager['cache']),
            'update_count': st.session_state.screen_manager['update_count'],
            'transition_in_progress': st.session_state.screen_manager['transition_in_progress']
        }
    
    def render_debug_panel(self):
        """デバッグパネルを表示"""
        with st.expander("🔧 画面遷移デバッグ情報"):
            debug_info = self.get_debug_info()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**画面情報**")
                st.write(f"- 現在の画面: `{debug_info['current_screen']}`")
                st.write(f"- スタック: {debug_info['screen_stack']}")
                st.write(f"- 状態数: {len(debug_info['screen_states'])}")
            
            with col2:
                st.write("**パフォーマンス**")
                st.write(f"- 履歴数: {debug_info['history_count']}")
                st.write(f"- キャッシュ: {debug_info['cache_size']}項目")
                st.write(f"- 更新回数: {debug_info['update_count']}")
            
            if st.button("キャッシュクリア"):
                self.clear_cache()
                st.success("キャッシュをクリアしました")
                st.rerun()
            
            if st.button("履歴クリア"):
                st.session_state.screen_manager['navigation_history'] = []
                st.success("履歴をクリアしました")
                st.rerun()


# ===== クイズ特化の遷移管理 =====

class QuizScreenManager(ScreenManager):
    """クイズアプリ用の画面遷移マネージャー"""
    
    def __init__(self):
        """初期化"""
        super().__init__()
        self._setup_quiz_navigation_rules()
    
    def _setup_quiz_navigation_rules(self):
        """クイズ用の遷移ルールを設定"""
        # スタート画面からクイズ画面への遷移
        self.add_navigation_rule(NavigationRule(
            from_screen='start',
            to_screen='quiz',
            transition_type=TransitionType.SLIDE
        ))
        
        # クイズ画面から結果画面への遷移（条件なし - 手動で制御）
        self.add_navigation_rule(NavigationRule(
            from_screen='quiz',
            to_screen='result',
            transition_type=TransitionType.FADE
        ))
        
        # クイズ中断時の確認
        self.add_navigation_rule(NavigationRule(
            from_screen='quiz',
            to_screen='start',
            confirmation_required=True,
            confirmation_message="クイズを中断しますか？進捗は失われます。"
        ))
    
    def _is_quiz_completed(self) -> bool:
        """クイズが完了しているかチェック"""
        # SessionManagerと連携してチェック（遅延インポート）
        try:
            from .session_manager import get_session_manager
        except ImportError:
            # 相対インポートが失敗した場合
            from modules.session_manager import get_session_manager
            
        sm = get_session_manager()
        quiz_session = sm.get_quiz_session()
        
        if quiz_session:
            # quiz_sessionのprogressから完了状態をチェック
            return quiz_session.progress.is_completed if quiz_session.progress else False
        return False
    
    def navigate_to_next_question(self) -> bool:
        """次の問題へ遷移"""
        # 遅延インポート
        try:
            from .session_manager import get_session_manager
        except ImportError:
            from modules.session_manager import get_session_manager
            
        sm = get_session_manager()
        
        # 次の問題へ進む
        sm.advance_question()
        
        # 画面を更新必要としてマーク
        self.mark_screen_dirty('quiz')
        
        # 更新カウントを増やす
        st.session_state.screen_manager['update_count'] += 1
        
        return True
    
    def complete_quiz(self) -> bool:
        """クイズを完了して結果画面へ遷移"""
        # 遅延インポート
        try:
            from .session_manager import get_session_manager
        except ImportError:
            from modules.session_manager import get_session_manager
            
        sm = get_session_manager()
        
        # クイズ完了処理
        quiz_session = sm.get_quiz_session()
        if quiz_session:
            # 完了状態をセット
            if quiz_session.progress:
                quiz_session.progress.is_completed = True
            
            # 結果データを準備
            result_data = {
                'completed_at': datetime.now().isoformat(),
                'total_questions': quiz_session.settings.total_questions,
                'correct_answers': quiz_session.progress.correct_answers if quiz_session.progress else 0
            }
            
            # 結果画面へ遷移
            return self.navigate_to('result', data=result_data, transition_type=TransitionType.ZOOM)
        
        return False
    
    def restart_quiz(self) -> bool:
        """クイズをリスタート"""
        # 遅延インポート
        try:
            from .session_manager import get_session_manager
        except ImportError:
            from modules.session_manager import get_session_manager
            
        sm = get_session_manager()
        
        # クイズリセット
        sm.reset_quiz()
        
        # 画面状態をリセット
        self.reset_screen_state('quiz')
        self.reset_screen_state('result')
        
        # キャッシュクリア
        self.clear_cache()
        
        # スタート画面へ遷移
        return self.navigate_home()
    
    def handle_quiz_interruption(self) -> bool:
        """クイズ中断処理"""
        # 確認ダイアログを表示
        if 'quiz_interruption_confirmed' not in st.session_state:
            st.warning("⚠️ クイズを中断しますか？")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("はい、中断する", type="secondary"):
                    st.session_state.quiz_interruption_confirmed = True
                    st.rerun()
            
            with col2:
                if st.button("いいえ、続ける", type="primary"):
                    return False
            
            return False
        
        else:
            # 中断確認済み
            del st.session_state.quiz_interruption_confirmed
            return self.restart_quiz()


# ===== ユーティリティ関数 =====

def get_screen_manager() -> QuizScreenManager:
    """画面遷移マネージャーのシングルトンインスタンスを取得"""
    if 'screen_manager_instance' not in st.session_state:
        st.session_state.screen_manager_instance = QuizScreenManager()
    return st.session_state.screen_manager_instance


def navigate_with_transition(target_screen: str, 
                            transition_type: TransitionType = TransitionType.FADE,
                            data: Dict[str, Any] = None) -> bool:
    """遷移エフェクト付きで画面遷移"""
    manager = get_screen_manager()
    return manager.navigate_to(target_screen, data=data, transition_type=transition_type)


def optimized_update(component_id: str, 
                    render_func: Callable,
                    data: Any = None,
                    strategy: UpdateStrategy = UpdateStrategy.PARTIAL):
    """最適化された更新処理"""
    manager = get_screen_manager()
    
    if manager.should_update(component_id, data, strategy):
        render_func()
        st.session_state.screen_manager['update_count'] += 1


def with_loading_state(func: Callable) -> Callable:
    """ローディング状態を表示するデコレータ"""
    def wrapper(*args, **kwargs):
        with st.spinner("読み込み中..."):
            return func(*args, **kwargs)
    return wrapper


def track_screen_time(screen_id: str):
    """画面滞在時間を追跡"""
    manager = get_screen_manager()
    state = manager.get_screen_state(screen_id)
    
    if state:
        elapsed = (datetime.now() - state.entered_at).total_seconds()
        return elapsed
    return 0