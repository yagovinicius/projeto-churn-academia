import requests
from faker import Faker
import random
from datetime import datetime, timedelta, timezone

API_URL = "http://127.0.0.1:8000/aluno"
fake = Faker("pt_BR")

# Planos a criar (nome, duração em meses, preço)
planos = [
    {"nome": "Mensal", "duracao_meses": 1, "preco": 100.0},
    {"nome": "Trimestral", "duracao_meses": 3, "preco": 270.0},
    {"nome": "Semestral", "duracao_meses": 6, "preco": 480.0},
    {"nome": "Anual", "duracao_meses": 12, "preco": 900.0},
]


def get_admin_token():
    resp = requests.post("http://127.0.0.1:8000/token", data={
        "username": "admin",
        "password": "admin"
    })
    return resp.json()["access_token"]


def criar_planos(headers):
    planos_id = {}
    for plano in planos:
        resp = requests.post(f"{API_URL}/planos", json=plano, headers=headers)
        if resp.status_code in (200, 201):
            plano_id = resp.json()['id']
            planos_id[plano['nome']] = plano_id
            print(f"Plano '{plano['nome']}' criado com id {plano_id}")
        elif resp.status_code == 400 and "Plano já cadastrado" in resp.text:
            print(f"Plano '{plano['nome']}' já existe.")
        else:
            print(f"Erro ao criar plano '{plano['nome']}': {resp.text}")
    return planos_id


def criar_aluno(plano_id, headers):
    # Decide sexo com peso 50/50 para balancear análise
    sexo = random.choice(["Masculino", "Feminino"])

    # Gera nome de acordo com sexo
    if sexo == "Masculino":
        nome = fake.first_name_male() + " " + fake.last_name()
    else:
        nome = fake.first_name_female() + " " + fake.last_name()

    email = fake.unique.email()
    senha = "senha123"
    data_nascimento = fake.date_of_birth(
        minimum_age=18, maximum_age=65).isoformat()

    aluno = {
        "nome": nome,
        "email": email,
        "senha": senha,
        "data_nascimento": data_nascimento,
        "sexo": sexo,
        "plano_id": plano_id,
    }
    resp = requests.post(f"{API_URL}/registro", json=aluno, headers=headers)
    if resp.status_code in (200, 201):
        print(f"Aluno {nome} criado com id {resp.json()['id']}")
        return resp.json()['id']
    else:
        print(f"Erro ao criar aluno {nome}: {resp.text}")
        return None


def criar_checkins(aluno_id, plano_nome, headers):
    hoje = datetime.now(timezone.utc).date()

    freq_por_plano = {
        "Mensal": 2,
        "Trimestral": 3,
        "Semestral": 3,
        "Anual": 4,
    }

    base_freq = freq_por_plano.get(plano_nome, 2)

    # Gera dias sem checkin entre 0 e 60
    dias_sem_checkin = random.randint(0, 60)
    ultimo_checkin = hoje - timedelta(days=dias_sem_checkin)

    # Aplica probabilidade proporcional aos dias sem checkin
    # Quanto mais dias, maior a chance de churn, mas não é determinístico
    prob_churn = min(dias_sem_checkin / 60, 0.95)
    is_churn = random.random() < prob_churn

    checkin_dates = []

    if is_churn:
        # Gera checkins antigos antes do último checkin
        for _ in range(base_freq * 3):
            dia_checkin = ultimo_checkin - \
                timedelta(days=random.randint(1, 30))
            checkin_dates.append(dia_checkin)
    else:
        # Gera checkins recentes, na última semana
        for semana in range(4):
            for _ in range(base_freq):
                dia_checkin = hoje - \
                    timedelta(days=semana * 7 + random.randint(0, 6))
                checkin_dates.append(dia_checkin)

    checkin_dates = sorted(set(checkin_dates))

    for data in checkin_dates:
        hora_dt = datetime.combine(data, datetime.strptime(
            "07:00:00", "%H:%M:%S").time()).replace(tzinfo=timezone.utc)
        payload = {
            "aluno_id": aluno_id,
            "data": data.isoformat(),
            "hora": hora_dt.isoformat(),
        }
        resp = requests.post(f"{API_URL}/checkin",
                             json=payload, headers=headers)
        if resp.status_code in (200, 201):
            print(
                f"Checkin criado para aluno {aluno_id} em {data.isoformat()} {hora_dt.isoformat()}")
        else:
            print(
                f"Erro ao criar checkin para aluno {aluno_id}: {resp.status_code} - {resp.text}")


if __name__ == "__main__":
    token = get_admin_token()
    headers = {"Authorization": f"Bearer {token}"}
    planos_id = criar_planos(headers)
    total_alunos = 1000

    proporcoes = {
        "Mensal": 0.4,
        "Trimestral": 0.25,
        "Semestral": 0.2,
        "Anual": 0.15,
    }

    for plano_nome, proporcao in proporcoes.items():
        quantidade = int(total_alunos * proporcao)
        plano_id = planos_id.get(plano_nome)
        if not plano_id:
            print(f"Plano {plano_nome} não encontrado, pulando...")
            continue
        for _ in range(quantidade):
            aluno_id = criar_aluno(plano_id, headers)
            if aluno_id:
                criar_checkins(aluno_id, plano_nome, headers)
