import MeCab
import jaconv
import json
from typing import Dict, List
try:
  from typing import Literal
except:
  from typing_extensions import Literal
m = MeCab.Tagger()

def tokenize(text: str, dict_type: Literal["unidic_lite", "neologd"] = "unidic_lite"
             )->List[Dict[str, str]]:
  if dict_type == "unidic_lite":
    lines = m.parse(text).splitlines()[:-1]
    token_dicts = []
    for line in lines:
      parts = line.split('\t')
      surface = parts[0]
      pronunciation = parts[1]
      stem_pronunciation = parts[2]
      stem = parts[3]
      pos = parts[4].split("-")
      
      token_dict = {}
      token_dict["surface"] = surface
      token_dict["pronunciation"] = pronunciation
      token_dict["stem_pronunciation"] = stem_pronunciation
      token_dict["yomi"] = pronunciation
      token_dict["stem"] = stem
      for i in range(5):
        if i < len(pos):
          token_dict[f"pos{i}"] = pos[i]
        else:
          token_dict[f"pos{i}"] = ""
      token_dicts.append(token_dict)

  return token_dicts 

def get_yomi(text):
    tokens = tokenize(text)
    yomi = ""
    for token in tokens:
      yomi += token["yomi"]
    return yomi

#単語抽出用の関数（表記ゆれ吸収リストを作るときの関数と同じ）
def extract_words(text: str) -> List[str]:
  tokens = tokenize(text)
  
  words=[]
  for token in tokens:
    surface = token["surface"]
    pos0 = token["pos0"]
    if pos0 in ['記号','助詞','助動詞'] : continue
    if surface == "ー": continue
    stem = token["stem"]

    if stem != '*': stem_yomi = jaconv.hira2kata(get_yomi(stem))
    else: stem_yomi = jaconv.hira2kata(surface) 
    words.append(stem_yomi)
  words.append(jaconv.hira2kata(get_yomi(text)))
  return words


#入力：botanswerのkeyのリスト
#出力：ユーザの想定入力とbotanswerのタイトルの結びつけリスト
def make_simwords_list(titles):  
  simwords = {}
  for t in titles:
    #生文字列から単語を抽出
    words = set(extract_words(t)) 
    #カタカナ読みから単語を抽出
    katayomi = get_yomi(t)
    words |= set(extract_words(katayomi))
    #ひらがな読みから単語を抽出
    hirayomi = jaconv.kata2hira(katayomi)
    words |= set(extract_words(hirayomi))
  
    for w in words:
      if w not in simwords: simwords[w]=[]
      simwords[w].append(t)
  return simwords
  
class Faq:
  def __init__(self, config):
    BOTANSWER_PATH = config["botanswer"]
    SEARCH_WORD = config["search_word"]
    with open(BOTANSWER_PATH) as f:
      self.botanswer = json.load(f)
    
    if "simwords" in config and os.path.exists(config["simwords"]):
      with open(config["simwords"], encoding="utf-8") as f:
        self.simwords = json.load(f)
    else:
      titles = [v for v in self.botanswer]
      self.simwords = make_simwords_list(titles)
    #print(self.simwords)
    self.search_word = SEARCH_WORD
      
#入力文字列から単語を抽出し、対応しそうな回答候補のタイトルのリストを返す
  def __get_candidates(self, question):
    #botanswerのkeyに一致するものがあれば、question１つのリストを候補として返す
    if question in self.botanswer: return [question]
    #botanswerのkeyに一致するものがない場合、candidateをsimwordsから取得して返す。
    candidates = {}
    words = extract_words(question)
    for word in words:
      #wordがsimwordsになければ処理をスキップ
      if word not in self.simwords: continue
      #適当なアルゴリズムで候補を取得する(現状は候補タイトルのうち登場回数が多いものを選ぶ)
      for w in self.simwords[word]:
        candidates[w]=candidates.get(w,0)+1
    #candidatesが一つもない場合、空のリストを返す
    if len(candidates) == 0: return []
    #candidatesが１つ以上存在する場合、最も多く登場した単語だけ抜き出す
    max_count = max([v for k,v in candidates.items()])
    candidate_words = [k for k,v in candidates.items() if v == max_count]
    return candidate_words
  
  
  #questionからanswerを生成する。候補が１個以下のときは文字列、２個以上のときはリストを返す。
  def get_answer(self, question):
    candidates = self.__get_candidates(question)
    #候補がゼロのとき
    if len(candidates) == 0: 
      return self.get_answer_with_zero_candidate(question)
    #候補が１のとき
    elif len(candidates) == 1:
      msg = self.botanswer[candidates[0]]
      return msg
    #候補が2以上のとき
    else:
      return candidates
  #回答候補が０個のときの回答文字列
  def get_answer_with_zero_candidate(self, question):
    msg = 'すみません、よくわかりませんでした'
    msg += '\nもしよかったらググってみてください'
    msg += '\nhttps://www.google.com/search?q='+self.search_word+'+'+question
    return msg

  
if __name__ == "__main__":
  import argparse, json, os
  parser = argparse.ArgumentParser()
  parser.add_argument("--config_path", type=str, default="config_sample.json")
  parser.add_argument("--config_key", type=str, default="sample")
  parser.add_argument("--search_word", type=str, default="チョコレート")
  parser.add_argument("--save_simwords", action="store_true")

  args = parser.parse_args()

  with open(args.config_path, encoding="utf-8") as f:
    config = json.load(f)
  faq = Faq(config[args.config_key])
  print("config_path and key:", args.config_path, args.config_key)
  print("search_word:", args.search_word)
  print("answer:", end=" ")
  print(faq.get_answer(args.search_word))

  if args.save_simwords:
    botanswer_path = config[args.config_key]["botanswer"]
    botanswer_filename = os.path.basename(botanswer_path)
    output_path = os.path.join(os.path.dirname(botanswer_path), f"simwords_{botanswer_filename}")
    
    with open(botanswer_path) as f:
      botanswer = json.load(f)
    botanswer_titles = list(botanswer.keys())
    simwords = make_simwords_list(botanswer_titles)
    with open(output_path, "w", encoding="utf-8") as f:
      json.dump(simwords, f,indent=2, ensure_ascii=False)

