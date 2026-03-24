# Guia Do Codigo

Este documento resume como o back-end funciona depois da migracao da persistencia para o Google Cloud Firestore.

## Visao Geral

O projeto continua organizado em camadas:

- `app/main.py`: cria a aplicacao FastAPI e registra middlewares e rotas.
- `app/core`: guarda configuracoes globais.
- `app/api`: define endpoints HTTP e dependencias injetadas nas rotas.
- `app/application`: concentra services e DTOs.
- `app/domain`: descreve entidades e contratos de repositorio.
- `app/infrastructure`: implementa a persistencia concreta com Firestore.

Fluxo geral:

```text
rotas recebem -> services processam -> repositorios persistem -> Firestore armazena
```

## Configuracoes

Arquivo: `app/core/config.py`

As configuracoes principais agora sao:

- `app_name`
- `app_version`
- `api_prefix`
- `google_cloud_project`
- `firestore_equipes_collection`
- `firestore_confrontos_collection`
- `allowed_origins`

As colecoes padrao sao:

- `equipes`
- `confrontos`

Em desenvolvimento local, o SDK pode usar `GOOGLE_APPLICATION_CREDENTIALS`.
Em Cloud Run, o ideal e usar as credenciais padrao do ambiente.

## Dependencias Da API

Arquivo: `app/api/dependencies.py`

Esse arquivo monta a aplicacao:

- cria uma instancia unica de `FirestoreDatabase`
- instancia os repositorios concretos
- injeta os services usados pelas rotas

Assim, as rotas continuam desacopladas da tecnologia de persistencia.

## Persistencia Com Firestore

Arquivos:

- `app/infrastructure/persistence/firestore/firestore_client.py`
- `app/infrastructure/repositories/firestore_equipe_repository.py`
- `app/infrastructure/repositories/firestore_confronto_repository.py`

### `FirestoreDatabase`

Responsavel por:

- criar o client do Firestore
- apontar para o projeto configurado
- expor as colecoes de `equipes` e `confrontos`

### `FirestoreEquipeRepository`

Responsavel por:

- listar documentos da colecao `equipes`
- buscar por id
- criar
- atualizar
- remover

Cada equipe e salva como documento cujo id do documento e o proprio `id` numerico convertido para string.

### `FirestoreConfrontoRepository`

Faz a mesma ideia para a colecao `confrontos`.

Os documentos sao ordenados por `id` nas listagens para manter consistencia com o comportamento anterior.

## Camada De Dominio

As entidades continuam em:

- `app/domain/entities/equipe.py`
- `app/domain/entities/confronto.py`

Elas seguem sendo validadas com Pydantic e nao precisam conhecer o Firestore.

## Camada De Aplicacao

Os services seguem sendo responsaveis pelas regras:

- `EquipeService`: CRUD de equipes e geracao de ids
- `ConfrontoService`: CRUD de confrontos, filtros e geracao de ids
- `DashboardService`: consolidacao de totais e proximos confrontos

O ponto importante e que a logica de negocio nao mudou com a troca do banco. O que mudou foi apenas a implementacao concreta dos repositorios.

## API

As rotas continuam nas mesmas URLs:

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

Ou seja, a migracao para Firestore nao altera o contrato HTTP consumido pelo front-end.

## Exemplo De Fluxo

### Criar equipe

```text
Cliente -> POST /api/v1/equipes
       -> rota valida com EquipeInput
       -> EquipeService.criar_equipe()
       -> FirestoreEquipeRepository.criar()
       -> documento salvo em equipes/{id}
```

### Listar confrontos

```text
Cliente -> GET /api/v1/confrontos
       -> rota chama ConfrontoService.listar_confrontos()
       -> FirestoreConfrontoRepository.listar()
       -> documentos da colecao confrontos
       -> itens viram objetos Confronto
       -> resposta JSON para o cliente
```

## Resumo Final

Hoje o projeto esta preparado para rodar no Google Cloud com backend em Cloud Run e persistencia em Firestore, mantendo a mesma estrutura de camadas e o mesmo contrato de API para o frontend.
