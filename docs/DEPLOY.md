# Deploy de produção

**Arquitetura:** frontend na **Vercel**, API + Postgres no **Render**.
Cada metade na ferramenta feita para ela, e ambas com free tier.

```
  zilobservatorio.com.br       api.zilobservatorio.com.br
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
- Acesso ao painel de DNS da **GoDaddy** para `zilobservatorio.com.br`
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
- [ ] Registros de estacionamento da GoDaddy apagados antes de criar os novos
- [ ] DNS propagado e HTTPS ativo nos dois
- [ ] `zilmanifesto.org` e `zilmanifesto.com.br` encaminhando para o canônico
- [ ] `dig +short zilobservatorio.com.br MX` devolve algo — senão o canal de conduta não recebe

> `/proposicoes` fica **vazia** enquanto `scripts/sync_pipeline.py` não rodar.
> É o esperado: o `seed.py` só traz as votações curadas. A página tem empty
> state explicando.
