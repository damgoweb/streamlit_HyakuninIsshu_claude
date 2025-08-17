# 百人一首クイズアプリ

Streamlitを使用した百人一首の学習クイズアプリケーションです。

## 機能

### Phase 1: 基本機能
- [x] 上の句→下の句クイズ
- [x] 4択選択肢
- [x] 正誤判定
- [x] 基本スコア表示

### Phase 2: 拡張機能（予定）
- [ ] 複数クイズモード（下の句→上の句、作者→歌）
- [ ] 難易度設定
- [ ] 出題数設定
- [ ] 復習機能

### Phase 3: 学習支援機能（予定）
- [ ] 詳細解説表示
- [ ] ヒント機能
- [ ] 検索機能
- [ ] 学習統計

## セットアップ

### 必要な環境
- Python 3.7以上
- Streamlit

### インストール

1. 必要なパッケージをインストール
```bash
pip install streamlit
```

2. データファイルの配置
`data/hyakunin_isshu.json`に百人一首データを配置してください。

### 実行方法

```bash
streamlit run app.py
```

## プロジェクト構造

```
hyakunin_isshu_quiz/
├── app.py                    # メインアプリケーション
├── data/
│   └── hyakunin_isshu.json  # 百人一首データ
├── modules/
│   ├── __init__.py          # Pythonパッケージ初期化
│   ├── data_manager.py      # データ管理モジュール
│   ├── quiz_generator.py    # クイズ生成モジュール
│   └── ui_components.py     # UI部品モジュール
└── README.md                # プロジェクト説明
```

## データ形式

JSONファイルは以下の形式で構成されています：

```json
[
  {
    "id": 1,
    "author": "天智天皇",
    "upper": "秋の田の かりほの庵の 苫をあらみ",
    "lower": "わが衣手は 露にぬれつつ",
    "reading_upper": "あきのたの かりほのいほの とまをあらみ",
    "reading_lower": "わがころもでは つゆにぬれつつ",
    "description": "歌の解説..."
  }
]
```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。