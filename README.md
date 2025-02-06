# League of Legends 게임 모니터링 프로그램

이 프로그램은 리그 오브 레전드 게임 상태를 모니터링하고 게임 시작/종료 시 카카오톡 오픈톡방에 알림 메시지를 전송해주는 도구야.

## 주요 기능
- **소환사 정보 조회:** Riot API를 통해 소환사와 계정 정보를 가져옴.
- **게임 상태 확인:** 게임 시작 시 챔피언 및 진행 시간, 게임 종료 시 승패 및 KDA 정보를 확인.
- **카카오톡 알림 전송:** Win32 API를 사용하여 카카오톡 오픈톡방에 메시지를 자동 전송.

## 설치 및 실행 방법

### 1. Python 및 필수 패키지 설치
Python 3.x가 설치되어 있어야 해. 터미널에서 아래 명령어로 필수 패키지 설치:
```bash:terminal
pip install requests pywin32
```

### 2. 환경 변수 설정
프로그램 동작에 필요한 환경 변수를 설정해야 해. 아래 항목들을 환경 변수로 등록하거나, 직접 `config.py` 파일 내 기본값을 수정해도 돼:

- `RIOT_API_KEY`: Riot API 키 (예: `YOUR_RIOT_API_KEY`)
- `RIOT_REGION`: Riot API 사용 지역 (예: `asia`)
- `RIOT_SUMMONER_REGION`: 소환사 정보 조회 지역 (예: `kr`)
- `SUMMONER_NAME`: 대상 소환사 이름 (형식: "닉네임#태그", 예: `t1smash#KR3`)
- `KAKAO_OPENTALK_NAME`: 카카오톡 오픈톡방 이름 (예: 채팅방 이름)

**예시 (Windows CMD):**
```bash:terminal
set RIOT_API_KEY=YOUR_RIOT_API_KEY
set RIOT_REGION=asia
set RIOT_SUMMONER_REGION=kr
set SUMMONER_NAME=t1smash#KR3
set KAKAO_OPENTALK_NAME=채팅방이름
```

### 3. 프로그램 실행
프로젝트 루트 디렉터리에서 아래 명령어를 실행해 모니터링을 시작할 수 있어.

- **기본 모드 (실제 Riot API 연동):**
  ```bash:terminal
  python start.py
  ```

- **테스트 모드 (더미 데이터 사용, 체크 주기 2초):**
  ```bash:terminal
  python start.py test
  ```

## 프로젝트 구조
- **`riot_api.py`**  
  Riot API와 통신해 소환사 정보, 챔피언 이름, 게임 정보 등을 처리함.

- **`monitor_lol_game.py`**  
  게임 시작/종료를 주기적으로 체크하며, 카카오톡 메시지 전송 로직을 구현.

- **`start.py`**  
  모니터링 프로세스를 시작하는 스크립트. `monitor_game()` 함수를 호출.

- **`config.py`**  
  환경 변수 및 설정값을 관리함.

- **`send_kakao_message.py`**  
  Win32 API를 이용해 특정 카카오톡 오픈톡방에 메시지를 자동 전송.

## 주의 사항
- `send_kakao_message.py`의 기능은 Windows 전용이고, 실제 카카오톡 클라이언트 실행 및 오픈톡방 창 활성화가 필요해.
- Riot API의 호출 횟수 제한을 고려하면서 사용해야 해.
- 초기 설정 시 환경 변수를 올바르게 등록하지 않으면 실행 오류가 발생할 수 있음.

## 문의
실행 중 문제가 발생하면 이슈 트래커에 문의하거나, 설정 파일을 꼼꼼히 확인해보길 바라!

Happy monitoring!
