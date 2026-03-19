# Guia Do Codigo

Este documento explica de forma simples como o back-end funciona hoje, qual e o papel de cada camada e como uma requisicao percorre o sistema ate gravar ou ler dados do arquivo JSON.

## Visao Geral

O projeto foi organizado em camadas para separar responsabilidades:

- `app/main.py`: cria a aplicacao FastAPI e registra middlewares e rotas.
- `app/core`: guarda configuracoes globais.
- `app/api`: define endpoints HTTP e dependencias injetadas nas rotas.
- `app/application`: concentra os servicos e os DTOs de entrada e saida.
- `app/domain`: descreve as entidades do negocio e os contratos dos repositorios.
- `app/infrastructure`: implementa a persistencia concreta em arquivo JSON.
- `data/database.json`: banco temporario da aplicacao.

Mesmo usando um JSON simples, a ideia foi manter o codigo pronto para evoluir. Isso ajuda a seguir principios como:

- Responsabilidade unica: cada arquivo faz uma coisa principal.
- Inversao de dependencia: os servicos dependem de contratos, nao do JSON diretamente.
- Baixo acoplamento: se trocar o JSON por banco real no futuro, a API muda pouco.

## Arquivo `app/main.py`

O `main.py` e o ponto de entrada da API.

Ele faz quatro coisas principais:

1. Importa o FastAPI e o middleware de CORS.
2. Carrega as configuracoes com `get_settings()`.
3. Cria a aplicacao com nome, versao e descricao.
4. Registra as rotas com o prefixo `/api/v1`.

Fluxo simplificado:

```text
main.py -> cria app -> aplica CORS -> inclui routers -> API pronta
```

O CORS existe para permitir que o front Angular em `http://localhost:4200` consiga chamar a API durante o desenvolvimento.

## Configuracoes em `app/core/config.py`

Esse arquivo centraliza configuracoes da aplicacao.

### Classe `Settings`

Ela guarda:

- `app_name`: nome exibido na documentacao.
- `app_version`: versao da API.
- `api_prefix`: prefixo comum das rotas.
- `database_file`: caminho do arquivo JSON.
- `allowed_origins`: origens liberadas no CORS.

### Funcao `_parse_allowed_origins`

Ela aceita dois formatos para a variavel de ambiente:

- JSON, por exemplo: `["http://localhost:4200"]`
- texto separado por virgula, por exemplo: `http://localhost:4200,http://localhost:3000`

### Funcao `get_settings`

Ela monta o objeto `Settings` uma vez so usando `@lru_cache`. Isso evita recriar configuracoes a cada requisicao.

## Dependencias em `app/api/dependencies.py`

Esse arquivo liga as camadas.

Ele cria:

- a instancia unica de `JsonDatabase`
- os repositorios concretos
- os servicos usados pelas rotas

Na pratica, ele funciona como um lugar de "montagem" da aplicacao.

Exemplo:

- a rota de equipes pede um `EquipeService`
- `dependencies.py` cria esse service
- o service recebe um `EquipeRepository`
- o repositorio concreto usado hoje e o `JsonEquipeRepository`

Isso deixa o endpoint limpo, sem saber como os dados sao salvos.

## Camada de Dominio em `app/domain`

Essa camada representa o negocio.

### Entidade `Equipe`

Arquivo: `app/domain/entities/equipe.py`

Modela uma equipe com:

- `id`
- `nome`
- `responsavel`
- `email`
- `membros`
- `icone`
- `cor`
- `sigla`

Ela usa Pydantic para validar os dados.

### Entidade `Membro`

Tambem no arquivo de equipe.

Modela um integrante da equipe com:

- `id`
- `nome`
- `habilidades`
- `funcao`

### Entidade `Confronto`

Arquivo: `app/domain/entities/confronto.py`

Representa uma partida entre duas equipes com:

- `id`
- `equipeA`
- `equipeB`
- `data`
- `horario`
- `local`
- `golsA`
- `golsB`
- `modalidade`
- `status`
- `destaque`
- `periodoAtual`
- `duracao`
- `fase`

### Enum `StatusConfronto`

Tambem em `confronto.py`.

Define os status permitidos:

- `agendado`
- `ao-vivo`
- `encerrado`

### Contratos de repositorio

Arquivos:

- `app/domain/repositories/equipe_repository.py`
- `app/domain/repositories/confronto_repository.py`

Esses arquivos dizem quais operacoes um repositorio precisa oferecer, por exemplo:

- listar
- obter por id
- criar
- atualizar
- remover

Eles nao dizem onde os dados ficam. So definem a interface esperada.

## Camada de Aplicacao em `app/application`

Essa camada organiza o que entra e o que sai da API, alem das regras de uso.

### DTOs de entrada

Arquivos:

- `app/application/dtos/equipe_dto.py`
- `app/application/dtos/confronto_dto.py`

DTO significa Data Transfer Object.

Esses modelos validam o payload que chega nas requisicoes `POST` e `PUT`.

Por exemplo:

- `EquipeInput` valida nome, responsavel, email e lista de membros.
- `ConfrontoInput` valida equipes, data, horario, local e dados opcionais do confronto.

Isso evita que o endpoint precise validar campo por campo manualmente.

### DTO de saida do dashboard

Arquivo: `app/application/dtos/dashboard_dto.py`

O `ResumoDashboard` padroniza a resposta de `/dashboard/resumo` com:

- `totalEquipes`
- `totalConfrontos`
- `confrontosEncerrados`
- `proximosConfrontos`

### Services

Arquivos:

- `app/application/services/equipe_service.py`
- `app/application/services/confronto_service.py`
- `app/application/services/dashboard_service.py`

