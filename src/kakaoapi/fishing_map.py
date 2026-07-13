import pandas as pd
import geopandas as gpd
from shapely.ops import nearest_points

# 1. 데이터 불러오기 및 초기 공간 데이터 생성
fishing_df = pd.read_csv("C:/mongo_data/data/낚시터정보_부산광역시.csv", encoding="cp949")
danger_df = pd.read_excel("C:/mongo_data/data/연안사고위험구역_좌표변환.xlsx")
danger_df = danger_df.dropna(subset=["경도", "위도"])

fishing_gdf = gpd.GeoDataFrame(fishing_df, geometry=gpd.points_from_xy(fishing_df["WGS84경도"], fishing_df["WGS84위도"]), crs="EPSG:4326")
danger_gdf = gpd.GeoDataFrame(danger_df, geometry=gpd.points_from_xy(danger_df["경도"], danger_df["위도"]), crs="EPSG:4326")

# -------------------------------------------------------------
# 2. 🔥 [중요] 거리 계산을 위해 미터(m) 단위 좌표계(EPSG:5179)로 변환
# -------------------------------------------------------------
fishing_gdf_m = fishing_gdf.to_crs(epsg=5179)
danger_gdf_m = danger_gdf.to_crs(epsg=5179)

# 위험구역의 모든 포인트들을 하나로 결합 (가장 가까운 점을 찾기 위함)
danger_union = danger_gdf_m.unary_union


# -------------------------------------------------------------
# 3. 분석 ①: 각 낚시터에서 가장 가까운 위험구역까지의 거리 구하기
# -------------------------------------------------------------
def get_nearest_distance(fishing_point, danger_geom):
    # 가장 가까운 위험구역의 지점을 찾음
    nearest_danger_point = nearest_points(fishing_point, danger_geom)[1]
    # 두 점 사이의 거리를 계산 (미터 단위)
    return fishing_point.distance(nearest_danger_point)

# 낚시터 데이터에 '가장_가까운_위험구역_거리_m' 컬럼 추가
fishing_gdf["가장_가까운_위험구역_거리_m"] = fishing_gdf_m['geometry'].apply(
    lambda x: get_nearest_distance(x, danger_union)
)


# -------------------------------------------------------------
# 4. 분석 ②: 위험구역 반경 500m 이내에 있는 낚시터 필터링
# -------------------------------------------------------------
# 위험구역 주변에 500m 버퍼(원)를 생성합니다.
danger_buffers = danger_gdf_m.buffer(500).unary_union

# 버퍼 영역 안에 포함되는 낚시터만 골라냅니다.
is_inside_danger = fishing_gdf_m['geometry'].within(danger_buffers)
danger_close_fishing = fishing_gdf[is_inside_danger]


# -------------------------------------------------------------
# 5. 보고서용 통계 자료 계산 및 출력
# -------------------------------------------------------------
total_count = len(fishing_gdf)                       # 전체 낚시터 수
danger_close_count = len(danger_close_fishing)       # 500m 이내 취약 낚시터 수
safe_count = total_count - danger_close_count        # 안전 영역 낚시터 수

# 🧮 퍼센트(%) 비율 계산 ($ \text{비율} = \frac{\text{취약 개수}}{\text{전체 개수}} \times 100 $)
danger_ratio = (danger_close_count / total_count) * 100

print("\n" + "="*50)
print("📌 부산시 낚시터 안전 취약 지역 위치 비율 분석 보고서 데이터")
print("="*50)
print(f"✅ 분석 대상 전체 낚시터 수 : {total_count}개")
print(f"✅ 연안사고 위험구역 반경 500m 이내 낚시터 수 : {danger_close_count}개")
print(f"📢 [결론] 부산시 전체 낚시터 중 총 {danger_ratio:.1f}%가 '안전 취약 지역'에 위치하고 있습니다.")
print("="*50)

# 추가 인사이트: 구군별(지역별)로 어디가 가장 취약한지 통계 내기
# (낚시터 데이터에 '시군구명' 또는 '주소' 컬럼이 있다면 지역별 집계가 가능합니다)
# 아래 '시군구명' 컬럼 이름은 데이터 원본에 맞게 확인해 주세요.
district_col = [col for col in fishing_gdf.columns if '구' in col or '군' in col or '주소' in col]

if district_col:
    print("\n📊 [참고 자료] 위험구역 500m 이내 낚시터의 지역별 분포 (상위 5개 지역):")
    # 주소에서 '구' 단위만 잘라내어 집계 (예: 부산광역시 해운대구 -> 해운대구)
    danger_close_fishing['구군'] = danger_close_fishing[district_col[0]].apply(lambda x: str(x).split()[1] if len(str(x).split()) > 1 else str(x))
    print(danger_close_fishing['구군'].value_counts().head(5))
    print("="*50)