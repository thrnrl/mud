import socket
import threading

# 서버에 연결
def start_client(client_id):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 9999))

    # 클라이언트 ID를 서버로 전송
    client.send(str(client_id).encode())

    def receive_messages():
        while True:
            response = client.recv(1024).decode()

            if response == "0":
                print("다른 클라이언트의 차례입니다. 대기해주세요.")
            elif response == "1":
                print("너의 턴입니다. 공격을 입력하세요!")
                user_input = input("1을 입력하면 50 데미지, 2를 입력하면 80 데미지: ")
                client.send(user_input.encode())  # 입력값을 서버로 전송
            else:
                print(response)  # 서버에서 다른 메시지 처리

    # 서버로부터 메시지를 받는 스레드 시작
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    while True:
        # 클라이언트가 계속 대기하면서 서버로부터 메시지를 기다림
        pass

    client.close()

if __name__ == "__main__":
    # 클라이언트 ID를 받아서 클라이언트 시작
    client_id = int(input("이 클라이언트는 번호 몇 번인가요? (1, 2, 3, 4): "))
    start_client(client_id)