Os services concentram a regra de aplicacao.

#### `EquipeService`

Responsavel por:

- listar equipes
- buscar equipe por id
- criar equipe
- atualizar equipe
- remover equipe
- gerar o proximo id da equipe
- gerar ids de membros quando eles nao vierem no payload

Exemplo importante:

Quando uma equipe nova e criada, o service:

1. busca o maior id atual
2. soma 1
3. monta a entidade `Equipe`
4. delega a gravacao ao repositorio

#### `ConfrontoService`

Responsavel por:

- listar confrontos
- filtrar por equipe
- filtrar por modalidade
- filtrar por status
- listar proximos confrontos
- buscar por id
- criar
- atualizar
- remover

Ele tambem calcula o proximo id automaticamente.

#### `DashboardService`

Responsavel por montar o resumo do dashboard.

Ele:

1. carrega todas as equipes
2. carrega todos os confrontos
3. conta totais
4. separa confrontos encerrados
5. pega os proximos confrontos
6. devolve tudo no formato `ResumoDashboard`

## Camada de API em `app/api/routes`

Essa camada expoe os endpoints HTTP.

Cada arquivo tem um `APIRouter` com rotas do seu dominio.

### `health.py`

Endpoint:

- `GET /api/v1/health`

Uso:

- verificar se a API esta respondendo

### `dashboard.py`

Endpoint:

- `GET /api/v1/dashboard/resumo`

Uso:

- alimentar os cards e a lista de proximos confrontos do dashboard do front-end

### `equipes.py`

Endpoints:

- `GET /api/v1/equipes`
- `GET /api/v1/equipes/{equipe_id}`
- `POST /api/v1/equipes`
- `PUT /api/v1/equipes/{equipe_id}`
- `DELETE /api/v1/equipes/{equipe_id}`

O arquivo recebe um `EquipeService` por dependencia. A rota fica responsavel so por:

- receber a requisicao
- validar os dados com Pydantic
- chamar o service
- retornar resposta ou erro 404

### `confrontos.py`

Endpoints:

- `GET /api/v1/confrontos`
- `GET /api/v1/confrontos/proximos`
- `GET /api/v1/confrontos/{confronto_id}`
- `POST /api/v1/confrontos`
- `PUT /api/v1/confrontos/{confronto_id}`
- `DELETE /api/v1/confrontos/{confronto_id}`

Essa rota tambem aceita filtros por query string em `GET /confrontos`:

- `equipe`
- `modalidade`
- `status`

## Persistencia em JSON

Hoje os dados ficam em `data/database.json`.

Estrutura atual:

```json
{
  "equipes": [],
  "confrontos": []
}
```

### Arquivo `app/infrastructure/persistence/json_db/json_database.py`

Esse arquivo faz o acesso bruto ao JSON.

Responsabilidades:

- garantir que o arquivo existe
- ler o conteudo do arquivo
- escrever o conteudo do arquivo
- garantir a estrutura minima com `equipes` e `confrontos`

Ou seja, ele nao sabe o que e uma equipe ou um confronto. Ele so sabe ler e escrever JSON.

### Repositorio `JsonEquipeRepository`

Arquivo: `app/infrastructure/repositories/json_equipe_repository.py`

Ele pega os dados crus do JSON e converte para objetos `Equipe`.

Responsabilidades:

- ler `data["equipes"]`
- transformar cada item em `Equipe`
- adicionar equipe nova
- atualizar equipe existente
- remover equipe

### Repositorio `JsonConfrontoRepository`

Arquivo: `app/infrastructure/repositories/json_confronto_repository.py`

Faz a mesma ideia para confrontos:

- ler `data["confrontos"]`
- transformar cada item em `Confronto`
- criar
- atualizar
- remover

## Fluxo completo de uma requisicao

### Exemplo 1: criar equipe

```text
Cliente -> POST /api/v1/equipes
       -> rota valida com EquipeInput
       -> EquipeService.criar_equipe()
       -> JsonEquipeRepository.criar()
       -> JsonDatabase.write()
       -> database.json atualizado
```

### Exemplo 2: listar confrontos

```text
Cliente -> GET /api/v1/confrontos
       -> rota chama ConfrontoService.listar_confrontos()
       -> JsonConfrontoRepository.listar()
       -> JsonDatabase.read()
       -> itens viram objetos Confronto
       -> resposta JSON para o cliente
```

## O que foi melhorado na refatoracao

Durante a revisao, os pontos mais importantes foram:

- alinhamento dos nomes e campos com o front Angular
- uso de rotas em portugues e no dominio real do projeto
- criacao de um DTO explicito para o resumo do dashboard
- separacao melhor das dependencias com provedores de repositorio e servico
- correcao da estrutura padrao do JSON para `equipes` e `confrontos`
- limpeza da documentacao para refletir o estado real da API

## O que ainda pode evoluir depois

Quando voce quiser dar o proximo passo, os candidatos naturais sao:

- adicionar testes automatizados para services e rotas
- trocar `data` e `horario` de `str` para tipos de data/hora reais
- criar repositorio com banco real, como PostgreSQL
- adicionar paginacao e ordenacao nas listagens
- incluir logs e tratamento global de excecoes
- criar schemas separados para resposta resumida e resposta detalhada

## Resumo final

Hoje o projeto esta organizado para ser simples de entender e ao mesmo tempo facil de evoluir.

Se voce quiser pensar no codigo em uma frase:

```text
rotas recebem -> services processam -> repositorios persistem -> JSON armazena
```

Esse desenho ajuda bastante porque cada parte tem um papel claro e voce nao precisa misturar regra de negocio com HTTP ou com leitura de arquivo.
