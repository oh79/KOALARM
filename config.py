import os

# Riot API 관련 설정 (환경변수로 관리)
RIOT_API_KEY = os.environ.get("RIOT_API_KEY", "YOUR_RIOT_API_KEY")
if not RIOT_API_KEY:
    raise EnvironmentError("RIOT_API_KEY 환경변수가 설정되어 있지 않습니다.")

RIOT_REGION = os.environ.get("RIOT_REGION", "asia")
RIOT_SUMMONER_REGION = os.environ.get("RIOT_SUMMONER_REGION", "kr")

# 소환사 이름 (예: "이름#태그")
SUMMONER_NAME = os.environ.get("SUMMONER_NAME","t1smash#KR3")
if not SUMMONER_NAME:
    raise EnvironmentError("SUMMONER_NAME 환경변수가 설정되어 있지 않습니다.")

# 카카오톡 관련 설정: 오픈톡방 이름
KAKAO_OPENTALK_NAME = os.environ.get("KAKAO_OPENTALK_NAME","단체방이름")
if not KAKAO_OPENTALK_NAME:
    raise EnvironmentError("KAKAO_OPENTALK_NAME 환경변수가 설정되어 있지 않습니다.") 