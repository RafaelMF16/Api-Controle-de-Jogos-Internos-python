# Jogos Internos API Python

API em Python para servir o projeto de controle dos jogos internos, organizada em camadas inspiradas em clean architecture.

## Stack

- FastAPI
- Uvicorn
- Pydantic
- Persistencia inicial em arquivo JSON

## Estrutura

- `app/api`: rotas HTTP e dependencias
- `app/application`: casos de uso, DTOs e servicos
- `app/domain`: entidades e contratos
- `app/infrastructure`: persistencia e implementacoes concretas
- `app/core`: configuracoes da aplicacao
- `data`: arquivo JSON usado como banco temporario

## Endpoints principais

- `GET /api/v1/health`
- `GET /api/v1/dashboard/resumo`
- `GET /api/v1/equipes`
- `GET /api/v1/equipes/{equipe_id}`
- `POST /api/v1/equipes`
- `PUT /api/v1/equipes/{equipe_id}`
- `DELETE /api/v1/equipes/{equipe_id}`
- `GET /api/v1/confrontos`
- `GET /api/v1/confrontos/proximos`
- `GET /api/v1/confrontos/{confronto_id}`
- `POST /api/v1/confrontos`
- `PUT /api/v1/confrontos/{confronto_id}`
- `DELETE /api/v1/confrontos/{confronto_id}`

## Como executar

1. Instale Python 3.11+.
2. Crie e ative um ambiente virtual.
3. Instale as dependencias:

```bash
pip install -r requirements.txt
```

4. Execute a API:

```bash
uvicorn app.main:app --reload
```

5. Acesse a documentacao interativa:

```text
http://127.0.0.1:8000/docs
```

## Observacoes

- O arquivo `data/database.json` funciona como banco temporario.
- A API ja esta preparada para um front Angular consumir com CORS habilitado.
- O contrato dos endpoints foi ajustado para refletir os objetos usados no front-end Angular.
- A persistencia em JSON e simples de entender agora e pode ser trocada depois por banco relacional sem alterar as rotas.
