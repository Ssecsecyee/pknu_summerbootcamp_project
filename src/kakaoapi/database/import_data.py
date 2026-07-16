import pandas as pd
from connection import get_db

db = get_db()

def import_csv_to_mongodb(file_path, collection_name):
    # CSV 읽기
    df = pd.read_csv(file_path, encoding='cp949') # 한글 깨짐 방지
    # 데이터프레임을 딕셔너리 리스트로 변환
    data = df.to_dict(orient='records')
    # MongoDB에 삽입
    db[collection_name].insert_many(data)
    print(f"{collection_name}에 데이터 삽입 완료!")

# 데이터 import 실행
import_csv_to_mongodb(r'..\data\낚시터정보_부산광역시.csv', 'fishing_spots_busan')