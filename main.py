import socket
import threading
import random

# 초기 보스 체력
boss_health = 1000

# 클라이언트들의 체력 초기화
clients_health = {
    1: 100,
    2: 100,
    3: 100,
    4: 100
}

# 접속된 클라이언트 리스트 (클라이언트 ID -> 소켓)
connected_clients = {}

# 공격 데미지
attack_damage = {
    "1": 50,  # 1 입력 시 보스에게 50 데미지
    "2": 80   # 2 입력 시 보스에게 80 데미지
}

# 턴 관리 및 클라이언트의 공격 데미지 기록
clients_attack = {}
turn_condition = threading.Condition()
current_turn = 1  # 첫 번째 클라이언트부터 시작
turn_logs = {}  # 클라이언트별 공격 로그 저장

# 클라이언트의 접속을 처리하는 함수
def handle_client(client_socket):
    global boss_health, current_turn, clients_attack, turn_logs

    try:
        client_id = int(client_socket.recv(1024).decode())  # 클라이언트가 보낸 ID
        connected_clients[client_id] = client_socket
        clients_attack[client_id] = 0  # 공격 초기화
        turn_logs[client_id] = []  # 로그 초기화

        while True:
            with turn_condition:
                # 현재 턴인지 확인
                while current_turn != client_id:
                    # 현재 턴이 아니면 0을 보내고 대기
                    client_socket.send("0".encode())  # 턴이 아니면 0 전송
                    turn_condition.wait()  # 현재 턴이 아니면 대기

                # 현재 턴이면 1을 보내고 공격 입력 대기
                client_socket.send("1".encode())  # 턴이면 1 전송

                # 클라이언트의 공격을 받음
                data = client_socket.recv(1024).decode()

                # 잘못된 입력 처리
                if data not in attack_damage:
                    client_socket.send("잘못된 입력입니다. 1 또는 2를 입력하세요.\n".encode())
                    continue

                # 데미지 합산
                damage = attack_damage[data]
                clients_attack[client_id] += damage  # 클라이언트의 공격 데미지 합산

                # 로그 기록
                turn_logs[client_id].append(f"Client{client_id} 공격: {damage} 데미지")

                # 턴 넘기기
                current_turn = (current_turn % len(connected_clients)) + 1
                turn_condition.notify_all()  # 다른 클라이언트에게 턴을 넘김

                # 턴이 모두 끝난 후 보스 체력 업데이트
                if all(damage > 0 for damage in clients_attack.values()):
                    # 보스 체력 업데이트
                    total_damage = sum(clients_attack.values())
                    boss_health -= total_damage
                    attacked_client = random.choice(list(connected_clients.keys()))
                    clients_health[attacked_client] -= 30

                    # 로그 메시지
                    log_message = f"보스의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                    log_message += f"보스가 Client{attacked_client}를 공격했습니다!\n"
                    for client_id in connected_clients:
                        log_message += f"Client{client_id} 체력: {clients_health[client_id]}\n"

                    # 모든 클라이언트에게 메시지 전송
                    send_to_all_clients(log_message)

                    # 턴 초기화
                    clients_attack = {client_id: 0 for client_id in connected_clients}
                    current_turn = 1  # 첫 번째 클라이언트부터 다시 시작

            # 게임 종료 확인
            if boss_health <= 0:
                send_to_all_clients("축하합니다! 보스를 처치했습니다!\n")
                break

    finally:
        # 클라이언트 접속 종료시 리스트에서 제거
        del connected_clients[client_id]
        client_socket.close()

# 모든 클라이언트에게 메시지를 전송하는 함수
def send_to_all_clients(message):
    for client_socket in connected_clients.values():
        try:
            client_socket.send(message.encode())
        except:
            pass  # 예외 처리, 클라이언트 연결이 끊어졌을 때

# 클라이언트를 처리하는 서버 함수
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 9999))
    server.listen(5)
    print("서버가 시작되었습니다. 클라이언트 접속 대기 중...")

    while True:
        client_socket, addr = server.accept()
        print(f"클라이언트 {addr}가 접속했습니다.")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
