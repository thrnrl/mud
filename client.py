import socket
import threading

# 직업 리스트
jobs = {
    1: "정찰",  # Scout
    2: "전투",  # Combat
    3: "의무",  # Medic
    4: "격투가"   # Support
}

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
                print("너의 턴입니다. 행동을 선택하세요!")
                if jobs[job_choice] == "정찰":
                    print("1: 30 데미지 / 2: 50 데미지 + 약점 간파")
                elif jobs[job_choice] == "전투":
                    print("1: 50 데미지 / 2: 100 강한 공격")
                elif jobs[job_choice] == "의무":
                    print("1: 팀원 체력 30 회복 (팀원 번호 선택) / 2: 전체 팀원 체력 10 회복")
                elif jobs[job_choice] == "격투가":
                    print("1: 50 데미지 / 2: 40 데미지 + 50% 확률로 연속 공격")
                user_input = input("행동을 선택하세요: ")
                client.send(user_input.encode())
            else:
                print(response)

    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.daemon = True
    receive_thread.start()

    # 직업 선택
    print("직업을 선택하세요:")
    for job_id, job_name in jobs.items():
        print(f"{job_id}. {job_name}")

    job_choice = int(input("직업 번호를 선택하세요 (1-4): "))
    if job_choice not in jobs:
        print("잘못된 직업 번호입니다. 기본 직업 '정찰'로 설정됩니다.")
        job_choice = 1

    print(f"선택한 직업: {jobs[job_choice]}")
    client.send(str(job_choice).encode()) 

    while True:
        pass

    client.close()

if __name__ == "__main__":
    # 클라이언트 ID를 받아서 클라이언트 시작
    client_id = int(input("이 클라이언트는 번호 몇 번인가요? (1, 2, 3, 4): "))
    start_client(client_id)
