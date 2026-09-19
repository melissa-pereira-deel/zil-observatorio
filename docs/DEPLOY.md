# Deploy de produção

**Arquitetura:** frontend na **Vercel**, API + Postgres no **Render**.
Cada metade na ferramenta feita para ela, e ambas com free tier.

```
  zilobservatorio.org          api.zilobservatorio.org
  ┌──────────────────┐         ┌──────────────────────┐
  │  Next.js         │ ──────► │  FastAPI (Docker)    │
  │  Vercel          │  HTTPS  │  Render              │
  └──────────────────┘         │  └── Postgres        │
                               └──────────────────────┘
```

**Dá para subir sem domínio próprio.** Nesse caso a API fica em
`zil-api.onrender.com` e o site no domínio `.vercel.app` que a Vercel atribuir;
o DNS entra depois, sem refazer nada. A Parte 4 é a única que fica de lado.

**Não vão para produção, deliberadamente:**

| Serviço | Por quê |
|---|---|
| Typesense | Declarado no `docker-compose.yml` e **não usado em linha nenhuma de código**. Subir seria pagar por serviço morto |
| Redis + workers Celery | Só fazem sync agendado. Enquanto o volume for baixo, rodar o pipeline da sua máquina é suficiente — ver "Quando ligar os workers" |
| `/ranking` e `/parlamentar/[id]` | As 7 classificações estão `validacao: nao-validado`; o ranking não tem base. Ver "A flag do ranking" |
| Indexação por buscadores | Estar no ar e estar no Google são coisas diferentes, e só a primeira é reversível. Ver "A flag da indexação" |

---

## Antes de começar

Tenha em mãos:

- Conta na [Render](https://render.com) e na [Vercel](https://vercel.com) (ambas aceitam login pelo GitHub)
- Acesso ao DNS de `zilobservatorio.org`
- O repositório conectado às duas plataformas

> **Repositório privado:** as duas plataformas conseguem acessar repositórios
> privados depois que você autoriza o app delas no GitHub. Não é preciso tornar
> o repo público para o deploy — só para destravar o GitHub Actions.

---

## Parte 1 — API + banco no Render

### 1.1 Criar pelo blueprint

O arquivo [`render.yaml`](../render.yaml) na raiz descreve o serviço e o banco.

1. No painel do Render: **New → Blueprint**
2. Selecione o repositório `zil-observatorio`
3. O Render lê o `render.yaml` e propõe criar `zil-api` (web) e `zil-db` (Postgres)
4. Confirme

O `ADMIN_TOKEN` é gerado automaticamente pelo Render e nunca aparece em log.

### 1.2 Preencher a variável que falta

`CORS_ORIGINS` fica marcada como `sync: false` — ou seja, você preenche no
painel. **O frontend ainda não existe**, então deixe vazia por enquanto e volte
aqui depois da Parte 3, quando souber o domínio exato que a Vercel atribuiu.

Se já tiver domínio próprio, pode preencher de uma vez com
`https://zilobservatorio.org`.

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

> **Free tier do Render:** o serviço hiberna após um período sem tráfego e o
> primeiro acesso seguinte demora alguns segundos. O Postgres gratuito tem
> prazo de validade — confira as condições vigentes no painel, porque elas
> mudam, e programe a migração para um plano pago ou outro provedor antes do
> vencimento. **Não descubra isso pelo banco sumindo.**

---

## Parte 2 — Popular o banco

O banco sobe vazio. O pipeline roda da sua máquina, apontando para produção:

```bash
cd ~/zil-observatorio
DATABASE_URL="<Internal Database URL do painel do Render>" .venv/bin/python scripts/seed.py
```

Isso sincroniza da API da Câmara as votações já curadas em `data/direcoes/`,
aplica as direções e recalcula os scores.

Para a base de proposições enriquecidas — que é o conteúdo publicável hoje:

```bash
DATABASE_URL="<...>" .venv/bin/python scripts/sync_pipeline.py
```

> Use a **External Database URL** se estiver rodando de fora do Render.

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

## Parte 4 — DNS (só quando houver domínio próprio)

Pule esta parte se estiver subindo nos domínios das plataformas. Voltar aqui
depois não exige refazer nada — só acrescentar o domínio nos dois painéis,
atualizar `NEXT_PUBLIC_API_URL` e `CORS_ORIGINS`, e redeploy do frontend.


No provedor de DNS de `zilobservatorio.org`:

| Tipo | Nome | Aponta para | De quem |
|---|---|---|---|
| `A` ou `CNAME` | `@` (raiz) | o valor que a Vercel mostrar | Vercel |
| `CNAME` | `www` | o valor que a Vercel mostrar | Vercel |
| `CNAME` | `api` | `zil-api.onrender.com` | Render |

Adicione o domínio nos dois painéis (**Vercel → Settings → Domains**,
**Render → Settings → Custom Domain**) — eles emitem o certificado HTTPS
automaticamente depois que o DNS propaga.

Depois que `api.zilobservatorio.org` estiver de pé, confirme que
`CORS_ORIGINS` no Render contém exatamente a origem do frontend, **com
`https://` e sem barra no final**.

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

## Quando ligar os workers

Os workers Celery fazem sync automático (deputados semanal, votações a cada 6h,
scores diário) e exigem Redis mais dois serviços sempre de pé. Enquanto o
volume for baixo, rodar `scripts/sync_pipeline.py` da sua máquina entrega o
mesmo resultado sem custo nem superfície de operação.

Vale ligá-los quando: o sync manual passar a ser esquecido, ou o volume de
proposições tornar a execução local inviável.

Nesse momento, acrescentar ao `render.yaml`: um `type: redis`, um
`type: worker` para o Celery worker e outro para o beat — os três com as mesmas
variáveis da API. A imagem já os comporta: o Dockerfile copia `apps/workers` e
`packages` para dentro dela.

---

## Checklist

- [ ] Blueprint criado no Render; `zil-api` e `zil-db` no ar
- [ ] `/health` responde 200
- [ ] `/bussula` retorna 4 indicadores (se vier `[]`, o contexto do build está errado)
- [ ] Banco populado com `scripts/seed.py`
- [ ] Projeto na Vercel com **Root Directory `apps/web`**
- [ ] `NEXT_PUBLIC_API_URL` apontando para a API, sem barra no final
- [ ] `CORS_ORIGINS` contém a origem exata do frontend
- [ ] `/ranking` e `/parlamentar/<id>` servem a página `/em-breve`
- [ ] `/robots.txt` diz `Disallow: /` e a home traz `<meta name="robots" content="noindex">`
- [ ] Home e `/bussula` carregam dados reais
- [ ] Anotada a URL real da API (o Render muda o nome se já estiver tomado)
- [ ] Anotado quando o Postgres gratuito vence
- [ ] *(com domínio próprio)* DNS propagado e HTTPS ativo nos dois

> `/proposicoes` fica **vazia** enquanto `scripts/sync_pipeline.py` não rodar.
> É o esperado: o `seed.py` só traz as votações curadas. A página tem empty
> state explicando.
