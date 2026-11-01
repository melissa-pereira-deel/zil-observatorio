# Deploy de produção

**Arquitetura:** frontend na **Vercel**, API + Postgres no **Render**, sync
de dados agendado no **GitHub Actions**. Frontend e API nos planos gratuitos;
o Postgres no menor plano pago, porque o gratuito expira (ver 1.1).

```
  zilobservatorio.com.br       api.zilobservatorio.com.br
  ┌──────────────────┐         ┌──────────────────────┐
  │  Next.js         │ ──────► │  FastAPI (Docker)    │
  │  Vercel          │  HTTPS  │  Render              │
  └──────────────────┘         │  └── Postgres        │
                               └──────────▲───────────┘
                                          │ sync agendado
                               ┌──────────┴───────────┐
                               │  GitHub Actions      │
                               │  scripts/agenda.py   │
                               └──────────────────────┘
```

**Dá para subir sem domínio próprio.** Nesse caso a API fica em
`zil-api.onrender.com` e o site no domínio `.vercel.app` que a Vercel atribuir;
o DNS entra depois, sem refazer nada. A Parte 4 é a única que fica de lado.

**Não vão para produção, deliberadamente:**

| Serviço | Por quê |
|---|---|
| Typesense | Declarado no `docker-compose.yml` e **não usado em linha nenhuma de código**. Subir seria pagar por serviço morto |
| Redis + workers Celery | Só fazem sync agendado, e o agendamento roda no GitHub Actions, de graça — ver "Cron" |
| `/ranking` e `/parlamentar/[id]` | As 7 classificações estão `validacao: nao-validado`; o ranking não tem base. Ver "A flag do ranking" |
| Indexação por buscadores | Estar no ar e estar no Google são coisas diferentes, e só a primeira é reversível. Ver "A flag da indexação" |

---

## Antes de começar

Tenha em mãos:

