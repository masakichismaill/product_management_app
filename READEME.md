# 商品管理アプリ

Flaskを使って作成したシンプルな商品管理アプリです。

## 概要
商品を登録し、在庫管理や売上の記録・集計ができます。

---

## 機能
- 商品の追加・編集・削除
- 在庫の増減（販売・補充）
- 売上履歴の表示
- 商品ごとの売上回数の集計
- 日別売上の集計

---

## 使用技術
- Python
- Flask
- SQLite

---

## セットアップ方法

① リポジトリをクローン
```bash
git clone リポジトリURL
cd product_management_app
```
② 必要なライブラリをインストール
```bash
pip install -r requirements.txt
```
③ アプリ起動
```bash
python app.py
```
④ ブラウザでアクセス
```bash
http://127.0.0.1:5000
```