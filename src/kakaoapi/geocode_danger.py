import pandas as pd
import requests
import time

# 엑셀 읽기
df = pd.read_excel(
    "c:/Users/user/Desktop/project 낚시 금지 구역/연안사고위험구역/연안사고위험구역_최종.xlsx",
    sheet_name="연안사고위험구역_2023",
    header=1
)

# 카카오 REST API 키
KAKAO_API_KEY = "d40c2af9123125bb64cd913a8906a574"

url = "https://dapi.kakao.com/v2/local/search/address.json"

headers = {
    "Authorization": f"KakaoAK {KAKAO_API_KEY}"
}


def address_to_coord(address):

    params = {
        "query": address
    }

    response = requests.get(
        url,
        headers=headers,
        params=params
    )

    data = response.json()

    if data.get("documents"):
        x = data["documents"][0]["x"]
        y = data["documents"][0]["y"]

        return x, y

    return None, None


# 위도 / 경도 저장
df["경도"] = None
df["위도"] = None


for index, row in df.iterrows():

    address = row["주소"]

    x, y = address_to_coord(address)

    df.loc[index, "경도"] = x
    df.loc[index, "위도"] = y

    print(index, address, x, y)

    time.sleep(0.1)


# 엑셀 저장
df.to_excel(
    "연안사고위험구역_좌표변환.xlsx",
    index=False
)