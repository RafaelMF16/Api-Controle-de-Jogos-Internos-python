# Jogos Internos API Python

Backend do sistema **Jogos Internos**, responsável pela autenticação, regras de negócio, persistência em Firestore, paginação das listagens, gestão de esportes, usuários, confrontos e geração de previsão com IA.

## Visão Geral

A API foi construída com FastAPI e segue uma organização inspirada em Clean Architecture.

Ela cobre:

- autenticação por usuário e senha
- cadastro público de visitante
- sessão com cookie HTTP only
- gestão de usuários
- gestão de esportes coletivos e individuais
- regras específicas por perfil
- gestão de confrontos
- dashboard resumido
- geração de previsão de confronto
- fallback heurístico para previsão
- integração opcional com Vertex AI

## Tecnologias

- FastAPI
- Uvicorn
- Pydantic
- PyJWT
- Google Cloud Firestore
- Google GenAI / Vertex AI
- Python 3.12

Dependências principais em [requirements.txt](C:\Users\Rafae\Documents\Projetos\controle-de-jogos-internos-com-ia\jogos-internos-api-python\requirements.txt):

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `google-cloud-firestore`
- `google-genai`
- `PyJWT`

## Estrutura do Projeto

Pastas principais em [app](C:\Users\Rafae\Documents\Projetos\controle-de-jogos-internos-com-ia\jogos-internos-api-python\app):

- `api`
  - rotas HTTP
  - dependências
- `application`
  - DTOs
  - serviços
  - casos de uso
- `domain`
  - entidades
  - contratos de repositório
- `infrastructure`
  - implementações concretas
  - integração com Firestore
- `core`
  - configuração

## Módulos Funcionais

### Autenticação

Rotas em [auth.py](C:\Users\Rafae\Documents\Projetos\controle-de-jogos-internos-com-ia\jogos-internos-api-python\app\api\routes\auth.py):

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register-visitor`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `PUT /api/v1/auth/me/tema`

O backend trabalha com:

- `admin`
- `juiz`
- `capitao`
- `visitante`

### Usuários

Responsável por:

- cadastro de usuários administrativos
- atualização de perfis
- ativação/inativação
- controle de tema
- curso e período para perfis aplicáveis

Rotas principais:

- `GET /api/v1/usuarios`
- `POST /api/v1/usuarios`
- `PUT /api/v1/usuarios/{id}`
- `DELETE /api/v1/usuarios/{id}`

### Esportes

Responsável por:

- cadastro de equipes coletivas
- cadastro de inscrição individual
- vínculo da inscrição individual ao usuário autenticado
- membros e habilidades por equipe
- detalhe do cadastro

Rotas principais:

- `GET /api/v1/equipes`
- `GET /api/v1/equipes/{id}`
- `POST /api/v1/equipes`
- `PUT /api/v1/equipes/{id}`
- `DELETE /api/v1/equipes/{id}`

### Confrontos

Responsável por:

- criação de confronto
- edição
- resultado
- vencedor ou placar conforme modalidade
- detalhe do confronto
- geração de previsão

Rotas principais:

- `GET /api/v1/confrontos`
- `GET /api/v1/confrontos/{id}`
- `POST /api/v1/confrontos`
- `PUT /api/v1/confrontos/{id}`
- `DELETE /api/v1/confrontos/{id}`
- `POST /api/v1/confrontos/{id}/previsao`

### Dashboard

Responsável por:

- total de inscrições
- total de confrontos
- próximos confrontos

Rota principal:

- `GET /api/v1/dashboard/resumo`

### Health Check

- `GET /api/v1/health`

## Regras de Negócio Importantes

### Esportes coletivos

- possuem equipe
- possuem capitão
- possuem curso e período
- possuem membros

### Esportes individuais

- representam inscrição individual
- não possuem lista de membros
- usam dados do usuário autenticado
- bloqueiam duplicidade por usuário e modalidade

### Capitão

- pode gerenciar a própria equipe coletiva
- pode se inscrever em modalidade individual

### Visitante

- pode consultar anonimamente
- pode criar conta
- pode fazer inscrição individual autenticada

## Previsão de Confronto

O sistema salva a previsão diretamente no confronto.

Fluxo:

1. confronto é criado
2. backend monta o contexto do confronto
3. provedor de previsão é chamado
4. resultado é salvo no documento do confronto

A previsão inclui:

- percentual do participante A
- percentual do participante B
- favorito
- resumo
- modelo utilizado
- status da previsão

### Modos de previsão

O backend suporta:

- `vertex`
- `heuristic`

Se o Vertex falhar, o sistema pode usar fallback heurístico.

## Firestore

O Firestore é o banco principal do sistema.

Coleções principais:

- `usuarios`
- `equipes`
- `confrontos`

O backend já retorna respostas paginadas para:

- usuários
- esportes
- confrontos

## Como Executar

Na pasta [jogos-internos-api-python](C:\Users\Rafae\Documents\Projetos\controle-de-jogos-internos-com-ia\jogos-internos-api-python):

```powershell
pip install -r requirements.txt
```

Depois configure o projeto GCP:

```powershell
gcloud auth application-default login
gcloud config set project SEU_PROJECT_ID
gcloud auth application-default set-quota-project SEU_PROJECT_ID
```

Para subir a API:

```powershell
$env:GOOGLE_CLOUD_PROJECT="SEU_PROJECT_ID"
& "C:\Users\Rafae\AppData\Local\Programs\Python\Python312\python.exe" -m uvicorn app.main:app --reload
```

Swagger:

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Admin Inicial

Se a coleção de usuários estiver vazia, a API pode criar um admin bootstrap.

Variáveis usadas:

- `BOOTSTRAP_ADMIN_NAME`
- `BOOTSTRAP_ADMIN_USERNAME`
- `BOOTSTRAP_ADMIN_PASSWORD`

## Como Usar Vertex AI

Para ativar previsão com Vertex no ambiente local:

```powershell
$env:GOOGLE_CLOUD_PROJECT="SEU_PROJECT_ID"
$env:PREDICTION_PROVIDER="vertex"
$env:PREDICTION_MODEL="gemini-2.5-flash"
$env:VERTEX_AI_LOCATION="us-central1"
```

Depois suba a API normalmente.

Se a previsão for feita via Vertex, o confronto salvo tende a registrar o modelo como:

- `gemini-2.5-flash`

Se cair no fallback local:

- `heuristic-v1`

## Observações

- o backend usa cookie de autenticação
- o Firestore é a fonte principal de persistência
- as respostas de listagem seguem contrato paginado
- a dashboard ainda entrega o resumo completo dos próximos confrontos para o frontend paginar localmente
- o projeto está pronto para integração com GCP e Vertex AI
