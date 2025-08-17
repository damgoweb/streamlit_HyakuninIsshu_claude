#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
データ管理モジュール
百人一首データの読み込みと管理を担当
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import random


class DataManager:
    """百人一首データを管理するクラス"""
    
    def __init__(self, data_file: str = "data/hyakunin_isshu.json"):
        """
        初期化
        
        Args:
            data_file: JSONデータファイルのパス
        """
        self.data_file = data_file
        self.poems_data: List[Dict[str, Any]] = []
        self.is_loaded: bool = False
        self._poems_by_number: Dict[int, Dict[str, Any]] = {}
        self._poems_by_author: Dict[str, List[Dict[str, Any]]] = {}
    
    def load_poem_data(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        百人一首データを読み込む
        
        Returns:
            (成功フラグ, データリスト, メッセージ)
        """
        try:
            # プロジェクトルートからの相対パスを構築
            current_dir = Path(__file__).parent.parent
            file_path = current_dir / self.data_file
            
            if not file_path.exists():
                return False, [], f"データファイルが見つかりません: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データ検証
            if not isinstance(data, list):
                return False, [], "データ形式が不正です（リストである必要があります）"
            
            if len(data) == 0:
                return False, [], "データが空です"
            
            # 必須フィールドの確認（idまたはnumberフィールドを受け入れる）
            required_fields = ['upper', 'lower', 'author']
            for poem in data:
                # idまたはnumberフィールドのチェック
                if 'id' not in poem and 'number' not in poem:
                    return False, [], f"必須フィールド 'id' または 'number' が不足しています"
                
                # idフィールドをnumberフィールドに正規化
                if 'id' in poem and 'number' not in poem:
                    poem['number'] = poem['id']
                elif 'number' not in poem:
                    poem['number'] = poem.get('id', 0)
                
                # その他の必須フィールドのチェック
                for field in required_fields:
                    if field not in poem:
                        return False, [], f"必須フィールド '{field}' が不足しています"
            
            # データを保存
            self.poems_data = data
            self.is_loaded = True
            
            # インデックスを構築
            self._build_indexes()
            
            return True, self.poems_data, f"データを正常に読み込みました（{len(data)}首）"
            
        except json.JSONDecodeError as e:
            return False, [], f"JSONファイルの解析エラー: {e}"
        except Exception as e:
            return False, [], f"データ読み込みエラー: {e}"
    
    def _build_indexes(self):
        """データのインデックスを構築"""
        self._poems_by_number = {}
        self._poems_by_author = {}
        
        for poem in self.poems_data:
            # numberフィールドがない場合はidを使用
            poem_number = poem.get('number', poem.get('id', 0))
            
            # 番号インデックス
            self._poems_by_number[poem_number] = poem
            
            # 作者インデックス
            author = poem['author']
            if author not in self._poems_by_author:
                self._poems_by_author[author] = []
            self._poems_by_author[author].append(poem)
    
    def get_all_poems(self) -> List[Dict[str, Any]]:
        """
        全ての歌データを取得
        
        Returns:
            歌データのリスト
        """
        return self.poems_data
    
    def get_poem_by_number(self, number: int) -> Optional[Dict[str, Any]]:
        """
        番号で歌を取得
        
        Args:
            number: 歌番号（1-100）
            
        Returns:
            歌データまたはNone
        """
        return self._poems_by_number.get(number)
    
    def get_poems_by_author(self, author: str) -> List[Dict[str, Any]]:
        """
        作者で歌を検索
        
        Args:
            author: 作者名
            
        Returns:
            該当する歌のリスト
        """
        return self._poems_by_author.get(author, [])
    
    def search_poems(self, keyword: str) -> List[Dict[str, Any]]:
        """
        キーワードで歌を検索
        
        Args:
            keyword: 検索キーワード
            
        Returns:
            該当する歌のリスト
        """
        if not keyword:
            return []
        
        keyword_lower = keyword.lower()
        results = []
        
        for poem in self.poems_data:
            # 各フィールドで検索
            if (keyword_lower in poem.get('upper', '').lower() or
                keyword_lower in poem.get('lower', '').lower() or
                keyword_lower in poem.get('author', '').lower() or
                keyword_lower in poem.get('reading', '').lower() or
                keyword_lower in poem.get('translation', '').lower()):
                results.append(poem)
        
        return results
    
    def get_random_poems(self, count: int = 10, 
                        exclude_numbers: List[int] = None) -> List[Dict[str, Any]]:
        """
        ランダムに歌を取得
        
        Args:
            count: 取得数
            exclude_numbers: 除外する歌番号のリスト
            
        Returns:
            ランダムに選ばれた歌のリスト
        """
        available_poems = self.poems_data.copy()
        
        if exclude_numbers:
            available_poems = [p for p in available_poems 
                             if p.get('number', p.get('id', 0)) not in exclude_numbers]
        
        if len(available_poems) < count:
            return available_poems
        
        return random.sample(available_poems, count)
    
    def get_poems_by_difficulty(self, difficulty: str = "beginner") -> List[Dict[str, Any]]:
        """
        難易度別に歌を取得
        
        Args:
            difficulty: 難易度（beginner/intermediate/advanced）
            
        Returns:
            該当する歌のリスト
        """
        if difficulty == "beginner":
            # 有名な歌（1-20番、特に有名なもの）
            famous_numbers = [1, 2, 5, 7, 9, 13, 17, 20, 23, 24, 
                            33, 35, 43, 48, 51, 57, 66, 77, 83, 99]
            return [p for p in self.poems_data 
                   if p.get('number', p.get('id', 0)) in famous_numbers]
        
        elif difficulty == "intermediate":
            # 中級（21-60番）
            return [p for p in self.poems_data 
                   if 21 <= p.get('number', p.get('id', 0)) <= 60]
        
        else:  # advanced
            # 全ての歌
            return self.poems_data
    
    def get_data_stats(self) -> Dict[str, Any]:
        """
        データ統計情報を取得
        
        Returns:
            統計情報の辞書
        """
        if not self.is_loaded:
            return {
                'total_poems': 0,
                'unique_authors': 0,
                'average_upper_length': 0,
                'average_lower_length': 0,
                'data_file_path': self.data_file
            }
        
        authors = set(poem['author'] for poem in self.poems_data)
        upper_lengths = [len(poem['upper']) for poem in self.poems_data]
        lower_lengths = [len(poem['lower']) for poem in self.poems_data]
        
        return {
            'total_poems': len(self.poems_data),
            'unique_authors': len(authors),
            'average_upper_length': sum(upper_lengths) / len(upper_lengths) if upper_lengths else 0,
            'average_lower_length': sum(lower_lengths) / len(lower_lengths) if lower_lengths else 0,
            'data_file_path': self.data_file
        }
    
    def validate_data(self) -> Tuple[bool, List[str]]:
        """
        データの整合性を検証
        
        Returns:
            (検証成功フラグ, エラーメッセージのリスト)
        """
        errors = []
        
        if not self.is_loaded:
            return False, ["データが読み込まれていません"]
        
        # 歌番号の重複チェック
        numbers = [poem.get('number', poem.get('id', 0)) for poem in self.poems_data]
        if len(numbers) != len(set(numbers)):
            errors.append("歌番号に重複があります")
        
        # 歌番号の範囲チェック
        for poem in self.poems_data:
            poem_number = poem.get('number', poem.get('id', 0))
            if not (1 <= poem_number <= 100):
                errors.append(f"歌番号が範囲外: {poem_number}")
        
        # 必須フィールドの値チェック
        for poem in self.poems_data:
            poem_number = poem.get('number', poem.get('id', 0))
            if not poem.get('upper'):
                errors.append(f"上の句が空: 歌番号 {poem_number}")
            if not poem.get('lower'):
                errors.append(f"下の句が空: 歌番号 {poem_number}")
            if not poem.get('author'):
                errors.append(f"作者が空: 歌番号 {poem_number}")
        
        return len(errors) == 0, errors
    
    def export_to_json(self, output_file: str) -> bool:
        """
        データをJSONファイルにエクスポート
        
        Args:
            output_file: 出力ファイルパス
            
        Returns:
            成功フラグ
        """
        if not self.is_loaded:
            return False
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.poems_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False


# モジュールレベルの関数（オプション）
def create_data_manager(data_file: str = "data/hyakunin_isshu.json") -> DataManager:
    """
    DataManagerインスタンスを作成
    
    Args:
        data_file: データファイルパス
        
    Returns:
        DataManagerインスタンス
    """
    return DataManager(data_file)