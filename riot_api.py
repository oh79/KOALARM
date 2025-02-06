import os
import json
import requests
from urllib.parse import quote
from config import RIOT_API_KEY, RIOT_REGION, RIOT_SUMMONER_REGION, SUMMONER_NAME

def get_account_info(game_name, tag_line):
    """
    소환사 정보 조회.
    GET https://{RIOT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}
    """
    url = f"https://{RIOT_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()

def get_champion_name(champion_id):
    try:
        # 해당 버전의 챔피언 데이터 파일 URL 생성
        champion_url = "https://ddragon.leagueoflegends.com/cdn/15.3.1/data/ko_KR/champion.json"
        resp = requests.get(champion_url, timeout=5)  # 요청 보내기
        resp.raise_for_status()  # HTTP 오류 발생시 예외 발생
        data = resp.json()
        
        # 딕셔너리 컴프리헨션을 사용해 챔피언 번호(key)와 이름(name) 매핑 생성
        champion_mapping = {champ["key"]: champ["name"] for champ in data.get("data", {}).values()}
        
        # 챔피언 번호가 문자열인지 여부 확인 후 반환 (숫자인 경우 문자열로 변환)
        return champion_mapping.get(str(champion_id))
    except Exception as e:
        print("챔피언 이름을 가져오는 중 오류 발생:", e)
    return None

def get_start_game_info(summoner_id):
    """
    활성 게임 정보를 조회하여, 게임이 진행 중이면 플레이어의 챔피언과 게임 시간을 반환합니다.
    게임이 진행 중이지 않으면 False 반환.
    반환 예시: {"champion": "아우렐리온 솔", "gameTime": "3분 37초"}
    """
    encrypted_summoner_id = quote(summoner_id)
    url = f"https://{RIOT_SUMMONER_REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{encrypted_summoner_id}"
    headers = {"X-Riot-Token": RIOT_API_KEY}
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        # 활성 게임 정보가 없으므로 종료된 경기 정보를 반환
        return False
    response.raise_for_status()
    game_data = response.json()
    # print(game_data)
    if not game_data:
        return game_data
    # config에 있는 소환사 이름에서 '#' 앞부분만 취한 뒤 양쪽 공백 제거, 소문자로 변환
    target_name = SUMMONER_NAME.split("#")[0].strip().lower()
    champion_id = 1
    for participant in game_data.get("participants", []):
        # summonerName 대신 summonerId로 비교
        print(participant.get("summoner_id", "").strip())
        print(encrypted_summoner_id)
        if participant.get("puuid", "").strip() == encrypted_summoner_id:
            champion_id = participant.get("championId")
            break

    champion = get_champion_name(champion_id) if champion_id is not None else "N/A"
    game_length_seconds = game_data.get("gameLength", 0) + 150
    minutes = game_length_seconds // 60
    seconds = game_length_seconds % 60
    game_time_str = f"{minutes}분 {seconds}초"
    return {"champion": champion, "gameTime": game_time_str}

def get_finished_game_info(puuid):
    """
    puuid를 사용해 최근 완료된 경기 결과 정보를 조회합니다.
    1. 최근 경기 ID 조회: GET /lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=1
    2. 해당 경기 상세 정보에서 승리 여부, KDA 정보를 추출합니다.
    
    반환 예시:
        {"win": True, "kills": 10, "deaths": 8, "assists": 2, "matchId": "KR_xxxx"}
    """
    RIOT_MATCH_REGION = os.environ.get("RIOT_MATCH_REGION", "asia")
    puuid_encoded = quote(puuid)
    match_ids_url = (
        f"https://{RIOT_MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid_encoded}/ids"
        f"?start=0&count=1&api_key={RIOT_API_KEY}"
    )
    response_ids = requests.get(match_ids_url, timeout=10)
    response_ids.raise_for_status()
    match_ids = response_ids.json()
    if not match_ids:
        return None
    match_id = match_ids[0]
    match_url = f"https://{RIOT_MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    response_match = requests.get(match_url, timeout=10)
    response_match.raise_for_status()
    match_data = response_match.json()
    participants = match_data.get("info", {}).get("participants", [])
    target = None
    for p in participants:
        if p.get("puuid") == puuid:
            target = p
            break
    if not target:
        return None
    return {
        "win": target.get("win", False),
        "kills": target.get("kills", 0),
        "deaths": target.get("deaths", 0),
        "assists": target.get("assists", 0),
        "matchId": match_id
    }