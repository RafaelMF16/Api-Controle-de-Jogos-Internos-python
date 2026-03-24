# Jogos Internos API Python

API em Python para servir o projeto de controle dos jogos internos, organizada em camadas inspiradas em clean architecture.

## Stack

- FastAPI
- Uvicorn
- Pydantic
- Google Cloud Firestore

## Estrutura

- `app/api`: rotas HTTP e dependencias
- `app/application`: casos de uso, DTOs e servicos
- `app/domain`: entidades e contratos
- `app/infrastructure`: persistencia e implementacoes concretas
- `app/core`: configuracoes da aplicacao
- `app/infrastructure/persistence/firestore`: cliente e acesso ao Firestore

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

4. Configure as credenciais do Google Cloud:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json
export GOOGLE_CLOUD_PROJECT=seu-projeto
```

5. Execute a API:

```bash
uvicorn app.main:app --reload
```

6. Acesse a documentacao interativa:

```text
http://127.0.0.1:8000/docs
```

## Observacoes

- A API ja esta preparada para um front Angular consumir com CORS habilitado.
- O contrato dos endpoints foi ajustado para refletir os objetos usados no front-end Angular.
- As colecoes padrao no Firestore sao `equipes` e `confrontos`, mas podem ser alteradas por variavel de ambiente.
- Em Cloud Run, o ideal e usar credenciais padrao do ambiente e informar o projeto pelo `GOOGLE_CLOUD_PROJECT`.
