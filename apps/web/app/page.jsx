import { useState } from "react";

// ── Design tokens ──
const G="#1B6B3A",GD="#0E3D20",GL="#E8F0EA",Y="#C4940A",BG="#F0EBE0",FG="#1A1714",FS="#5C564C",FM="#8A8478",DV="#D6CFC3",CB="#E8E2D6",W="#FDFBF7",OR="#C4760A";
const f={d:"'Archivo Black',sans-serif",b:"'Archivo',sans-serif",m:"'IBM Plex Mono',monospace"};

// ── Data ──
const DEPS=[
  {n:"Ana Cristina Lima",p:"PSB",u:"GO",s:7.2,v:14},
  {n:"Carlos Eduardo Rocha",p:"PL",u:"GO",s:-3.8,v:11},
  {n:"Marina Santos Oliveira",p:"PT",u:"GO",s:5.1,v:9},
  {n:"Roberto Almeida Jr.",p:"PP",u:"GO",s:-1.4,v:12},
  {n:"Fernanda Bastos",p:"MDB",u:"GO",s:2.9,v:8},
  {n:"João Pedro Vieira",p:"PSOL",u:"GO",s:6.8,v:10},
];
const UFS=["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT","PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"];
const PAUTAS=[["ZIL-FER","Fertilizantes","🌱"],["ZIL-MIN","Minerais","⛏️"],["ZIL-SEM","Semicondutores","🔬"],["ZIL-ENE","Energia","⚡"],["ZIL-DIG","Digital","📡"],["ZIL-DEF","Defesa","🛡️"],["ZIL-EDU","Capital Humano","🎓"],["ZIL-AGR","Agro-Indústria","🏭"],["ZIL-COM","Comércio","🌐"]];

const CONQUISTAS=[["1906","Santos Dumont voa","Disseram que era impossível."],["1969","Embraer","A terceira maior fabricante de aviões do mundo."],["1972","Embrapa","Cerrado vira celeiro de 1 bilhão de pessoas."],["1975","Proálcool","Crise do petróleo? Inventamos alternativa."],["1994","Plano Real","2.477% de inflação/ano. Resolvido."],["1996","Urna eletrônica","150 milhões de votos. Resultado em horas."],["2006","Pré-sal","Tecnologia que nenhum outro país dominava."],["2020","PIX","US$4 mi para criar. US$5,7 bi economizados. O mundo copia."]];

const PRINC=[["CONSENSO, NÃO POLARIZAÇÃO","Redes sociais amplificam divisão porque engajamento raivoso gera cliques. O ZIL faz o oposto: usa tecnologia que identifica e amplifica os pontos onde grupos opostos concordam."],["SINAL, NÃO RUÍDO","O debate público está afogado em ruído. O ZIL é o lugar onde há clareza: dados verificáveis, metas mensuráveis, progresso rastreável."],["PROJETO DE ESTADO, NÃO DE GOVERNO","Nenhum programa estratégico pode morrer com um mandato. Criamos tecnologia que mede continuidade, registra compromissos e torna a descontinuidade visível."],["APARTIDÁRIO POR DESIGN","O ZIL não lança candidatos, não apoia partidos. Tem método. O agricultor conservador e o sindicalista progressista concordam que importar 87% dos fertilizantes é absurdo."],["ABERTO E AUDITÁVEL","Todo dado, algoritmo, classificação e decisão é pública. Código aberto. Processo rastreável. Legitimidade vem de transparência."],["COMPROMISSO TEM REGISTRO","Todo parlamentar que assumir compromisso terá esse compromisso registrado publicamente. A plataforma cruza promessa com voto real."]];

const MECS=[["Deliberação por consenso","Inspirado no Polis/vTaiwan — que gerou legislação real para 23 milhões de taiwaneses. Ninguém responde a ninguém: apenas propõe, concorda ou discorda. O algoritmo identifica declarações-ponte entre grupos opostos."],["A bússola","Marcos estratégicos definidos pela comunidade, com métricas verificáveis. Monitorados trimestralmente, independente de quem governa. Quando um governo muda, os marcos não mudam."],["Compromisso rastreável","Parlamentares registram metas específicas. O sistema cruza cada compromisso com dados reais de votação e execução orçamentária."],["Score de alinhamento","Cada parlamentar tem score calculado por fórmula transparente. Qualquer cidadão pode ver, auditar e contestar."],["Continuidade mensurável","Índice público que mostra quanto cada governo manteve, expandiu ou desmontou dos programas estratégicos anteriores."]];

const PERGS=["O Brasil processa os recursos que extrai ou exporta matéria-prima barata?","Nossos fertilizantes, chips e combustíveis dependem de importação?","Os compromissos dos nossos representantes estão sendo cumpridos?","Os programas estratégicos estão sendo mantidos entre governos?","O país está mais ou menos soberano do que há um ano?"];

// ── Components ──
function Score({s,sz=38}){
  const c=s>=5?G:s>=2?G:s>=-2?Y:s>=-5?OR:"#B54A3A";
  const bg=s>=2?GL:s>=-2?"#FDF6E3":"#FEF0EE";
  return <div style={{width:sz,height:sz,borderRadius:"50%",border:`2px solid ${c}`,background:bg,display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:sz*.3,color:c,flexShrink:0}}>{s>0?"+":""}{s.toFixed(1)}</div>;
}

