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

# 직업별 특성 (데미지와 회복량)
job_effects = {
    1: {"name": "정찰", "attack1": 30, "attack2": 50, "special": "약점 간파"},
    2: {"name": "전투", "attack1": 50, "attack2": 100, "special": "강한 공격"},
    3: {"name": "의무", "heal1": 30, "heal2": 10, "special": "회복"},
    4: {"name": "격투가", "attack1": 50, "attack2": 40, "special": "연속 공격"}
}

clients_attack = {}
clients_jobs = {}  # 각 클라이언트의 직업 저장
turn_condition = threading.Condition()
current_turn = 1  # 첫 번째 클라이언트부터 시작
turn_logs = {}  # 각 클라이언트별 공격 로그 저장

def handle_client(client_socket):
    global boss_health, current_turn, clients_attack, clients_health, turn_logs

    try:
        client_id = int(client_socket.recv(1024).decode())  # 클라이언트가 보낸 ID
        connected_clients[client_id] = client_socket
        clients_attack[client_id] = 0  # 공격 초기화
        turn_logs[client_id] = []  # 공격 로그 초기화

        # 직업 정보 받기
        job_choice = int(client_socket.recv(1024).decode())  # 클라이언트의 직업
        clients_jobs[client_id] = job_choice

        while True:
            with turn_condition:
                # 현재 턴인지 확인
                while current_turn != client_id:
                    client_socket.send("0".encode())  # 턴이 아니면 0 전송
                    turn_condition.wait()  # 현재 턴이 아니면 대기

                # 현재 턴이면 1을 보내고 행동 선택 대기
                client_socket.send("1".encode())  # 턴이면 1 전송

                # 클라이언트의 선택을 받음
                data = client_socket.recv(1024).decode()

                # 직업별 처리
                job = clients_jobs[client_id]
                if job == 1:  # 정찰
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"정찰 공격: {damage} 데미지")
                    elif data == "2":
                        damage = job_effects[job]["attack2"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"정찰 공격: {damage} 데미지 (약점 간파)")
                    else:
                        client_socket.send("잘못된 입력입니다. 1 또는 2를 입력하세요.\n".encode())

                elif job == 2:  # 전투
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"전투 공격: {damage} 데미지")
                    elif data == "2":
                        damage = job_effects[job]["attack2"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"전투 공격: {damage} 데미지 (강한 공격)")
                    else:
                        client_socket.send("잘못된 입력입니다. 1 또는 2를 입력하세요.\n".encode())

                elif job == 3:  # 의무
                    if data == "1":
                        # 팀원 체력 30 회복 (팀원 선택)
                        client_socket.send("회복할 팀원 번호를 입력하세요: ")
                        teammate_id = int(client_socket.recv(1024).decode())
                        clients_health[teammate_id] += 30
                        turn_logs[client_id].append(f"의무 회복: 팀원 {teammate_id} 체력 30 회복")
                    elif data == "2":
                        # 전체 팀원 체력 10 회복
                        for teammate_id in clients_health:
                            clients_health[teammate_id] += 10
                        turn_logs[client_id].append("의무 회복: 전체 팀원 체력 10 회복")
                    else:
                        client_socket.send("잘못된 입력입니다. 1 또는 2를 입력하세요.\n".encode())
                
                elif job == 4:  # 격투가
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"격투가 기본 공격: {damage} 데미지")
                    elif data == "2":
                        total_damage = 0
                        while random.random() < 0.6:
                            total_damage += job_effects[job]["attack2"]
                        clients_attack[client_id] += total_damage
                        turn_logs[client_id].append(f"격투가 연속 공격: {total_damage} 데미지")
                    else:
                        client_socket.send("잘못된 입력입니다. 1 또는 2를 입력하세요.\n".encode())

                # 턴 넘기기
                current_turn = (current_turn % len(connected_clients)) + 1
                turn_condition.notify_all()  # 다른 클라이언트에게 턴을 넘김

            # 턴이 종료되면 보스 체력 상태와 클라이언트 체력 상태, 공격 로그를 전송
            if all(damage > 0 for damage in clients_attack.values()):
                # 보스 체력 업데이트
                total_damage = sum(clients_attack.values())
                boss_health -= total_damage

                attacked_client = random.choice(list(connected_clients.keys()))
                clients_health[attacked_client] -= 30

                log_message = f"보스의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                log_message += f"보스가 Client{attacked_client}를 공격했습니다!\n"
                for client_id in connected_clients:
                    log_message += f"Client{client_id} 체력: {clients_health[client_id]}\n"

                send_to_all_clients(log_message)

                clients_attack = {client_id: 0 for client_id in connected_clients}
                current_turn = 1  
                
            if boss_health <= 0:
                send_to_all_clients("축하합니다! 보스를 처치했습니다!\n")
                break

    finally:
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
