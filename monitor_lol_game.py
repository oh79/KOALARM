import time
import sys
from riot_api import get_account_info, get_start_game_info, get_finished_game_info, SUMMONER_NAME
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
        테스트 모드용 더미 함수: sim_counter 값에 따라 게임 진행 여부를 시뮬레이션.
        상태 1,2는 게임중, 0,3은 게임종료.
        """
        global sim_counter
        state = sim_counter % 4
        sim_counter += 1
        if state in (1, 2):
            return {"champion": "아우렐리온 솔", "gameTime": "-3분 37초"}
        else:
            return None

    def get_finished_game_info(puuid):
        """
        테스트 모드용 더미 함수: 고정된 게임 종료 정보를 반환.
        """
        return {"win": True, "kills": 10, "deaths": 8, "assists": 2, "matchId": "TEST_MATCH_001"}
else:
    get_start_game_info = get_start_game_info
    get_finished_game_info = get_finished_game_info

def monitor_game():
    """
    타겟 플레이어의 게임 상태(시작/종료)를 주기적으로 체크하여 카카오톡 메시지를 전송합니다.
    
    [게임 시작 시]
      메시지 포맷:
      [고병국님이 게임중입니다!]
      챔피언 : (실제 챔피언 이름)
      게임 시간 : (게임 경과 시간)
      전적 보러 가기: https://lol.ps/summoner/하음응_KR2?region=kr
    
    [게임 종료 시]
      메시지 포맷:
      고병국님의 게임이 끝났습니다.
      결과: 승리/패배
      고병국님의 KDA: 10/8/2
      전적 보러 가기: https://lol.ps/summoner/하음응_KR2?region=kr
    """
    if "#" not in SUMMONER_NAME:
        print("SUMMONER_NAME 형식이 올바르지 않습니다. 예: 이름#태그")
        return
    game_name, tag_line = SUMMONER_NAME.split("#", 1)
    # print(game_name, tag_line)

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
            print(start_info)
            if start_info and not in_game:
                # 게임 시작 감지 시, 동적 정보를 사용해 메시지 구성
                champion = start_info.get("champion", "N/A")
                game_time = start_info.get("gameTime", "N/A")
                start_msg = (
                    f"[고병국님이 게임중입니다!]\n"
                    f"챔피언 : {champion}\n"
                    f"게임 시간 : {game_time}\n"
                    "전적 보러 가기 : https://lol.ps/summoner/{SUMMONER_NAME}?region=kr"
                )
                print("게임 시작 감지:", start_msg)
                result = send_kakao_message(start_msg)
                print(result)
                in_game = True
            elif not start_info and in_game:
                finished_info = get_finished_game_info(puuid)
                if finished_info:
                    outcome = "승리" if finished_info.get("win") else "패배"
                    kda = f"{finished_info.get('kills')}/{finished_info.get('deaths')}/{finished_info.get('assists')}"
                    record_url = "https://lol.ps/summoner/{SUMMONER_NAME}?region=kr"
                    end_msg = (
                        f"[고병국님의 게임이 끝났습니다.]\n"
                        f"결과 : {outcome}\n"
                        f"고병국님의 KDA : {kda}\n"
                        f"전적 보러 가기 : {record_url}"
                    )
                    print(end_msg)
                else:
                    end_msg = "고병국님의 게임이 끝났습니다. (게임 결과를 확인할 수 없습니다.)"
                print("게임 종료 감지:", end_msg)
                result = send_kakao_message(end_msg)
                print(result)
                in_game = False
            else:
                print("상태 변화 없음.")
        except Exception as e:
            print("모니터링 중 오류 발생:", e)
        time.sleep(2 if test_mode else 60)

if __name__ == "__main__":
    monitor_game() 