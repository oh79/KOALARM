import time
import sys
from riot_api import get_account_info, get_start_game_info, get_finished_game_info, SUMMONER_NAME, get_summoner_tier, get_overall_game_stats
from send_kakao_message import send_kakao_message

# 테스트 모드 활성화: 명령줄 인자 "test"가 있으면 활성화
test_mode = False
if len(sys.argv) > 1 and sys.argv[1].lower() == "test":
    test_mode = True

if test_mode:
    print("테스트 모드 활성화: Dummy 함수 사용 및 체크 주기 2초 적용")
    sim_counter = 0

    def get_start_game_info(puuid):
        """
        테스트 모드용 더미 함수:
          - sim_counter 값에 따라 게임 진행 여부를 시뮬레이션.
          - 상태 1,2는 게임중, 0,3은 게임종료.
          - summonerId 및 기타 필요한 정보도 더미 데이터로 반환.
        """
        global sim_counter
        state = sim_counter % 4
        sim_counter += 1
        if state in (1, 2):
            return {
                "champion": "제이스",
                "gameTime": "6분 1초",
                "gameType": "개인 랭크",
                "teamLineup": {
                    "탑": "나는 너가 허접이란걸 알고있어 [세트, 9/9/7]",
                    "정글": "KLINGZ [바이, 3/5/11]",
                    "미드": "최후의쌈닭 [멜, 13/5/5]",
                    "원딜": "태지귀요밍 [카이사, 1/4/5]",
                    "서폿": "군대가기싫어요 [쓰레쉬, 1/6/12]"
                },
                "summonerId": "DUMMY_SUMMONER_ID"
            }
        else:
            return False

    def get_finished_game_info(puuid):
        """
        테스트 모드용 더미 함수:
          - 고정된 게임 종료 정보를 반환.
          - 게임 종류, 티어, 팀 라인업 등의 정보도 포함.
        """
        return {
            "win": True,
            "kills": 10,
            "deaths": 8,
            "assists": 2,
            "gameTime": "22분 39초",
            "gameType": "개인 랭크",
            "tier": "실버3 30포인트",
            "teamLineup": {
                "탑": "탑닉 [챔피언A, 5/3/2]",
                "정글": "정글닉 [챔피언B, 3/4/6]",
                "미드": "미드닉 [챔피언C, 8/2/1]",
                "원딜": "원딜닉 [챔피언D, 7/5/3]",
                "서폿": "서폿닉 [챔피언E, 1/7/10]"
            },
            "teamTotalKills": 14,
            "topKiller": "미드닉 (8킬)",
            "funMessage": "즐거운 게임 되세요!"
        }
else:
    # 프로덕션 모드에서는 riot_api.py에 정의된 함수를 그대로 사용
    get_start_game_info = get_start_game_info
    get_finished_game_info = get_finished_game_info