- Conta na [Render](https://render.com) e na [Vercel](https://vercel.com) (ambas aceitam login pelo GitHub)
- Acesso ao painel de DNS da **GoDaddy** para `zilobservatorio.com.br`
- O repositório conectado às duas plataformas

> **O repositório é público**, e por isso os minutos de GitHub Actions não
> custam nada — é o que torna o cron gratuito. Render e Vercel acessam o
> repositório depois que você autoriza o app delas no GitHub.

---

## Parte 1 — API + banco no Render

### 1.1 Criar pelo blueprint

O arquivo [`render.yaml`](../render.yaml) na raiz descreve o serviço e o banco.

1. No painel do Render: **New → Blueprint**
2. Selecione o repositório `zil-observatorio`
3. O Render lê o `render.yaml` e propõe criar `zil-api` (web) e `zil-db` (Postgres)
4. **Confira no resumo que o `zil-db` está no plano `basic-256mb` e o preço
   mensal**, e confirme

**Por que o banco é pago:** o Postgres gratuito do Render expira 30 dias depois
de criado e é apagado após 14 dias de carência, sem backup. O `basic-256mb` é o
menor plano pago e, ao contrário do gratuito, tem backup. A API continua no
plano gratuito.

O `ADMIN_TOKEN` é gerado automaticamente pelo Render e nunca aparece em log.

### 1.2 Preencher a variável que falta

`CORS_ORIGINS` fica marcada como `sync: false` — ou seja, você preenche no
painel. **O frontend ainda não existe**, então deixe vazia por enquanto e volte
aqui depois da Parte 3, quando souber o domínio exato que a Vercel atribuiu.

Com o domínio próprio já apontado, o valor final é
`https://zilobservatorio.com.br`.

### 1.3 Conferir que subiu

O primeiro deploy roda `alembic upgrade head` antes de servir (ver
`apps/api/entrypoint.sh`), então o schema é criado sozinho.

```bash
curl https://zil-api.onrender.com/health
curl https://zil-api.onrender.com/bussula
```

O segundo precisa retornar os 4 indicadores. **Se vier `[]`**, os dados
editoriais não entraram na imagem — confira que o build usou a raiz do
repositório como contexto (`dockerContext: .`).

> **API no plano gratuito:** o serviço dorme após 15 minutos sem tráfego e
> leva cerca de um minuto para acordar. O workflow `acordar-api` evita isso
> com um ping a cada 14 minutos — ver "Cron".

---

## Parte 2 — Popular o banco

O banco sobe vazio. Quem o popula são os mesmos workflows que depois o mantêm
atualizado (ver "Cron"), rodados à mão uma vez.

### 2.1 Segredos do repositório

Em **GitHub → Settings → Secrets and variables → Actions → New repository
secret**:

| Segredo | Valor |
|---|---|
| `PRODUCAO_DATABASE_URL` | a **External Database URL** do `zil-db` (painel do Render → Connect) |
| `ANTHROPIC_API_KEY` | a chave da Anthropic — só o enriquecimento usa |

Segredo de Actions não aparece em log nem para quem abre um PR de fora.

### 2.2 Rodar, nesta ordem

Em **Actions**, cada um com **Run workflow**:

1. `dados` → job **`cadastros`** — deputados e senadores
2. `direcoes` — as votações curadas em `data/direcoes/`, direções e scores
3. `dados` → job **`diario`** — votações e Senado do ano, descoberta de
   proposições do ano, scores
4. `dados` → job **`enriquecer`** com o limite que couber no orçamento — as
   proposições descobertas entram como pendentes, e o cron semanal só
   processa 30 por vez

Cada passo grava uma linha em `ingestion_runs`, com status e contagens.

> **Alternativa da sua máquina:** `DATABASE_URL="<External Database URL>"
> .venv/bin/python scripts/agenda.py cadastros` (e os demais jobs) faz o
> mesmo. Para trazer proposições de anos anteriores, `agenda.py proposicoes
> --ano-inicio 2020` — o `diario` só busca as do ano corrente.

---

## Parte 3 — Frontend na Vercel

### 3.1 Criar o projeto

1. **Add New → Project**, selecione `zil-observatorio`
2. **Root Directory: `apps/web`** ← passo mais fácil de errar; o Next.js não
   está na raiz do repositório
3. Framework: Next.js (detectado automaticamente)

### 3.2 Variáveis de ambiente

| Variável | Valor | Para quê |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | a URL da API, com `https://` e **sem barra no final** | De onde o browser busca os dados |
| `NEXT_PUBLIC_RANKING_PUBLICO` | não definir (ou `false`) | Mantém o ranking fora do ar |
| `NEXT_PUBLIC_INDEXACAO_PUBLICA` | não definir (ou `false`) | Mantém o site fora dos buscadores |

Sem domínio próprio, `NEXT_PUBLIC_API_URL` é `https://zil-api.onrender.com` —
confira a URL real no painel, porque o Render muda o nome se `zil-api` já
estiver tomado.

> **`NEXT_PUBLIC_*` é gravada no bundle durante o build.** Trocar o valor no
> painel não muda o site: é preciso **redeploy**. Isso vale para as três.

Se for usar os deploys de preview da Vercel, acrescente o domínio deles ao
`CORS_ORIGINS` no Render — senão o preview carrega sem dado nenhum e parece
bug de frontend.

### 3.3 Fechar o círculo do CORS

Com o domínio da Vercel em mãos, volte ao Render e preencha `CORS_ORIGINS` com
a origem exata — **com `https://`, sem barra no final**. É só variável de
ambiente: o serviço reinicia, não reconstrói.

Sem isso o site sobe bonito e **vazio**, porque as páginas buscam os dados pelo
browser. Parece bug de frontend e não é.

---

## Parte 4 — DNS na GoDaddy

Pule esta parte se estiver subindo nos domínios das plataformas. Voltar aqui
depois não exige refazer nada — só acrescentar o domínio nos dois painéis,
atualizar `NEXT_PUBLIC_API_URL` e `CORS_ORIGINS`, e redeploy do frontend.

**Adicione o domínio nos dois painéis primeiro** (**Vercel → Settings →
Domains**, **Render → Settings → Custom Domain**). Cada uma mostra o valor
exato a apontar — use o que aparecer lá, não o que estiver escrito aqui,
porque esses valores mudam. As duas só servem o domínio e só emitem o
certificado depois que ele está reivindicado no painel delas.

Depois, em **GoDaddy → My Products → zilobservatorio.com.br → DNS**:

| Tipo | Nome | Aponta para | De quem |
|---|---|---|---|
| `A` | `@` (raiz) | o IP que a Vercel mostrar | Vercel |
| `CNAME` | `www` | o alvo que a Vercel mostrar | Vercel |
| `CNAME` | `api` | o alvo que o Render mostrar (`zil-api.onrender.com`) | Render |

> **Por que `A` na raiz e não `CNAME`:** o DNS não permite CNAME no apex de um
> domínio, e a GoDaddy segue essa regra. Para `@` só existe registro `A`.

**Antes de criar, apague o que a GoDaddy já deixou lá.** Domínio estacionado
vem com um `A` em `@` apontando para a página de venda e um `CNAME www`. Se o
registro antigo ficar, o site alterna entre a Vercel e o estacionamento, de
forma intermitente e difícil de diagnosticar.

Os certificados HTTPS saem sozinhos depois que o DNS propaga. A GoDaddy
costuma levar de minutos a algumas horas.

```bash
dig +short zilobservatorio.com.br A
dig +short api.zilobservatorio.com.br CNAME
```

Depois que `api.zilobservatorio.com.br` estiver de pé, confirme que
`CORS_ORIGINS` no Render contém exatamente a origem do frontend, **com
`https://` e sem barra no final**.

> **`www` e a raiz são origens diferentes para o CORS.** Se a Vercel estiver
> redirecionando `www` para a raiz, basta `https://zilobservatorio.com.br`. Se
> as duas servirem o site, as duas precisam estar em `CORS_ORIGINS`.

### Os outros dois domínios

`zilmanifesto.org` e `zilmanifesto.com.br` também são do projeto e encaminham
para o canônico. Isso é **Forwarding** na GoDaddy (*My Products → o domínio →
Forwarding*), não registro de DNS: um 301 para `https://zilobservatorio.com.br`.
Buscadores consolidam os três num endereço só.

### E-mail no domínio

O `CODE_OF_CONDUCT.md` manda reportar violações para
**conduta@zilobservatorio.com.br**. Esse endereço precisa **existir** — hoje o
domínio não tem registro MX nenhum, ou seja, não recebe e-mail. Um
encaminhamento da própria GoDaddy para a sua caixa pessoal resolve.

```bash
dig +short zilobservatorio.com.br MX    # vazio = o canal de conduta não funciona
```

---

## A flag do ranking

`/ranking` e `/parlamentar/[id]` não são apenas escondidos da navegação: um
middleware (`apps/web/middleware.ts`) fecha as rotas na borda e serve
`/em-breve`, que explica por quê. Esconder link não é esconder página — sem o
middleware, as rotas continuariam acessíveis por URL direta e por buscador.

Para publicar o ranking quando a curadoria sustentar:

1. Reveja as classificações e troque `validacao: nao-validado` nos arquivos de
   `data/direcoes/`
2. Defina `NEXT_PUBLIC_RANKING_PUBLICO=true` na Vercel
3. Redeploy

O critério não é técnico. Ver `docs/GOVERNANCE.md`, seção "Estado atual da
governança".

---

## A flag da indexação

Estar no ar e estar no Google são coisas diferentes, e **só a primeira é
reversível**. Uma URL indexada pode continuar aparecendo em buscas, em cache e
em prints muito depois de você mudar a página. Enquanto as 7 classificações
estiverem `nao-validado`, um resultado de busca levaria alguém direto a um
número que o próprio projeto não sustenta.

Por isso o padrão é **não indexar**, em duas camadas — porque uma não substitui
a outra:

| Camada | Arquivo | O que faz |
|---|---|---|
| `robots.txt` | `apps/web/app/robots.ts` | pede ao buscador que **não rastreie** |
| `<meta name="robots">` | `apps/web/app/layout.tsx` | impede **indexar** uma URL descoberta por link de fora |

Para abrir aos buscadores quando a curadoria sustentar:

1. `NEXT_PUBLIC_INDEXACAO_PUBLICA=true` na Vercel
2. **Redeploy** — o valor é gravado no bundle durante o build

Conferir depois:

```bash
curl https://<seu-dominio>/robots.txt          # deve dizer Allow: /
curl -s https://<seu-dominio>/ | grep robots   # não deve haver meta noindex
```

---

## Cron

O agendamento de produção roda no **GitHub Actions**, não em workers Celery:
sem Redis, sem serviço sempre de pé, e de graça porque o repositório é
público. Os jobs são subcomandos de [`scripts/agenda.py`](../scripts/agenda.py),
que chama as mesmas funções das tasks Celery e registra cada passo em
`ingestion_runs` do mesmo jeito.

| Workflow | Quando (BRT) | O que faz |
|---|---|---|
| `dados` · `diario` | todo dia, 04:15 | votações da Câmara e do Senado do ano, descoberta de proposições do ano e votações de cada uma, direções e Score ZIL |
| `dados` · `cadastros` | segunda, 03:30 | deputados e senadores |
| `dados` · `enriquecer` | quarta, 06:00 | resumo com LLM das 30 proposições pendentes mais recentes |
| `direcoes` | a cada merge que muda `data/direcoes/` | valida, sincroniza as votações curadas, aplica direções e recalcula scores |
| `acordar-api` | a cada 14 min | `GET /health`, para a API gratuita não dormir |

**Segredos:** `PRODUCAO_DATABASE_URL` (todos) e `ANTHROPIC_API_KEY` (só
`enriquecer`, e só no passo que roda o LLM). **Variável:** `API_PUBLICA_URL`
(por exemplo `https://api.zilobservatorio.com.br`) — sem ela o `acordar-api`
termina sem fazer nada, para não falhar a cada 14 minutos antes do deploy.

**Custo do LLM:** o limite de 30 por semana deixa o gasto previsível. Para
mudar, edite o `--limite` em `.github/workflows/dados.yml`, ou rode
`enriquecer` à mão com outro valor.

**Falhas:** uma execução que falha fica vermelha em Actions e o GitHub avisa
por e-mail. Os passos seguintes de um job rodam mesmo assim (uma falha no
Senado não impede o score da Câmara), mas o job termina vermelho.

**Limites do agendador do GitHub:**

- horários em UTC no arquivo; atrasos de alguns minutos em horário de pico, e
  execuções puladas de vez em quando — o `acordar-api` pode falhar em acordar
  a API numa janela ou outra;
- **workflows agendados em repositório público são desligados após 60 dias
  sem commit.** O GitHub avisa por e-mail antes; reative em Actions. Os
  commits do próprio cron não contam, porque ele não faz commit.

**Desligar:** Actions → o workflow → **Disable workflow**.

**Se a API acordada por cron incomodar:** troque `plan: free` por
`plan: starter` no serviço `zil-api` do `render.yaml` e apague
`.github/workflows/acordar-api.yml`.

**E os workers Celery?** Continuam no repositório para quem roda o
`docker compose` local. Em produção, o Actions cobre o mesmo agendamento.

---

## Checklist

- [ ] Blueprint criado no Render; `zil-api` e `zil-db` no ar
- [ ] `/health` responde 200
- [ ] `/bussula` retorna 4 indicadores (se vier `[]`, o contexto do build está errado)
- [ ] `zil-db` no plano pago (`basic-256mb`), não no gratuito
- [ ] Segredos `PRODUCAO_DATABASE_URL` e `ANTHROPIC_API_KEY` no repositório
- [ ] Banco populado pelos workflows `dados` (`cadastros`, `diario`) e `direcoes`, todos verdes
- [ ] Variável `API_PUBLICA_URL` definida depois do DNS; `acordar-api` verde
- [ ] Projeto na Vercel com **Root Directory `apps/web`**
- [ ] `NEXT_PUBLIC_API_URL` apontando para a API, sem barra no final
- [ ] `CORS_ORIGINS` contém a origem exata do frontend
- [ ] `/ranking` e `/parlamentar/<id>` servem a página `/em-breve`
- [ ] `/robots.txt` diz `Disallow: /` e a home traz `<meta name="robots" content="noindex">`
- [ ] Home e `/bussula` carregam dados reais
- [ ] Anotada a URL real da API (o Render muda o nome se já estiver tomado)
- [ ] Registros de estacionamento da GoDaddy apagados antes de criar os novos
- [ ] DNS propagado e HTTPS ativo nos dois
- [ ] `zilmanifesto.org` e `zilmanifesto.com.br` encaminhando para o canônico
- [ ] `dig +short zilobservatorio.com.br MX` devolve algo — senão o canal de conduta não recebe

> As proposições aparecem em `/proposicoes` assim que o `diario` roda, mas
> sem resumo até o `enriquecer` processá-las. A página tem empty state
> explicando.
