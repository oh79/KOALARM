import time, win32con, win32api, win32gui
from config import KAKAO_OPENTALK_NAME

# # 채팅방에 메시지 전송'
def kakao_sendtext(chatroom_name, text):
    """
    지정된 채팅방에 텍스트를 전송합니다.
    """
    # # 핸들 _ 채팅방
    hwndMain = win32gui.FindWindow(None, chatroom_name)
    if not hwndMain:
        raise Exception("채팅방 창을 찾을 수 없습니다!")
    hwndEdit = win32gui.FindWindowEx(hwndMain, None, "RICHEDIT50W", None)
    if not hwndEdit:
        raise Exception("채팅 입력창을 찾을 수 없습니다!")
    # hwndListControl = win32gui.FindWindowEx( hwndMain, None, "EVA_VH_ListControl_Dblclk", None)

    win32api.SendMessage(hwndEdit, win32con.WM_SETTEXT, 0, text)
    SendReturn(hwndEdit)


# # 엔터
def SendReturn(hwnd):
    """
    엔터키를 전송하여 메시지 전송 완료.
    """
    win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.01)
    win32api.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)


# # 채팅방 열기
def open_chatroom(chatroom_name):
    """
    채팅방 열기: 채팅방 검색 후 선택합니다.
    """
    hwndkakao = win32gui.FindWindow(None, "카카오톡")
    if not hwndkakao:
        raise Exception("카카오톡 창을 찾을 수 없습니다!")
    hwndkakao_edit1 = win32gui.FindWindowEx(hwndkakao, None, "EVA_ChildWindow", None)
    hwndkakao_edit2_1 = win32gui.FindWindowEx(hwndkakao_edit1, None, "EVA_Window", None)
    hwndkakao_edit2_2 = win32gui.FindWindowEx(hwndkakao_edit1, hwndkakao_edit2_1, "EVA_Window", None)
    hwndkakao_edit3 = win32gui.FindWindowEx(hwndkakao_edit2_2, None, "Edit", None)

    # # Edit에 검색 _ 입력되어있는 텍스트가 있어도 덮어쓰기됨
    win32api.SendMessage(hwndkakao_edit3, win32con.WM_SETTEXT, 0, chatroom_name)
    time.sleep(1)   # 안정성 위해 필요
    SendReturn(hwndkakao_edit3)
    time.sleep(1)


# 실제 카톡 메시지 전송 함수 (문자열 메시지를 받아 전송)
def send_kakao_message(text):
    """
    주어진 메시지를 카카오톡 오픈톡방에 전송합니다.
    """
    try:
        open_chatroom(KAKAO_OPENTALK_NAME)  # 채팅방 열기
        kakao_sendtext(KAKAO_OPENTALK_NAME, text)  # 메시지 전송
        time.sleep(0.5)
        kakao_sendtext(KAKAO_OPENTALK_NAME, text)  # 메시지 전송
        return "카카오 메시지 전송 성공"
    except Exception as e:
        return f"카카오 메시지 전송 실패: {e}"


def main():
    open_chatroom(KAKAO_OPENTALK_NAME)  # 채팅방 열기
    text = "test"
    result = send_kakao_message(text)   # 메시지 전송
    print(result)


if __name__ == '__main__':
    main()