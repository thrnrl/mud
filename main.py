import socket
import threading
import random

# 초기 보스 체력
boss_health = 1000
clients_attack = {}
connected_clients = {}

# 직업별 특성 (데미지, 회복량, 기본 체력)
job_effects = {
    1: {"name": "정찰", "attack1": 30, "attack2": 50, "base_health": 100},
    2: {"name": "전투", "attack1": 50, "attack2": 100, "base_health": 120},
    3: {"name": "석궁병", "attack1": 50, "attack2": 10, "base_health": 90},
    4: {"name": "격투가", "attack1": 50, "attack2": 40, "base_health": 110}
}

clients_jobs = {}  # 각 클라이언트의 직업 저장
turn_condition = threading.Condition()
current_turn = 1  # 첫 번째 클라이언트부터 시작
turn_logs = {}  # 각 클라이언트별 공격 로그 저장
boss_bleeding = False
bleeding_turns = 0
boss_turn_counter = 0
clients_last_used_skill = {}

def handle_client(client_socket):
    global boss_health, current_turn, clients_attack, turn_logs, boss_bleeding, bleeding_turns, boss_turn_counter

    try:
        client_id = int(client_socket.recv(1024).decode())  # 클라이언트가 보낸 ID
        connected_clients[client_id] = client_socket
        clients_attack[client_id] = 0  # 공격 초기화
        turn_logs[client_id] = []  # 공격 로그 초기화
        job_choice = int(client_socket.recv(1024).decode())  # 클라이언트의 직업
        clients_jobs[client_id] = job_choice
        clients_last_used_skill[client_id] = 0  # 2번 스킬 사용 여부 초기화

        # 클라이언트 직업에 맞는 기본 체력 (직업별 기본 체력)
        base_health = job_effects[job_choice]["base_health"]

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
                        # 2번 스킬 사용 전 쿨타임 체크
                        if clients_last_used_skill[client_id] == 2:
                            client_socket.send("쿨타임 중입니다. 1턴 후 사용 가능합니다.\n".encode())
                            continue
                        damage = job_effects[job]["attack2"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"정찰 공격: {damage} 데미지 (약점 간파)")
                
                elif job == 2:  # 전투
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"전투 공격: {damage} 데미지")
                    elif data == "2":
                        # 2번 스킬 사용 전 쿨타임 체크
                        if clients_last_used_skill[client_id] == 2:
                            client_socket.send("쿨타임 중입니다. 1턴 후 사용 가능합니다.\n".encode())
                            continue
                        damage = job_effects[job]["attack2"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"전투 공격: {damage} 데미지 (강한 공격)")

                elif job == 3:  # 석궁병
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"석궁병 기본 공격: {damage} 데미지")
                    elif data == "2":
                        # 2번 스킬 사용 전 쿨타임 체크
                        if clients_last_used_skill[client_id] == 2:
                            client_socket.send("쿨타임 중입니다. 1턴 후 사용 가능합니다.\n".encode())
                            continue
                        # 출혈 효과 (10 데미지)
                        damage = job_effects[job]["attack2"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"석궁병 출혈 효과: {damage} 데미지 (출혈)")
                        boss_bleeding = True
                        bleeding_turns = 3  # 출혈 상태 3턴으로 설정

                elif job == 4:  # 격투가
                    if data == "1":
                        damage = job_effects[job]["attack1"]
                        clients_attack[client_id] += damage
                        turn_logs[client_id].append(f"격투가 기본 공격: {damage} 데미지")
                    elif data == "2":
                        # 2번 스킬 사용 전 쿨타임 체크
                        if clients_last_used_skill[client_id] == 2:
                            client_socket.send("쿨타임 중입니다. 1턴 후 사용 가능합니다.\n".encode())
                            continue
                        total_damage = 0
                        while random.random() < 0.6:
                            total_damage += job_effects[job]["attack2"]
                        clients_attack[client_id] += total_damage
                        turn_logs[client_id].append(f"격투가 연속 공격: {total_damage} 데미지")

                # 사용한 스킬 기록
                clients_last_used_skill[client_id] = 2 if data == "2" else 1

                # 턴 넘기기
                current_turn = (current_turn % len(connected_clients)) + 1
                turn_condition.notify_all()  # 다른 클라이언트에게 턴을 넘김

            # 턴 종료 시 처리
            if all(damage > 0 for damage in clients_attack.values()):
                # 보스 체력 업데이트
                total_damage = sum(clients_attack.values())
                boss_health -= total_damage

                # 보스가 출혈 상태인 경우 출혈 데미지 적용
                if boss_bleeding:
                    boss_health -= 10
                    bleeding_turns -= 1
                    turn_logs[client_id].append(f"보스가 출혈 상태로 10 데미지를 받았습니다.")
                    if bleeding_turns <= 0:
                        boss_bleeding = False  # 출혈 상태 종료

                # 보스의 전체 공격 처리
                if boss_turn_counter == 2:
                    boss_turn_counter = 0  # 카운터 초기화
                    # 보스의 전체 공격: 모든 클라이언트에게 10 데미지
                    for client_id in connected_clients:
                        job = clients_jobs[client_id]
                        job_effects[job]["base_health"] -= 10  # 전체 공격으로 체력 감소
                        turn_logs[client_id].append(f"보스의 전체 공격: 10 데미지")
                    log_message = f"보스의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                    log_message += f"보스가 전체 공격을 실시하여 모든 클라이언트가 10 데미지를 입었습니다.\n"
                    if boss_bleeding:
                        log_message += f"보스가 출혈 상태로 10 데미지를 받았습니다. 출혈 상태가 {bleeding_turns}턴 남았습니다.\n"
                    for client_id in connected_clients:
                        log_message += f"Client{client_id}[{job_effects[clients_jobs[client_id]]['name']}] 남은 체력: {job_effects[clients_jobs[client_id]]['base_health']}\n"
                    send_to_all_clients(log_message)
                else:
                    # 보스가 랜덤으로 한 명에게만 공격
                    attacked_client = random.choice(list(connected_clients.keys()))
                    client_job = clients_jobs[attacked_client]
                    job_effects[client_job]["base_health"] -= 30

                    log_message = f"보스의 체력이 {total_damage}만큼 감소하여 현재 체력은 {boss_health}입니다.\n"
                    log_message += f"보스가 Client{attacked_client}를 공격했습니다! 30 데미지를 입혔습니다.\n"
                    if boss_bleeding:
                        log_message += f"보스가 출혈 상태로 10 데미지를 받았습니다. 출혈 상태가 {bleeding_turns}턴 남았습니다.\n"
                    for client_id in connected_clients:
                        log_message += f"Client{client_id}[{job_effects[clients_jobs[client_id]]['name']}] 남은 체력: {job_effects[clients_jobs[client_id]]['base_health']}\n"
                    send_to_all_clients(log_message)

                # 턴 종료 후 보스 공격과 관련된 처리가 끝난 후 턴을 1로 리셋
                clients_attack = {client_id: 0 for client_id in connected_clients}
                current_turn = 1  
                boss_turn_counter += 1  # 보스 턴 카운터 증가

            if boss_health <= 0:
                send_to_all_clients("축하합니다! 보스를 처치했습니다!\n")
                break

    finally:
        del connected_clients[client_id]
        client_socket.close()

def send_to_all_clients(message):
    for client_socket in connected_clients.values():
        try:
            client_socket.send(message.encode())
        except:
            pass  

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
