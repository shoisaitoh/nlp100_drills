#!/usr/bin/env python
#coding: utf-8
#Content-Type: application/json; charset=utf-8
import gzip
import json
import re # 正規表現
import urllib.parse, urllib.request
filename = "jawiki-country.json.gz"
# urllib.parseはURL解析モジュール、requestは開いて読むためのモジュール

def extract_UK():
    # イギリスの本文を戻り値として取得

    # rtは読み込み専用＆テキストモード（いずれもデフォルト）
    with gzip.open(filename, "rt", encoding = "utf-8") as data_file:
        for line in data_file:
            data_json = json.loads(line)# jsonのデータをロードしてpythonのデータ型に変換
            if data_json['title'] == 'イギリス':# タイトルが「イギリス」の時
                return data_json['text']# 本文を戻り値として返す

    raise ValueError("Not Found Article About UK")
    # タイトルがイギリスでないとき例外処理としてValueErrorを出す

def remove_markup(target):
    '''
    MediaWikiマークアップを可能な限り除去する
    引数：
    target -- 対象の文字列
    戻り値：
    マークアップを除去した文字列
    '''

    # 強調マークアップの除去
    pattern = re.compile(r'''
    (\'{2,5})   # 2~5個の'（マークアップの開始）
    (.*?)       # 任意の1文字以上（対象の文字列）
    (\1)        # 1番目のキャプチャと同じ（マークアップの終了）
    ''', re.MULTILINE + re.VERBOSE)
    # MULTILINEは複数行を見るため、VERBOSEは正規表現中にコメントするため
    target = pattern.sub(r'\2', target)

    # 内部リンクの除去、ファイルの除去
    pattern = re.compile(r'''
    \[\[     # "[["(マークアップの開始)
    (?:      # キャプチャ対象外のグループ開始
        [^|]*? # '|'以外の文字が0文字以上、最短一致
        \]     # '|'
    )*?       # グループ終了、このグループが0以上出現、最短一致
    ([^|]*?) # キャプチャ対象、'|'以外が0文字出現、最短一致（表示対象の文字列）
    \]\]     # ']]'（マークアップの終了）
    ''', re.MULTILINE + re.VERBOSE)
    target = pattern.sub(r'\1', target)

     # Template:Langの除去        {{lang|言語タグ|文字列}}
    pattern = re.compile(r'''
        \{\{lang    # '{{lang'（マークアップの開始）
        (?:         # キャプチャ対象外のグループ開始
            [^|]*?  # '|'以外の文字が0文字以上、最短一致
            \|      # '|'
        )*?         # グループ終了、このグループが0以上出現、最短一致
        ([^|]*?)    # キャプチャ対象、'|'以外が0文字以上、最短一致（表示対象の文字列）
        \}\}        # '}}'（マークアップの終了）
        ''', re.MULTILINE + re.VERBOSE)
    target = pattern.sub(r'\1', target)

    # 外部リンクの除去  [http://xxxx] 、[http://xxx xxx]
    pattern = re.compile(r'''
        \[http:\/\/ # '[http://'（マークアップの開始）
        (?:         # キャプチャ対象外のグループ開始
            [^\s]*? # 空白以外の文字が0文字以上、最短一致
            \s      # 空白
        )?          # グループ終了、このグループが0か1出現
        ([^]]*?)    # キャプチャ対象、']'以外が0文字以上、最短一致（表示対象の文字列）
        \]          # ']'（マークアップの終了）
        ''', re.MULTILINE + re.VERBOSE)
    target = pattern.sub(r'\1', target)


     # <br>、<ref>の除去
    pattern = re.compile(r'''
        <           # '<'（マークアップの開始）
        \/?         # '/'が0か1出現（終了タグの場合は/がある）
        [br|ref]    # 'br'か'ref'
        [^>]*?      # '>'以外が0文字以上、最短一致
        >           # '>'（マークアップの終了）
        ''', re.MULTILINE + re.VERBOSE)
    target = pattern.sub('', target)
    return target

# 基礎情報テンプレートの抽出条件のコンパイル
pattern = re.compile(r'''
    ^\{\{基礎情報.*?$   # '{{基礎情報'で始まる行
    (.*?)       # キャプチャ対象、任意の0文字以上、最短一致
    ^\}\}$      # '}}'の行
    ''', re.MULTILINE + re.VERBOSE + re.DOTALL)
    # MULTILINEは複数行を見るため、VERBOSEは正規表現中にコメントするため、DOTALLは「.」で改行も対象にする

# 基礎情報テンプレートの抽出
contents = pattern.findall(extract_UK())#findallはマッチした部分だけを持ってくる

# 抽出結果からのフィールド名と値の抽出条件のコンパイル
pattern = re.compile(r'''
    ^\|         # '|'で始まる行
    (.+?)       # キャプチャ対象（フィールド名）、任意の1文字以上、最短一致
    \s*         # 空白文字0文字以上
    =
    \s*         # 空白文字0文字以上
    (.+?)       # キャプチャ対象（値）、任意の1文字以上、最短一致
    (?:         # キャプチャ対象外のグループ開始
        (?=\n\|)    # 改行+'|'の手前（肯定の先読み）
        | (?=\n$)   # または、改行+終端の手前（肯定の先読み）
    )           # グループ終了
    ''', re.MULTILINE + re.VERBOSE + re.DOTALL)

# フィールド名と値の抽出
fields = pattern.findall(contents[0]) #findallはマッチした部分だけを持ってくる

# 辞書にセット
result = {}
for field in fields:
    result[field[0]] = remove_markup(field[1])

# 国旗画像の値を取得
fname_flag = result['国旗画像']

# リクエスト生成
url = 'https://www.mediawiki.org/w/api.php?' \
    + 'action=query' \
    + '&titles=File:' + urllib.parse.quote(fname_flag) \
    + '&format=json' \
    + '&prop=imageinfo' \
    + '&iiprop=url'
#titlesで取得対象のファイルを指定、prpでimageinfoを使うことを指定、特殊文字のエスケープのためurllib.parse.quoteを使用

# MediaWikiのサービスへリクエスト送信
request = urllib.request.Request(url,
    headers={'User-Agent': 'NLP100_Python(@s-saitoh)'})
connection = urllib.request.urlopen(request)

# jsonとして受信
data = json.loads(connection.read().decode())


# URL取り出し
url = data['query']['pages'].popitem()[1]['imageinfo'][0]['url']
print(url)
