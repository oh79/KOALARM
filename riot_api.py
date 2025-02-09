import os
import json
import requests
from urllib.parse import quote
from config import RIOT_API_KEY, RIOT_REGION, RIOT_SUMMONER_REGION, SUMMONER_NAME

# 챔피언 정보를 캐시하기 위한 전역 변수
CHAMPION_MAPPING = None

def get_champion_mapping():
    """
    Data Dragon의 한국어 챔피언 데이터를 가져와서
    챔피언의 key와 한국어 이름을 매핑한 딕셔너리를 반환합니다.
    캐시되어 있다면 재요청하지 않습니다.
    """
    global CHAMPION_MAPPING
    if CHAMPION_MAPPING is None:
        try:
            champion_url = "https://ddragon.leagueoflegends.com/cdn/15.3.1/data/ko_KR/champion.json"
            resp = requests.get(champion_url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            # 챔피언의 key(문자열)와 한국어 이름 매핑 생성
            CHAMPION_MAPPING = {champ["key"]: champ["name"] for champ in data.get("data", {}).values()}
        except Exception as e:
            print("챔피언 데이터 로드 중 오류 발생:", e)
            CHAMPION_MAPPING = {}
    return CHAMPION_MAPPING

def get_champion_name(champion_id):
    """
    챔피언 id를 받아서 한국어 챔피언 이름을 반환합니다.
    만약 데이터를 찾지 못하면 "~"를 반환합니다.
    """
    mapping = get_champion_mapping()
    return mapping.get(str(champion_id), "~")

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

def format_team_lineup(team_participants):
    """
    팀 참가자 정보를 받아서, 각 포지션별(탑, 정글, 미드, 원딜, 서폿)
    팀원 정보를 구성합니다.
    각 팀원의 이름은 우선순위: riotId > summonerName > summonerId 순이며,
    챔피언 이름은 한국어로 출력됩니다.
    """
    lanes = ["탑", "정글", "미드", "원딜", "서폿"]
    team_lineup = {}
    if len(team_participants) == 5:
        for lane, p in zip(lanes, team_participants):
            display_name = p.get("riotId") or p.get("summonerName") or p.get("summonerId", "알수없음")
            k = p.get("kills", 0)
            d = p.get("deaths", 0)
            a = p.get("assists", 0)
            kda = f"{k}/{d}/{a}"
            # champion_id를 이용해 get_champion_name() 함수에서 한국어 이름 반환
            champ_name = get_champion_name(p.get("championId"))
            team_lineup[lane] = f"{display_name} [{champ_name}, {kda}]"
    else:
        team_lineup = {lane: "~" for lane in lanes}
    return team_lineup

def get_start_game_info(puuid):
    """
    활성 게임 정보를 조회하여 게임이 진행 중이면 다음 정보를 반환합니다:
      - 선택 챔피언 (대상 소환사가 선택한 챔피언)
      - 게임 경과 시간 (게임 시작 후 경과 시간, '분 초' 형식)
      - 게임 종류 (gameQueueConfigId 기준: 개인 랭크, 자유 랭크, 특별 게임 모드)
      - 팀 라인업 (같은 팀 5명의 참가자에 대해 포지션별(탑, 정글, 미드, 원딜, 서폿) 정보 출력)
      - summonerId (대상 소환사의 암호화된 summonerId)

    게임이 진행 중이지 않으면 False를 반환합니다.
    """
    encrypted_puuid = quote(puuid)
    url = f"https://{RIOT_SUMMONER_REGION}.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/{encrypted_puuid}"
    headers = {"X-Riot-Token": RIOT_API_KEY}

    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        return False  # 활성 게임 정보가 없으면 False 반환
    response.raise_for_status()
    game_data = response.json()
    # print(game_data)
    # 대상 소환사(타겟) 찾기
    target = None
    for p in game_data.get("participants", []):
        if p.get("puuid") == puuid:
            target = p
            break
    if not target:
        print("타겟 참가자를 찾을 수 없습니다.")
        return False

    # 선택한 챔피언 이름 조회 (championId 기준)
    champion_id = target.get("championId")
    champion = get_champion_name(champion_id) if champion_id else "~"

    # 게임 경과 시간 계산 (보정된 150초 추가 후 '분 초' 형식)
    game_length_seconds = game_data.get("gameLength", 0) + 150
    minutes = game_length_seconds // 60
    seconds = game_length_seconds % 60
    game_time_str = f"{minutes}분 {seconds}초"

    # 게임 종류 결정 (gameQueueConfigId 기준)
    queue_id = game_data.get("gameQueueConfigId")
    if queue_id == 420:
        game_type = "개인 랭크"
    elif queue_id == 440:
        game_type = "자유 랭크"
    elif queue_id:
        game_type = "특별 게임 모드"
    else:
        game_type = "~"

    # 동일 팀 참가자 추출
    my_team_id = target.get("teamId")
    team_participants = [p for p in game_data.get("participants", []) if p.get("teamId") == my_team_id]

    # 만약 팀 참가자 모두에 teamPosition 정보가 없다면(예: API 응답에 해당 필드 미존재, 5명 모두),
    # 원래 순서대로 할당하여 format_team_lineup 함수가 정상 동작하도록 함.
    if all(not p.get("teamPosition") for p in team_participants) and len(team_participants) == 5:
        ordered_team_participants = team_participants
    else:
        # teamPosition(및 role) 값을 이용해 라인별로 참가자를 분류 (탑, 정글, 미드, 원딜, 서폿)
        lane_mapping = {"탑": None, "정글": None, "미드": None, "원딜": None, "서폿": None}
        for p in team_participants:
            pos = (p.get("teamPosition") or "").upper()
            role = (p.get("role") or "").upper()
            lane = None
            if pos == "TOP":
                lane = "탑"
            elif pos == "JUNGLE":
                lane = "정글"
            elif pos in ("MIDDLE", "MID"):
                lane = "미드"
            elif pos in ("BOTTOM",):
                if role == "CARRY":
                    lane = "원딜"
                elif role == "SUPPORT":
                    lane = "서폿"
                else:
                    lane = "원딜"
            elif pos == "UTILITY":
                lane = "서폿"
            if lane and lane_mapping[lane] is None:
                lane_mapping[lane] = p

        ordered_team_participants = []
        for lane in ["탑", "정글", "미드", "원딜", "서폿"]:
            if lane_mapping[lane] is None:
                # 해당 라인에 해당하는 플레이어 정보가 없으면 기본 더미 데이터를 사용
                dummy = {
                    "riotId": "~",
                    "summonerName": "~",
                    "summonerId": "알수없음",
                    "championId": None,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0
                }
                ordered_team_participants.append(dummy)
            else:
                ordered_team_participants.append(lane_mapping[lane])

    # 팀 라인업 포맷팅: monitor_lol_game.py에서 사용하는 형식(탑, 정글, 미드, 원딜, 서폿)으로 변환
    team_lineup = format_team_lineup(ordered_team_participants)

    return {
        "champion": champion,
        "gameTime": game_time_str,
        "gameType": game_type,
        "teamLineup": team_lineup,
        "summonerId": target.get("summonerId")
    }

def get_summoner_tier(summoner_id):
    """
    소환사의 티어 정보를 조회합니다.
    API Endpoint:
      GET /lol/league/v4/entries/by-summoner/{encryptedSummonerId}
    반환 예시:
      "실버4 37포인트"
    """
    encrypted_summoner_id = quote(summoner_id)
    url = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    # 일반적으로 솔로랭크 큐 "RANKED_SOLO_5x5" 정보를 사용합니다.
    for entry in data:
        if entry.get("queueType") == "RANKED_SOLO_5x5":
            tier = entry.get("tier", "티어없음")
            rank = entry.get("rank", "")
            lp = entry.get("leaguePoints", 0)
            # 티어 영어명을 한글로 매핑
            tier_mapping = {
                "IRON": "아이언",
                "BRONZE": "브론즈",
                "SILVER": "실버",
                "GOLD": "골드",
                "PLATINUM": "플래티넘",
                "DIAMOND": "다이아몬드",
                "MASTER": "마스터",
                "GRANDMASTER": "그랜드마스터",
                "CHALLENGER": "챌린저"
            }
            tier_kor = tier_mapping.get(tier.upper(), tier)
            return f"{tier_kor}{rank} {lp}포인트"
    return "티어 정보 없음"

def get_finished_game_info(puuid):
    """
    puuid를 사용해 최근 완료된 경기 결과 정보를 조회합니다.
    1. 최근 경기 ID 조회: GET /lol/match-v5/matches/by-puuid/{puuid}/ids?start=0&count=1
    2. 경기 상세 정보를 통해 승리 여부, KDA, 게임 시간, 게임 종류,
       포지션별 팀원 정보, 팀 총 킬, 최고 킬 플레이어, 그리고 티어 정보를 추출합니다.
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
    # print(match_id)
    match_url = f"https://{RIOT_MATCH_REGION}.api.riotgames.com/lol/match/v5/matches/{match_id}?api_key={RIOT_API_KEY}"
    response_match = requests.get(match_url, timeout=10)
    response_match.raise_for_status()
    match_data = response_match.json()
    # print(match_data)
    participants = match_data.get("info", {}).get("participants", [])
    target = None
    for p in participants:
        if p.get("puuid") == puuid:
            target = p
            break
    if not target:
        return None

    # 게임 시간 변환 (초 → 분:초)
    game_duration_sec = match_data.get("info", {}).get("gameDuration", 0)
    minutes = game_duration_sec // 60
    seconds = game_duration_sec % 60
    game_time = f"{minutes}분 {seconds:02d}초"

    # 게임 종류 설정 (queueId에 따라)
    queue_id = match_data.get("info", {}).get("queueId")
    if queue_id == 420:
        game_type = "개인 랭크"
    elif queue_id == 440:
        game_type = "자유 랭크"
    else:
        game_type = "특별 게임 모드"

    # 같은 팀 참가자 추출
    team_id = target.get("teamId")
    team_participants = [p for p in participants if p.get("teamId") == team_id]

    # 포지션별 팀원 정보 초기화
    team_lineup = {
        "탑": "~",
        "정글": "~",
        "미드": "~",
        "원딜": "~",
        "서폿": "~"
    }

    for p in team_participants:
        pos = (p.get("teamPosition") or "").upper()
        role = (p.get("role") or "").upper()
        lane = None
        if pos == "TOP":
            lane = "탑"
        elif pos == "JUNGLE":
            lane = "정글"
        elif pos in ("MIDDLE", "MID"):
            lane = "미드"
        elif pos in ("BOTTOM",):
            if role == "CARRY":
                lane = "원딜"
            elif role == "SUPPORT":
                lane = "서폿"
            else:
                lane = "원딜"
        elif pos == "UTILITY":
            lane = "서폿"
        else:
            if role == "SUPPORT":
                lane = "서폿"
            elif role == "CARRY":
                lane = "원딜"
        if lane:
            nickname = p.get("riotIdGameName") or p.get("summonerName") or "~"
            champion_id = p.get("championId")
            # 챔피언 ID가 있으면 한국어 이름 반환, 없으면 "~" 사용
            champ = get_champion_name(champion_id) if champion_id else "~"
            k = p.get("kills", 0)
            d = p.get("deaths", 0)
            a = p.get("assists", 0)
            lineup_str = f"{nickname} [{champ}, {k}/{d}/{a}]"
            team_lineup[lane] = lineup_str

    # 팀 전체 킬 및 최고 킬 플레이어 계산
    team_total_kills = sum(p.get("kills", 0) for p in team_participants)
    top_killer = None
    max_kills = -1
    for p in team_participants:
        kills = p.get("kills", 0)
        if kills > max_kills:
            max_kills = kills
            top_killer = p.get("riotIdGameName") or p.get("summonerName")
    top_killer_info = f"{top_killer} ({max_kills}킬)" if top_killer else ""

    # 플레이어 티어 정보 (솔로 랭크 기준)
    summoner_id = target.get("summonerId")
    tier_info = get_summoner_tier(summoner_id) if summoner_id else "티어 정보 없음"

    return {
        "win": target.get("win", False),
        "kills": target.get("kills", 0),
        "deaths": target.get("deaths", 0),
        "assists": target.get("assists", 0),
        "matchId": match_id,
        "gameTime": game_time,
        "gameType": game_type,
        "tier": tier_info,
        "teamLineup": team_lineup,
        "teamTotalKills": team_total_kills,
        "topKiller": top_killer_info,
        "summonerId": summoner_id
    }

def get_overall_game_stats(summoner_id):
    """
    주어진 summoner_id로 솔로 랭크 (RANKED_SOLO_5x5) 전체 게임 정보를 조회하여
    전체 게임 수, 이긴 판 수, 패배한 판 수, 승률을 반환합니다.
    
    반환 예시:
       total_games, win_count, loss_count, win_rate
    """
    encrypted_summoner_id = quote(str(summoner_id))
    url = f"https://{RIOT_SUMMONER_REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}?api_key={RIOT_API_KEY}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    # 솔로 랭크 결과(RANKED_SOLO_5x5) 찾기
    solo = next((entry for entry in data if entry.get("queueType") == "RANKED_SOLO_5x5"), None)
    if solo:
        wins = solo.get("wins", 0)
        losses = solo.get("losses", 0)
        total = wins + losses
        win_rate = round(wins * 100 / total, 2) if total > 0 else 0
        return total, wins, losses, win_rate
    else:
        return 0, 0, 0, 0