def monitor_game():
    """
    타겟 플레이어의 게임 상태(시작/종료)를 주기적으로 체크하여 카카오톡 메시지를 전송합니다.
    
    [게임 시작 시] 출력 예시:
      [고병국님의 게임이 시작되었습니다.]
      소환사 : 이름#태그
      티어 : (실제 티어 정보)
      게임 종류 : 개인 랭크 / 자유 랭크 / 특별 게임 모드
      게임 시간 : (게임 경과 시간)
      선택 챔피언 : (실제 챔피언 이름)
      
      [팀원 정보]
      탑    : (팀원 정보)
      정글 : (팀원 정보)
      미드  : (팀원 정보)
      원딜 : (팀원 정보)
      서폿 : (팀원 정보)
      
      [전체 게임 수]
      전체 게임 수 / 이긴 판 수 / 패배한 판 수 
      승률 : (승률)
      
      전적 보러 가기 : https://lol.ps/summoner/소환사명?region=kr
    
    [게임 종료 시] 출력 예시:
      [고병국님의 게임이 종료되었습니다.]
      소환사 : 이름#태그
      티어 : (실제 티어 정보)
      결과 : 승리/패배
      게임 시간 : (게임 시간)
      고병국님의 KDA : 10/8/2
      게임 종류 : 개인 랭크 / 자유 랭크 / 특별 게임 모드
      
      [팀원 정보]
      탑    : (팀원 정보) [챔피언명, kda]
      정글 : (팀원 정보) [챔피언명, kda]
      미드  : (팀원 정보) [챔피언명, kda]
      원딜 : (팀원 정보) [챔피언명, kda]
      서폿 : (팀원 정보) [챔피언명, kda]

      [전체 게임 수]
      전체 게임 수 / 이긴 판 수 / 패배한 판 수 
      승률 : (승률)
      
      팀 총 킬 : (팀 총 킬)
      최고 킬 플레이어 : (최고 킬 플레이어 정보) [챔피언명, kda]
      (funMessage)
      
      전적 보러 가기 : https://lol.ps/summoner/소환사명?region=kr
    """
    if "#" not in SUMMONER_NAME:
        print("SUMMONER_NAME 형식이 올바르지 않습니다. 예: 이름#태그")
        return

    game_name, tag_line = SUMMONER_NAME.split("#", 1)
    try:
        account_info = get_account_info(game_name, tag_line)
        puuid = account_info.get("puuid")
        if not puuid:
            print("계정 정보에서 puuid를 가져오지 못했습니다.")
            return
        print(f"모니터링 시작: puuid {puuid} 확인됨")
    except Exception as e:
        print("계정 정보를 가져오는 중 오류 발생:", e)
        return

    in_game = False  # 게임 상태 플래그
    print("타겟 게임 상태를 체크합니다.")
    while True:
        try:
            start_info = get_start_game_info(puuid)
            print("활성 게임 정보:", start_info)
            if start_info and not in_game:
                # 활성 게임이 감지되면, 반환된 summonerId로 티어 정보 조회
                summoner_id = start_info.get("summonerId")
                tier_info = get_summoner_tier(summoner_id) if summoner_id else "티어 정보 없음"
                game_type = start_info.get("gameType", "~")
                team_lineup = start_info.get("teamLineup", {
                    "탑": "~",
                    "정글": "~",
                    "미드": "~",
                    "원딜": "~",
                    "서폿": "~"
                })
                
                # 전체 게임 정보 조회 (전체 게임 수, 이긴 판 수, 패배한 판 수, 승률)
                total_games, wins, losses, win_rate = get_overall_game_stats(summoner_id)
                
                start_msg = (
                    f"[고병국님의 게임이 시작되었습니다.]\n"
                    f"소환사 : {SUMMONER_NAME}\n"
                    f"티어 : {tier_info}\n"
                    f"게임 종류 : {game_type}\n"
                    f"게임 시간 : {start_info.get('gameTime', '~')}\n"
                    f"선택 챔피언 : {start_info.get('champion', '~')}\n\n"
                    f"[팀원 정보]\n"
                    f"팀원 1    : {team_lineup.get('탑', '~')}\n"
                    f"팀원 2    : {team_lineup.get('정글', '~')}\n"
                    f"팀원 3    : {team_lineup.get('미드', '~')}\n"
                    f"팀원 4    : {team_lineup.get('원딜', '~')}\n"
                    f"팀원 5    : {team_lineup.get('서폿', '~')}\n\n"
                    f"[전체 게임 수]\n"
                    f"{total_games} / {wins} / {losses}\n"

                    f"승률 : {win_rate}%\n\n"
                    f"전적 보러 가기 : https://lol.ps/summoner/{SUMMONER_NAME}?region=kr"
                )
                print(start_msg)
                result = send_kakao_message(start_msg)
                print("메시지 전송 결과:", result)
                in_game = True

            elif not start_info and in_game:
                finished_info = get_finished_game_info(puuid)
                if finished_info:
                    outcome = "승리" if finished_info.get("win") else "패배"
                    kda = f"{finished_info.get('kills')}/{finished_info.get('deaths')}/{finished_info.get('assists')}"
                    record_url = f"https://lol.ps/summoner/{SUMMONER_NAME}?region=kr"

                    # 전체 게임 정보 조회 (전체 게임 수, 이긴 판 수, 패배한 판 수, 승률)
                    total_games, wins, losses, win_rate = get_overall_game_stats(summoner_id)

                    team_lineup = finished_info.get("teamLineup", {
                        "탑": "~",
                        "정글": "~",
                        "미드": "~",
                        "원딜": "~",
                        "서폿": "~"
                    })
                    
                    end_msg = (
                        f"[고병국님의 게임이 종료되었습니다.]\n"
                        f"소환사 : {SUMMONER_NAME}\n"
                        f"결과 : {outcome}\n"
                        f"티어 : {finished_info.get('tier', '~')}\n"
                        f"게임 종류 : {finished_info.get('gameType', '~')}\n\n"
                        f"게임 시간 : {finished_info.get('gameTime', '~')}\n"
                        f"고병국님의 KDA : {kda}\n\n"
                        f"[팀원 정보]\n"
                        f"탑    : {team_lineup.get('탑', '~')}\n"
                        f"정글 : {team_lineup.get('정글', '~')}\n"
                        f"미드  : {team_lineup.get('미드', '~')}\n"
                        f"원딜 : {team_lineup.get('원딜', '~')}\n"
                        f"서폿 : {team_lineup.get('서폿', '~')}\n\n"
                        f"팀 총 킬 : {finished_info.get('teamTotalKills', '~')}\n"
                        f"최고 킬 플레이어 : {finished_info.get('topKiller', '~')}\n\n"
                        f"[전체 게임 수]\n"
                        f"{total_games} / {wins} / {losses}\n"
                        f"승률 : {win_rate}%\n\n"
                        f"전적 보러 가기 : {record_url}"
                    )
                    print(end_msg)
                    result = send_kakao_message(end_msg)
                    print("메시지 전송 결과:", result)
                else:
                    end_msg = "고병국님의 게임이 종료되었습니다. (게임 결과를 확인할 수 없습니다.)"
                    print(end_msg)
                    result = send_kakao_message(end_msg)
                    print("메시지 전송 결과:", result)
                in_game = False
            else:
                print("상태 변화 없음.")
        except Exception as e:
            print("모니터링 중 오류 발생:", e)
        time.sleep(2 if test_mode else 15)

if __name__ == "__main__":
    monitor_game() 