function Btn({children,primary,full,onClick,style:st}){
  return <button onClick={onClick} style={{fontFamily:f.d,fontSize:11,letterSpacing:2,padding:"13px 24px",width:full?"100%":"auto",border:primary?"none":`1.5px solid ${FG}`,background:primary?G:"transparent",color:primary?"#fff":FG,cursor:"pointer",textTransform:"uppercase",transition:"all .15s",...st}}
    onMouseEnter={e=>{if(primary)e.currentTarget.style.background=GD;else{e.currentTarget.style.background=FG;e.currentTarget.style.color=BG}}}
    onMouseLeave={e=>{e.currentTarget.style.background=primary?G:"transparent";e.currentTarget.style.color=primary?"#fff":FG}}>{children}</button>;
}

export default function ZIL(){
  const [pg,setPg]=useState("manifesto");
  const [dep,setDep]=useState(null);
  const [q,setQ]=useState("");
  const [logged,setLogged]=useState(false);
  const [nm,setNm]=useState("");
  const [em,setEm]=useState("");
  const [uf,setUf]=useState("GO");
  const [pautas,setPautas]=useState(new Set());
  const [fade,setFade]=useState(true);
  const [ct,setCt]=useState(148207);
  const [signed,setSigned]=useState(false);
  const [snm,setSnm]=useState("");
  const [sct,setSct]=useState("");
  const [cp,setCp]=useState(false);

  const go=(p,d)=>{setFade(false);setTimeout(()=>{setPg(p);if(d)setDep(d);setFade(true);window.scrollTo?.({top:0})},150)};
  const tp=c=>{const n=new Set(pautas);n.has(c)?n.delete(c):n.add(c);setPautas(n)};
  const ini=s=>s.split(" ").map(w=>w[0]).slice(0,2).join("");
  const fdeps=DEPS.filter(d=>!q||d.n.toLowerCase().includes(q.toLowerCase())||d.p.toLowerCase().includes(q.toLowerCase())).sort((a,b)=>b.s-a.s);

  const Nav=({back,title,right})=>(
    <div style={{display:"flex",alignItems:"center",gap:10,padding:"14px 20px",borderBottom:`1px solid ${DV}`,background:BG,position:"sticky",top:0,zIndex:10}}>
      {back&&<button onClick={()=>go(back)} style={{background:"none",border:"none",cursor:"pointer",fontSize:18,color:FM,padding:"2px 6px"}}>←</button>}
      <button onClick={()=>go("manifesto")} style={{background:"none",border:"none",cursor:"pointer",fontFamily:f.d,fontSize:15,letterSpacing:1,color:FG}}>ZIL</button>
      <div style={{flex:1}}/>
      {title&&<span style={{fontFamily:f.m,fontSize:9,letterSpacing:2,color:FM,textTransform:"uppercase"}}>{title}</span>}
      {right}
    </div>
  );

  const TopNav=()=>(
    <Nav right={logged?(
      <button onClick={()=>go("dashboard")} style={{width:26,height:26,borderRadius:"50%",background:G,border:"none",cursor:"pointer",fontFamily:f.d,fontSize:10,color:"#fff"}}>{(nm||"U")[0].toUpperCase()}</button>
    ):(
      <button onClick={()=>go("register")} style={{fontFamily:f.m,fontSize:9,letterSpacing:1,padding:"6px 12px",border:`1px solid ${G}`,background:"transparent",color:G,cursor:"pointer",transition:"all .15s"}}
        onMouseEnter={e=>{e.currentTarget.style.background=G;e.currentTarget.style.color="#fff"}}
        onMouseLeave={e=>{e.currentTarget.style.background="transparent";e.currentTarget.style.color=G}}>ENTRAR</button>
    )}/>
  );

  return(
    <div style={{background:BG,minHeight:"100vh",maxWidth:440,margin:"0 auto",fontFamily:f.b,color:FG,boxShadow:"0 0 80px rgba(0,0,0,.06)"}}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Archivo+Black&family=Archivo:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');*{margin:0;padding:0;box-sizing:border-box}::selection{background:${G};color:#fff}input,select{font:15px ${f.b};padding:13px 15px;background:transparent;border:1.5px solid ${DV};color:${FG};width:100%;transition:border .15s;border-radius:0;-webkit-appearance:none}input::placeholder{color:${FM}}input:focus,select:focus{outline:none;border-color:${G}}`}</style>

      <div style={{opacity:fade?1:0,transition:"opacity .15s"}}>

      {/* ═══════ MANIFESTO ═══════ */}
      {pg==="manifesto"&&<div>
        <TopNav/>

        {/* Hero */}
        <div style={{padding:"32px 22px 28px",position:"relative",overflow:"hidden"}}>
          <div style={{position:"absolute",top:-120,right:-80,width:320,height:320,borderRadius:"50%",border:`1px solid ${DV}`,opacity:.4,pointerEvents:"none"}}/>
          <div style={{fontFamily:f.m,fontSize:9,letterSpacing:3,color:FM,textTransform:"uppercase",marginBottom:28}}>Manifesto pela soberania industrial</div>
          <div style={{position:"relative",marginBottom:4}}>
            <span style={{fontFamily:f.d,fontSize:80,lineHeight:.85,letterSpacing:-3}}>ZIL</span>
            <div style={{position:"absolute",bottom:5,left:100,width:56,height:4,background:Y,transform:"skewX(-12deg)"}}/>
            <div style={{position:"absolute",bottom:5,left:162,width:22,height:4,background:G,transform:"skewX(-12deg)"}}/>
          </div>
          <p style={{fontFamily:f.b,fontWeight:600,fontSize:12,letterSpacing:4,color:FS,marginTop:18,textTransform:"uppercase"}}>Zero Dependência — Indústria Nacional — Liderança Soberana</p>
          <p style={{fontSize:16,lineHeight:1.6,color:FS,marginTop:28,maxWidth:380,borderLeft:`3px solid ${G}`,paddingLeft:16}}>
            Um país que venceu a hiperinflação, inventou o PIX, transformou cerrado em celeiro do mundo e construiu a Embraer pode fazer qualquer coisa — se conseguir convergir.
          </p>
          <div style={{display:"flex",flexWrap:"wrap",gap:24,marginTop:32}}>
            {[["94%","nióbio mundial",G],["87%","fertilizantes importados",Y],["83%","eletricidade renovável",G],["177mi","brasileiros no PIX",Y]].map(([v,l,c],i)=>(
              <div key={i}><div style={{fontFamily:f.d,fontSize:22,color:c}}>{v}</div><div style={{fontFamily:f.m,fontSize:8,color:FM,letterSpacing:1,marginTop:2}}>{l}</div></div>
            ))}
          </div>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* CTA bar — Ranking */}
        <div style={{padding:"20px 22px",display:"flex",gap:8}}>
          <Btn primary onClick={()=>go("ranking")} style={{flex:1,fontSize:10}}>Ver ranking</Btn>
          <Btn onClick={()=>go(logged?"dashboard":"register")} style={{flex:1,fontSize:10}}>{logged?"Meu painel":"Criar conta"}</Btn>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 01 — Conquistas */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:10}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>01</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1,lineHeight:1.2}}>Já fizemos antes.</h2>
          </div>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:20,maxWidth:400}}>Toda vez que disseram que não conseguiríamos, provamos o contrário. Cada conquista nasceu da recusa coletiva de aceitar dependência.</p>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:6}}>
            {CONQUISTAS.map(([y,t,d],i)=>(
              <div key={i} style={{padding:"12px 14px",borderLeft:`2px solid ${DV}`,transition:"all .2s"}} onMouseEnter={e=>e.currentTarget.style.background=CB} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
                <div style={{fontFamily:f.d,fontSize:10,color:Y,letterSpacing:2}}>{y}</div>
                <div style={{fontFamily:f.b,fontWeight:700,fontSize:12,color:FG,marginTop:2}}>{t}</div>
                <p style={{fontSize:11,lineHeight:1.45,color:FM,marginTop:2}}>{d}</p>
              </div>
            ))}
          </div>
          <div style={{marginTop:16,padding:"14px 16px",background:CB,borderLeft:`3px solid ${Y}`}}>
            <p style={{fontSize:12,lineHeight:1.6,color:FS}}><strong style={{color:FG}}>Nenhuma dessas conquistas nasceu de um lado só do espectro político. Nasceu de convergência.</strong></p>
          </div>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 02 — Por que paramos */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:10}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>02</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>Por que paramos?</h2>
          </div>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:10}}>O mesmo país que criou o PIX — US$4,6 trilhões processados em 2024 — importa 87% dos fertilizantes. Exporta petróleo e importa gasolina.</p>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:10}}>Em três décadas, desmontamos capacidade que levou gerações para construir. A Petrobras fechou fábricas de fertilizantes. A Vale foi privatizada por fração do valor. A estatal de chips, liquidada.</p>
          <p style={{fontSize:13,lineHeight:1.7,color:G,fontWeight:600}}>O problema não é capacidade. É outro.</p>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 03 — Problema de coordenação */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:10}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>03</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1,lineHeight:1.2}}>Não conseguimos convergir.</h2>
          </div>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:10}}>O Brasil não tem déficit de planos. Tem déficit de continuidade. Cada governo desfaz o que o anterior construiu. E o que alimenta esse ciclo?</p>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:10}}>Redes sociais maximizam engajamento. Engajamento é maximizado por indignação. Indignação gera polarização. Polarização impede convergência. Sem convergência, não existe projeto de longo prazo.</p>
          <p style={{fontSize:13,lineHeight:1.7,color:G,fontWeight:600}}>A saída é uma infraestrutura diferente — desenhada para convergência, não para polarização.</p>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 04 — O que é */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:10}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>04</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>O ZIL é tecnologia para consenso.</h2>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:14,marginTop:14,marginBottom:18}}>
            <div>
              <div style={{fontFamily:f.b,fontWeight:700,fontSize:10,letterSpacing:2,color:G,marginBottom:6,textTransform:"uppercase"}}>O que é</div>
              {["Tecnologia para consenso","Bússola de longo prazo","Dados verificáveis","Apartidário por design","Código aberto","Espaço de clareza"].map((t,i)=><div key={i} style={{fontSize:11,color:FS,marginBottom:4,display:"flex",gap:4,alignItems:"baseline"}}><span style={{color:G,fontSize:5}}>●</span>{t}</div>)}
            </div>
            <div>
              <div style={{fontFamily:f.b,fontWeight:700,fontSize:10,letterSpacing:2,color:FM,marginBottom:6,textTransform:"uppercase"}}>O que não é</div>
              {["Partido ou movimento","Veículo de candidaturas","Órgão de denúncia","Rede social de opinião","Ferramenta de um lado","Mais ruído"].map((t,i)=><div key={i} style={{fontSize:11,color:FM,marginBottom:4,display:"flex",gap:4,alignItems:"baseline"}}><span style={{color:FM,fontSize:5}}>○</span>{t}</div>)}
            </div>
          </div>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 05 — Princípios */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:14}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>05</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>Princípios de design</h2>
          </div>
          {PRINC.map(([t,d],i)=>(
            <div key={i} style={{paddingLeft:14,borderLeft:`2px solid ${G}`,marginBottom:16,transition:"padding .15s"}} onMouseEnter={e=>e.currentTarget.style.paddingLeft="18px"} onMouseLeave={e=>e.currentTarget.style.paddingLeft="14px"}>
              <div style={{fontFamily:f.b,fontWeight:700,fontSize:11,letterSpacing:2,color:GD,textTransform:"uppercase",marginBottom:3}}>{t}</div>
              <p style={{fontSize:12,lineHeight:1.6,color:FS,maxWidth:400}}>{d}</p>
            </div>
          ))}
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 06 — Mecanismos */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:14}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>06</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>Como funciona</h2>
          </div>
          {MECS.map(([t,d],i)=>(
            <div key={i} style={{padding:"14px 16px",borderLeft:`2px solid ${DV}`,borderBottom:i<MECS.length-1?`1px solid ${DV}`:"none",transition:"all .2s"}} onMouseEnter={e=>{e.currentTarget.style.borderLeftColor=G;e.currentTarget.style.background=CB}} onMouseLeave={e=>{e.currentTarget.style.borderLeftColor=DV;e.currentTarget.style.background="transparent"}}>
              <div style={{fontFamily:f.b,fontWeight:700,fontSize:13,color:FG,marginBottom:4}}>{t}</div>
              <p style={{fontSize:11,lineHeight:1.6,color:FS,maxWidth:420}}>{d}</p>
            </div>
          ))}
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 07 — Bússola */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:10}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>07</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>A bússola</h2>
          </div>
          <p style={{fontSize:13,lineHeight:1.7,color:FS,marginBottom:14}}>Perguntas estratégicas com métricas verificáveis. A bússola não muda com o ciclo de notícias.</p>
          {PERGS.map((p,i)=>(
            <div key={i} style={{padding:"10px 0 10px 14px",borderLeft:`2px solid ${Y}`,borderBottom:i<PERGS.length-1?`1px solid ${DV}`:"none"}}>
              <p style={{fontSize:12,fontWeight:500,color:FG}}>{p}</p>
            </div>
          ))}
          <div style={{marginTop:14,padding:"12px 16px",background:CB,borderLeft:`3px solid ${G}`}}>
            <p style={{fontSize:11,lineHeight:1.6,color:FS}}><strong style={{color:FG}}>Clareza onde antes havia só ruído.</strong> Marcos com métricas, fontes oficiais e prazos. Quando um governo muda, os marcos permanecem.</p>
          </div>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 08 — Público + Closing */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:14}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>08</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>Para quem é o ZIL</h2>
          </div>
          {["A quem quer sinal no meio do ruído","A quem discorda sobre política mas concorda sobre soberania","A quem cansou de promessa sem medição","A quem sabe que o Brasil pode mais — e quer a prova","Ao político que quer ser cobrado por resultados","A quem acredita que tecnologia pode servir à democracia"].map((p,i)=>(
            <div key={i} style={{fontSize:13,color:FS,marginBottom:5,display:"flex",gap:6,alignItems:"baseline",transition:"all .2s"}} onMouseEnter={e=>{e.currentTarget.style.color=G;e.currentTarget.style.paddingLeft="6px"}} onMouseLeave={e=>{e.currentTarget.style.color=FS;e.currentTarget.style.paddingLeft="0"}}>
              <span style={{color:Y,fontSize:7,flexShrink:0,marginTop:3}}>◆</span>{p}
            </div>
          ))}
          <div style={{marginTop:20,padding:"18px 20px",background:GD,color:BG}}>
            <p style={{fontFamily:f.d,fontSize:14,lineHeight:1.4,textTransform:"uppercase",letterSpacing:1}}>O Brasil não precisa de mais opinião. Precisa de mais convergência. O ZIL é a infraestrutura para isso.</p>
          </div>
        </div>

        <div style={{height:1,background:DV,margin:"0 22px"}}/>

        {/* 09 — Assinar */}
        <div style={{padding:"28px 22px"}}>
          <div style={{display:"flex",gap:14,alignItems:"baseline",marginBottom:14}}>
            <span style={{fontFamily:f.d,fontSize:40,color:DV}}>09</span>
            <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1}}>Assinar</h2>
          </div>
          {!signed?<div style={{maxWidth:360}}>
            <p style={{fontSize:12,color:FS,lineHeight:1.6,marginBottom:18}}>Sua assinatura não é um voto em partido. É um compromisso com o método: convergência por dados, transparência radical, e a recusa de aceitar que polarização é destino.</p>
            <div style={{display:"flex",flexDirection:"column",gap:8,marginBottom:12}}>
              <input placeholder="Nome" value={snm} onChange={e=>setSnm(e.target.value)}/>
              <input placeholder="Cidade, Estado" value={sct} onChange={e=>setSct(e.target.value)}/>
            </div>
            <Btn primary full onClick={()=>{if(snm.trim().length>1){setSigned(true);setCt(c=>c+1)}}}>Assinar o manifesto</Btn>
            <p style={{fontFamily:f.m,fontSize:9,color:FM,marginTop:8,letterSpacing:1}}>{ct.toLocaleString("pt-BR")} assinaturas</p>
          </div>:<div style={{maxWidth:360}}>
            <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:12}}>
              <div style={{width:28,height:28,background:G,color:"#fff",display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:13}}>✓</div>
              <div><div style={{fontWeight:700,fontSize:14}}>{snm}</div><div style={{fontFamily:f.m,fontSize:10,color:FM}}>{sct||"Brasil"} · nº {ct.toLocaleString("pt-BR")}</div></div>
            </div>
            <Btn full onClick={()=>{navigator.clipboard?.writeText(`Assinei o Manifesto ZIL.\n\nO Brasil tem 94% do nióbio mundial e importa 87% dos fertilizantes. O que falta não é capacidade — é convergência.\n\n#ManifestoZIL`).then(()=>{setCp(true);setTimeout(()=>setCp(false),3000)})}}>
              {cp?"✓ Copiado":"Copiar para compartilhar"}
            </Btn>
            {!logged&&<div style={{marginTop:14}}><Btn primary full onClick={()=>go("register")}>Criar conta e participar</Btn></div>}
          </div>}
        </div>

        {/* Footer */}
        <footer style={{background:GD,color:BG,padding:"28px 22px"}}>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:16}}>
            <div><div style={{display:"flex",alignItems:"center",gap:8}}><span style={{fontFamily:f.d,fontSize:20,letterSpacing:2}}>ZIL</span><div style={{width:16,height:3,background:Y}}/></div>
              <p style={{fontSize:10,color:"rgba(240,235,224,.35)",marginTop:8,lineHeight:1.5,maxWidth:260}}>Tecnologia aberta para consenso. Código, dados e processos públicos.</p></div>
            <div style={{textAlign:"right"}}><div style={{fontFamily:f.m,fontSize:8,letterSpacing:2,color:"rgba(240,235,224,.25)"}}>2026 · AGPL-3.0</div><div style={{fontFamily:f.m,fontSize:8,color:"rgba(240,235,224,.2)",marginTop:3}}>#ManifestoZIL</div></div>
          </div>
        </footer>
      </div>}

      {/* ═══════ RANKING ═══════ */}
      {pg==="ranking"&&<div>
        <Nav back="manifesto" title="Ranking"/>
        <div style={{padding:"20px 20px 12px"}}>
          <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1,marginBottom:4}}>Ranking ZIL</h2>
          <p style={{fontSize:12,color:FM,marginBottom:14}}>Score de alinhamento com a soberania industrial, de -10 a +10.</p>
          <input placeholder="Buscar por nome ou partido..." value={q} onChange={e=>setQ(e.target.value)}/>
        </div>
        <div style={{borderTop:`1px solid ${DV}`}}>
          {fdeps.map((d,i)=>(
            <div key={i} onClick={()=>go("profile",d)} style={{display:"flex",alignItems:"center",gap:12,padding:"14px 20px",borderBottom:`1px solid ${DV}`,cursor:"pointer",transition:"background .12s"}}
              onMouseEnter={e=>e.currentTarget.style.background=CB} onMouseLeave={e=>e.currentTarget.style.background="transparent"}>
              <span style={{fontFamily:f.d,fontSize:14,color:DV,width:20,textAlign:"right"}}>{i+1}</span>
              <div style={{width:36,height:36,borderRadius:"50%",background:DV,display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:13,color:FM,flexShrink:0}}>{ini(d.n)}</div>
              <div style={{flex:1,minWidth:0}}>
                <div style={{fontWeight:600,fontSize:13,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{d.n}</div>
                <div style={{fontFamily:f.m,fontSize:10,color:FM}}>{d.p} · {d.u}</div>
              </div>
              <Score s={d.s} sz={34}/>
            </div>
          ))}
        </div>
        <div style={{padding:"20px",textAlign:"center"}}><p style={{fontFamily:f.m,fontSize:10,color:FM}}>{fdeps.length} parlamentares · dados simulados</p></div>
      </div>}

      {/* ═══════ PROFILE ═══════ */}
      {pg==="profile"&&dep&&<div>
        <Nav back="ranking" title="Perfil"/>
        <div style={{padding:"24px 20px"}}>
          <div style={{display:"flex",gap:14,marginBottom:20}}>
            <div style={{width:56,height:56,borderRadius:"50%",background:DV,display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:20,color:FM}}>{ini(dep.n)}</div>
            <div><div style={{fontFamily:f.d,fontSize:16,textTransform:"uppercase",letterSpacing:.5,lineHeight:1.2}}>{dep.n}</div><div style={{fontFamily:f.m,fontSize:10,color:FM,marginTop:3}}>{dep.p} · {dep.u} · Deputado(a)</div></div>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:16,padding:"16px",background:CB,marginBottom:16}}>
            <Score s={dep.s} sz={50}/>
            <div><div style={{fontFamily:f.d,fontSize:12,textTransform:"uppercase",letterSpacing:1}}>Score ZIL</div><div style={{fontSize:11,color:FM,marginTop:3}}>{dep.s>=3?"Alinhado com a soberania":dep.s<=-3?"Contra a soberania":"Posição mista"}</div></div>
          </div>
          <div style={{display:"flex",borderTop:`1px solid ${DV}`,borderBottom:`1px solid ${DV}`,marginBottom:16}}>
            {[[Math.floor(dep.v*.7),"alinhados",G],[Math.floor(dep.v*.3),"contra",OR],[dep.v,"total",FS]].map(([v,l,c],i)=>(
              <div key={i} style={{flex:1,padding:"12px 0",textAlign:"center",borderRight:i<2?`1px solid ${DV}`:"none"}}><div style={{fontFamily:f.d,fontSize:16,color:c}}>{v}</div><div style={{fontFamily:f.m,fontSize:8,color:FM,letterSpacing:1,marginTop:1}}>{l}</div></div>
            ))}
          </div>
          <div style={{fontFamily:f.d,fontSize:11,textTransform:"uppercase",letterSpacing:1,marginBottom:10}}>Votos recentes</div>
          {[{d:"PL 1234 — Processamento local de nióbio",v:"SIM",c:"MIN",ok:true},{d:"PEC 45 — Privatização de refinarias",v:"SIM",c:"ENE",ok:false},{d:"PL 789 — Cadeia de fertilizantes",v:"SIM",c:"FER",ok:true}].map((x,i)=>(
            <div key={i} style={{display:"flex",alignItems:"flex-start",gap:8,padding:"10px 0",borderBottom:`1px solid ${DV}`}}>
              <div style={{width:5,height:5,borderRadius:"50%",background:x.ok?G:OR,marginTop:5,flexShrink:0}}/>
              <div style={{flex:1}}><div style={{fontSize:12,lineHeight:1.4}}>{x.d}</div><span style={{fontFamily:f.m,fontSize:8,padding:"1px 5px",background:GL,color:G,letterSpacing:1}}>{x.c}</span></div>
              <span style={{fontFamily:f.m,fontSize:9,padding:"2px 6px",background:x.ok?GL:"#FEF0EE",color:x.ok?G:OR}}>{x.v}</span>
            </div>
          ))}
          <div style={{marginTop:20,display:"flex",flexDirection:"column",gap:6}}>
            <Btn primary full onClick={()=>go(logged?"dashboard":"register")}>Cobrar esse deputado</Btn>
            <Btn full onClick={()=>go("manifesto")}>Ler o manifesto</Btn>
          </div>
          {!logged&&<p style={{fontFamily:f.m,fontSize:9,color:FM,marginTop:8,textAlign:"center"}}>Crie sua conta para cobrar e receber alertas</p>}
        </div>
      </div>}

      {/* ═══════ REGISTER ═══════ */}
      {pg==="register"&&<div>
        <Nav back="manifesto" title="Criar conta"/>
        <div style={{padding:"28px 20px"}}>
          <h2 style={{fontFamily:f.d,fontSize:18,textTransform:"uppercase",letterSpacing:1,marginBottom:6}}>Participe do ZIL</h2>
          <p style={{fontSize:13,color:FS,lineHeight:1.5,marginBottom:22}}>Cobre deputados, participe de deliberações, receba alertas sobre pautas estratégicas.</p>
          {[["Google","G"],["GitHub","⌘"]].map(([n,ic],i)=>(
            <button key={i} onClick={()=>go("onboarding")} style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"13px",border:`1.5px solid ${DV}`,background:W,cursor:"pointer",fontFamily:f.b,fontSize:13,color:FG,width:"100%",marginBottom:6,transition:"border .12s"}}
              onMouseEnter={e=>e.currentTarget.style.borderColor=G} onMouseLeave={e=>e.currentTarget.style.borderColor=DV}>
              <span style={{fontFamily:f.d,fontSize:15,width:20,textAlign:"center"}}>{ic}</span>Continuar com {n}
            </button>
          ))}
          <div style={{display:"flex",alignItems:"center",gap:10,margin:"16px 0"}}><div style={{flex:1,height:1,background:DV}}/><span style={{fontFamily:f.m,fontSize:9,color:FM,letterSpacing:1}}>OU</span><div style={{flex:1,height:1,background:DV}}/></div>
          <div style={{display:"flex",flexDirection:"column",gap:8,marginBottom:16}}>
            <div><label style={{fontFamily:f.m,fontSize:9,letterSpacing:1,color:FM,display:"block",marginBottom:4}}>NOME</label><input placeholder="Como quer ser chamado(a)" value={nm} onChange={e=>setNm(e.target.value)}/></div>
            <div><label style={{fontFamily:f.m,fontSize:9,letterSpacing:1,color:FM,display:"block",marginBottom:4}}>EMAIL</label><input type="email" placeholder="seu@email.com" value={em} onChange={e=>setEm(e.target.value)}/></div>
            <div><label style={{fontFamily:f.m,fontSize:9,letterSpacing:1,color:FM,display:"block",marginBottom:4}}>ESTADO</label><select value={uf} onChange={e=>setUf(e.target.value)}>{UFS.map(u=><option key={u}>{u}</option>)}</select></div>
          </div>
          <Btn primary full onClick={()=>go("onboarding")}>Criar conta</Btn>
          <p style={{fontFamily:f.m,fontSize:9,color:FM,marginTop:10,textAlign:"center",lineHeight:1.5}}>Magic link por email — sem senha.<br/>Ao criar conta, você aceita o código de conduta.</p>
          <div style={{marginTop:20,paddingTop:14,borderTop:`1px solid ${DV}`}}>
            {["Apartidário — não apoiamos partidos","Código aberto — todo dado é verificável","Sem ads, sem tracking, sem venda de dados"].map((t,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:6,marginBottom:4}}><span style={{color:G,fontSize:9}}>✓</span><span style={{fontFamily:f.m,fontSize:9,color:FM}}>{t}</span></div>
            ))}
          </div>
        </div>
      </div>}

      {/* ═══════ ONBOARDING ═══════ */}
      {pg==="onboarding"&&<div>
        <Nav title="Bem-vindo(a)"/>
        <div style={{padding:"24px 20px"}}>
          <div style={{display:"flex",gap:3,marginBottom:24}}>{[1,2,3].map(s=><div key={s} style={{flex:1,height:3,background:s<=2?G:DV}}/>)}</div>
          <h2 style={{fontFamily:f.d,fontSize:16,textTransform:"uppercase",letterSpacing:1,marginBottom:4}}>Seus deputados</h2>
          <p style={{fontSize:12,color:FM,marginBottom:12}}>Baseado no seu estado ({uf}):</p>
          <div style={{border:`1px solid ${DV}`,marginBottom:20}}>
            {DEPS.slice(0,4).map((d,i)=>(
              <div key={i} style={{display:"flex",alignItems:"center",gap:8,padding:"10px 12px",borderBottom:i<3?`1px solid ${DV}`:"none"}}>
                <div style={{width:28,height:28,borderRadius:"50%",background:DV,display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:10,color:FM,flexShrink:0}}>{ini(d.n)}</div>
                <div style={{flex:1,minWidth:0}}><div style={{fontSize:12,fontWeight:600,whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{d.n}</div><div style={{fontFamily:f.m,fontSize:9,color:FM}}>{d.p}</div></div>
                <Score s={d.s} sz={28}/>
                <button style={{fontFamily:f.m,fontSize:8,letterSpacing:1,padding:"4px 8px",border:`1px solid ${G}`,background:"transparent",color:G,cursor:"pointer",flexShrink:0}}>SEGUIR</button>
              </div>
            ))}
          </div>
          <h2 style={{fontFamily:f.d,fontSize:13,textTransform:"uppercase",letterSpacing:1,marginBottom:4}}>Pautas de interesse</h2>
          <p style={{fontSize:11,color:FM,marginBottom:10}}>Selecione para receber alertas:</p>
          <div style={{display:"flex",flexWrap:"wrap",gap:5,marginBottom:20}}>
            {PAUTAS.map(([c,l,e])=>{
              const sel=pautas.has(c);
              return <button key={c} onClick={()=>tp(c)} style={{display:"flex",alignItems:"center",gap:4,padding:"6px 10px",border:`1.5px solid ${sel?G:DV}`,background:sel?GL:"transparent",color:sel?G:FS,cursor:"pointer",fontFamily:f.b,fontSize:11,transition:"all .12s"}}><span style={{fontSize:12}}>{e}</span>{l}</button>;
            })}
          </div>
          <div style={{padding:"14px",background:CB,borderLeft:`2px solid ${Y}`,marginBottom:18}}>
            <div style={{fontFamily:f.d,fontSize:10,textTransform:"uppercase",letterSpacing:1,marginBottom:4}}>Assinar o manifesto</div>
            <p style={{fontSize:11,color:FS,lineHeight:1.5}}>Compromisso com o método: convergência por dados, transparência radical.</p>
            <div style={{display:"flex",alignItems:"center",gap:6,marginTop:6}}><div style={{width:5,height:5,background:Y,borderRadius:"50%"}}/><span style={{fontFamily:f.m,fontSize:9,color:FM}}>{ct.toLocaleString("pt-BR")} assinaturas</span></div>
          </div>
          <Btn primary full onClick={()=>{setLogged(true);go("dashboard")}}>Começar</Btn>
          <button onClick={()=>{setLogged(true);go("dashboard")}} style={{display:"block",margin:"8px auto 0",background:"none",border:"none",fontFamily:f.m,fontSize:9,color:FM,cursor:"pointer",letterSpacing:1}}>PULAR</button>
        </div>
      </div>}

      {/* ═══════ DASHBOARD ═══════ */}
      {pg==="dashboard"&&<div>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",padding:"14px 20px",borderBottom:`1px solid ${DV}`,position:"sticky",top:0,background:BG,zIndex:10}}>
          <button onClick={()=>go("manifesto")} style={{background:"none",border:"none",cursor:"pointer",fontFamily:f.d,fontSize:15,letterSpacing:1,color:FG}}>ZIL</button>
          <div style={{display:"flex",alignItems:"center",gap:6}}><span style={{fontFamily:f.m,fontSize:9,color:FM}}>{nm||"Usuário"}</span><div style={{width:24,height:24,borderRadius:"50%",background:G,display:"flex",alignItems:"center",justifyContent:"center",fontFamily:f.d,fontSize:9,color:"#fff"}}>{(nm||"U")[0].toUpperCase()}</div></div>
        </div>
        <div style={{padding:"20px"}}>
          <h2 style={{fontFamily:f.d,fontSize:16,textTransform:"uppercase",letterSpacing:1,marginBottom:2}}>Olá, {nm||"Usuário"}</h2>
          <p style={{fontSize:12,color:FM,marginBottom:18}}>Seu painel de soberania industrial.</p>

          <div style={{fontFamily:f.d,fontSize:11,textTransform:"uppercase",letterSpacing:1,marginBottom:8,display:"flex",alignItems:"center",gap:6}}><div style={{width:5,height:5,background:Y,borderRadius:"50%"}}/>Bússola</div>
          <div style={{border:`1px solid ${DV}`,marginBottom:16}}>
            {[["Fertilizantes < 70%",42,"avançando"],["Minerais estratégicos",18,"estagnado"],["Fundo soberano",5,"estagnado"]].map(([t,p,s],i)=>(
              <div key={i} style={{padding:"10px 12px",borderBottom:i<2?`1px solid ${DV}`:"none"}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}><span style={{fontSize:12,fontWeight:600}}>{t}</span><span style={{fontFamily:f.m,fontSize:8,color:s==="avançando"?G:Y,letterSpacing:1}}>{s.toUpperCase()}</span></div>
                <div style={{height:3,background:DV,borderRadius:1}}><div style={{height:3,background:s==="avançando"?G:Y,borderRadius:1,width:`${p}%`}}/></div>
              </div>
            ))}
          </div>

          <div style={{fontFamily:f.d,fontSize:11,textTransform:"uppercase",letterSpacing:1,marginBottom:8,display:"flex",justifyContent:"space-between"}}><span>Alertas</span><span style={{fontFamily:f.m,fontSize:9,color:G,fontWeight:400}}>3 novos</span></div>
          <div style={{border:`1px solid ${DV}`,marginBottom:16}}>
            {[["PL 1234 avançou para plenário","MIN","há 2h"],["Votação sobre fertilizantes amanhã","FER","há 5h"],["Score do Dep. Rocha: -3.1 → -3.8","","há 1d"]].map(([t,c,tm],i)=>(
              <div key={i} style={{display:"flex",alignItems:"flex-start",gap:8,padding:"10px 12px",borderBottom:i<2?`1px solid ${DV}`:"none"}}>
                <div style={{width:5,height:5,borderRadius:"50%",background:G,marginTop:4,flexShrink:0}}/>
                <div style={{flex:1}}><div style={{fontSize:12,lineHeight:1.35}}>{t}</div><div style={{display:"flex",gap:4,marginTop:2}}>{c&&<span style={{fontFamily:f.m,fontSize:8,padding:"1px 4px",background:GL,color:G,letterSpacing:1}}>{c}</span>}<span style={{fontFamily:f.m,fontSize:8,color:FM}}>{tm}</span></div></div>
              </div>
            ))}
          </div>

          <div style={{fontFamily:f.d,fontSize:11,textTransform:"uppercase",letterSpacing:1,marginBottom:8}}>Deliberação ativa</div>
          <div style={{padding:"14px",background:CB,border:`1px solid ${DV}`,marginBottom:16}}>
            <div style={{fontWeight:700,fontSize:13,marginBottom:4}}>O Brasil deve exigir processamento local de minerais estratégicos?</div>
            <div style={{display:"flex",gap:10,marginBottom:8}}><span style={{fontFamily:f.m,fontSize:8,color:FM}}>327 participantes</span><span style={{fontFamily:f.m,fontSize:8,color:FM}}>42 declarações</span><span style={{fontFamily:f.m,fontSize:8,color:G}}>7 dias</span></div>
            <Btn primary full style={{fontSize:9,padding:"9px"}}>Participar</Btn>
          </div>

          <div style={{display:"flex",gap:6}}>
            {[["Ranking","📊","ranking"],["Proposições","📜","ranking"],["Manifesto","📃","manifesto"]].map(([l,e,pg2],i)=>(
              <button key={i} onClick={()=>go(pg2)} style={{flex:1,padding:"12px 6px",border:`1px solid ${DV}`,background:"transparent",cursor:"pointer",display:"flex",flexDirection:"column",alignItems:"center",gap:3,transition:"border .12s"}}
                onMouseEnter={e=>e.currentTarget.style.borderColor=G} onMouseLeave={e=>e.currentTarget.style.borderColor=DV}>
                <span style={{fontSize:16}}>{e}</span><span style={{fontFamily:f.m,fontSize:8,color:FM,letterSpacing:1}}>{l}</span>
              </button>
            ))}
          </div>
        </div>
      </div>}

      </div>
    </div>
  );
}
