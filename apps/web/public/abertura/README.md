# Vídeo de abertura da home

Esta pasta guarda o vídeo de fundo da abertura (`app/page.tsx` →
`components/VideoAbertura.tsx`). A página confere quais arquivos existem
quando é gerada — a cada acesso em desenvolvimento, no build em produção:
sem vídeo e sem poster, mostra um fundo provisório nas cores da bandeira.
**Para publicar o vídeo, basta colocar os arquivos aqui e fazer o deploy** —
não há flag nem código a mudar.

## Arquivos esperados

| Arquivo | Uso | Especificação |
| --- | --- | --- |
| `abertura.mp4` | desktop | 1920×1080, H.264, **sem faixa de áudio**, 10–20 s, loop sem corte visível, ≤ 8 MB |
| `abertura-celular.mp4` | telas < 768px | 1080×1350 (4:5) ou 720×1280 (9:16), ≤ 3 MB. Sem ele, o celular usa o de desktop |
| `abertura-poster.webp` | primeiro quadro, desktop | 1600 px de largura, ≤ 200 KB. Aparece antes do vídeo carregar e com movimento reduzido |
| `abertura-poster-celular.webp` | primeiro quadro, celular | 1000 px de largura |

Hospedado fora do repositório (Vercel Blob, CDN), use as variáveis
`NEXT_PUBLIC_ABERTURA_VIDEO_URL` e `NEXT_PUBLIC_ABERTURA_VIDEO_CELULAR_URL`
no `.env` e na Vercel; elas têm precedência sobre os arquivos daqui. Como
toda `NEXT_PUBLIC_*`, mudar exige novo deploy.

## Como o vídeo é exibido

- Cobre a abertura de borda a borda (`object-fit: cover`) e passa por baixo
  da barra de navegação, que o desfoca.
- O texto fica embaixo, à esquerda. Um véu escurece a base e a metade
  esquerda, para o texto ser legível sobre qualquer quadro. **Deixe as
  partes mais calmas do vídeo no terço inferior e à esquerda**; o assunto
  principal funciona melhor no alto e à direita.
- Sempre mudo, em loop. O celular baixa só o arquivo de celular.
- Com "reduzir movimento" ligado no sistema, o vídeo não carrega: fica o
  poster.
- Há um botão de pausa no canto inferior direito (exigência de
  acessibilidade para movimento automático com mais de 5 segundos).

## Cuidados de conteúdo

Do guia de fotografia do design system (ZIL Interface › Fotografia):

- Gente trabalhando antes de máquina; máquina antes de cerimônia.
- **Nenhum político em primeiro plano.** O observatório é apartidário.
- Sem pessoas reconhecíveis sem autorização de uso de imagem. Vídeo gerado
  por IA não deve imitar uma pessoa real.
- Bandeira e símbolos nacionais com respeito ao uso previsto na Lei
  5.700/1971 (sem deformar, sem sobrepor marcas).
- Prefira cenas que o projeto possa sustentar: indústria, campo, energia,
  ciência, infraestrutura.

## Exportar os arquivos

```bash
# Vídeo de desktop: 1080p, H.264, sem áudio, otimizado para começar a tocar cedo
ffmpeg -i original.mp4 -an -vf scale=1920:-2 -c:v libx264 -crf 26 -preset slow -movflags +faststart abertura.mp4

# Celular, recorte 4:5 no centro
ffmpeg -i original.mp4 -an -vf "crop=ih*4/5:ih,scale=1080:-2" -c:v libx264 -crf 28 -preset slow -movflags +faststart abertura-celular.mp4

# Posters a partir do primeiro quadro
ffmpeg -i abertura.mp4 -frames:v 1 -vf scale=1600:-1 abertura-poster.webp
ffmpeg -i abertura-celular.mp4 -frames:v 1 -vf scale=1000:-1 abertura-poster-celular.webp
```
