import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# 1. 📂 [경로 수정] 카카오 API로 만든 위험구역 좌표변환 파일 로드
danger_df = pd.read_excel("C:/mongo_data/data/연안사고위험구역_좌표변환.xlsx")

# 혹시 모를 결측치 제거 및 GeoDataFrame 변환
danger_df = danger_df.dropna(subset=["경도", "위도"])
danger_gdf = gpd.GeoDataFrame(
    danger_df, 
    geometry=gpd.points_from_xy(danger_df["경도"], danger_df["위도"]), 
    crs="EPSG:4326"
)

# 📏 거리 계산용 미터 단위 좌표계(EPSG:5179)로 변환
danger_gdf_m = danger_gdf.to_crs(epsg=5179)


# 2. 🚨 사용자 위치 기준 위험 구역 체크 함수
def check_fishing_safety(user_lon, user_lat, max_distance_m=500):
    """
    user_lon: 사용자 현재 경도 (예: 129.004907)
    user_lat: 사용자 현재 위도 (예: 35.083344)
    max_distance_m: 위험 판단 반경 (기본값 500미터)
    """
    # ① 사용자의 위경도 좌표를 공간 데이터(Point)로 생성
    user_point = gpd.GeoSeries([Point(user_lon, user_lat)], crs="EPSG:4326")
    
    # ② 거리를 재기 위해 미터 단위 좌표계로 투영 변환
    user_point_m = user_point.to_crs(epsg=5179).iloc[0]
    
    # ③ 사용자 위치와 전국의 모든 위험구역 간의 거리 계산 (단위: 미터)
    distances = danger_gdf_m['geometry'].distance(user_point_m)
    
    # ④ 설정한 위험 반경(500m) 이내에 있는 위험구역만 필터링
    danger_nearby = danger_gdf_m[distances <= max_distance_m]
    
    print("\n" + "="*50)
    print(f"📍 사용자 GPS 수신 위치: 경도 {user_lon}, 위도 {user_lat}")
    print("="*50)
    
    # ⑤ 위험 영역 존재 여부에 따른 결과 판단
    if len(danger_nearby) > 0:
        print("❌ [경고] 현재 위치는 연안사고 위험구역 근처이므로 낚시를 금지합니다!")
        print(f"⚠️ 반경 {max_distance_m}m 이내에 지정된 위험구역이 {len(danger_nearby)}곳 존재합니다.")
        
        # 가장 가까운 위험구역 찾기
        closest_idx = distances.idxmin()
        closest_distance = distances.min()
        
        # 데이터셋의 열 이름에 맞게 장소명 추출 (보통 '장소명' 또는 첫 번째 열)
        place_name = danger_df.loc[closest_idx, '장소명'] if '장소명' in danger_df.columns else danger_df.loc[closest_idx].iloc[0]
        
        print(f"📌 가장 인접한 위험지역: '{place_name}' (약 {closest_distance:.1f}m 거리)")
        return False  # 위험함 (챗봇에게 경고 멘트 유도)
    else:
        print("✅ [안전] 반경 500m 이내에 등록된 연안사고 위험구역이 없습니다.")
        print("정상적인 낚시 활동이 가능합니다. 항상 구명조끼를 착용해 주세요!")
        return True   # 안전함


# 3. 🎯 가상의 GPS 좌표로 실시간 체킹 테스트
# 테스트 1: 아까 데이터에 있던 감천항 위험구역 좌표 근처일 때
print("🏃‍♂️ 사용자가 감천항 방파제 근처로 진입했다고 가정:")
check_fishing_safety(129.004907, 35.083344)

# 테스트 2: 위험구역과 완전히 떨어진 안전한 지역일 때
print("\n🏃‍♂️ 사용자가 안전한 백사장 근처에 있다고 가정:")
check_fishing_safety(129.123456, 35.123456)