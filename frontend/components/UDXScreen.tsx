import Link from "next/link";
import type { ScreenDefinition } from "../lib/screens";

const rows = [
  ["TXN-928401", "Pix", "R$ 1.250,00", "Concluído"],
  ["TXN-928397", "Link", "R$ 420,90", "Pendente"],
  ["TXN-928392", "Pix", "R$ 8.990,00", "Concluído"],
  ["TXN-928381", "Cartão", "R$ 199,90", "Em análise"],
];

function Stat({ label, value, hint }: { label: string; value: string; hint: string }) {
  return <div className="stat"><span>{label}</span><strong>{value}</strong><small>{hint}</small></div>;
}

function Table() {
  return (
    <div className="table">
      <div className="tr th"><span>ID</span><span>Método</span><span>Valor</span><span>Status</span></div>
      {rows.map((row) => <div className="tr" key={row[0]}>{row.map((cell) => <span key={cell}>{cell}</span>)}</div>)}
    </div>
  );
}

function Auth() {
  return <div className="auth-card">
    <div className="brand-mark">UDX</div>
    <h2>Acesso seguro</h2>
    <p>Entre para continuar na plataforma empresarial.</p>
    <label>E-mail<input placeholder="usuario@empresa.com.br" /></label>
    <label>Senha<input type="password" placeholder="••••••••••••" /></label>
    <button className="primary">Continuar</button>
    <div className="security-note">MFA, sessão protegida e trilha de auditoria habilitados.</div>
  </div>;
}

function Form({ screen }: { screen: ScreenDefinition }) {
  return <div className="panel form-panel">
    <div className="progress"><i /><i /><i /><i /></div>
    <div className="field-grid">
      <label>Identificação<input placeholder={screen.name} /></label>
      <label>Documento / referência<input placeholder="Informe os dados" /></label>
      <label className="wide">Descrição<textarea placeholder="Dados complementares e observações" /></label>
      <label>Status<select defaultValue="active"><option value="active">Ativo</option><option>Pendente</option></select></label>
      <label>Responsável<input placeholder="Equipe UDX / usuário" /></label>
    </div>
    <div className="form-actions"><button>Salvar rascunho</button><button className="primary">{screen.primaryAction}</button></div>
  </div>;
}

function Dashboard() {
  return <>
    <div className="stats-grid"><Stat label="Saldo disponível" value="R$ 148.290,40" hint="+12,8% no período" /><Stat label="TPV hoje" value="R$ 84.712,10" hint="428 transações" /><Stat label="Aprovação" value="98,4%" hint="+0,7 p.p." /><Stat label="Recebíveis" value="R$ 61.430,00" hint="próx. 7 dias" /></div>
    <div className="grid-2"><div className="panel"><h3>Volume processado</h3><div className="bars">{[42,66,58,78,62,91,74,88,64,82,95,72].map((h,i)=><i key={i} style={{height:`${h}%`}} />)}</div></div><div className="panel"><h3>Status operacional</h3><div className="status-line"><b className="dot ok" />API operacional</div><div className="status-line"><b className="dot ok" />Ledger sincronizado</div><div className="status-line"><b className="dot warn" />2 itens em conciliação</div></div></div>
    <div className="panel"><h3>Atividade recente</h3><Table /></div>
  </>;
}

function List() {
  return <div className="panel">
    <div className="toolbar"><div className="fake-search">Pesquisar por ID, nome ou documento</div><button>Filtros</button><button className="primary">Nova ação</button></div>
    <Table />
    <div className="pagination">1–4 de 248 registros <span>‹ &nbsp; 1 &nbsp; 2 &nbsp; 3 &nbsp; ›</span></div>
  </div>;
}

function Detail() {
  return <div className="grid-detail">
    <div className="panel">
      <div className="detail-hero"><div><span className="eyebrow">IDENTIFICADOR</span><h2>UDX-928401</h2></div><span className="status success">Concluído</span></div>
      <div className="kv"><span>Empresa<strong>GCNB LTDA</strong></span><span>Filial<strong>Matriz</strong></span><span>Valor<strong>R$ 1.250,00</strong></span><span>Criado em<strong>24/09/2026 · 10:32</strong></span></div>
      <h3>Linha do tempo</h3>
      <div className="timeline"><div>Solicitação criada<small>10:32:04</small></div><div>Processamento autorizado<small>10:32:05</small></div><div>Evento conciliado<small>10:32:07</small></div></div>
    </div>
    <aside className="panel side"><h3>Ações</h3><button className="primary">Ação principal</button><button>Exportar evidência</button><button>Ver auditoria</button></aside>
  </div>;
}

function Payment({ screen }: { screen: ScreenDefinition }) {
  return <div className="payment-grid">
    <div className="panel amount-card"><span>VALOR DA OPERAÇÃO</span><strong>R$ 0,00</strong><div className="keypad">{["1","2","3","4","5","6","7","8","9",",","0","⌫"].map(k=><button key={k}>{k}</button>)}</div><button className="primary full">{screen.primaryAction}</button></div>
    <div className="panel payment-side"><h3>Resumo</h3><div className="summary-row"><span>Conta</span><strong>Conta principal</strong></div><div className="summary-row"><span>Método</span><strong>{screen.domain}</strong></div><div className="summary-row"><span>Tarifa estimada</span><strong>R$ 0,00</strong></div><div className="qr-placeholder">UDX<br/>QR / NFC</div><small>Ambiente de interface. Operações financeiras dependem do provider homologado.</small></div>
  </div>;
}

function Receipt({ screen }: { screen: ScreenDefinition }) {
  return <div className="receipt"><div className="check">✓</div><span className="status success">Operação confirmada</span><h2>R$ 1.250,00</h2><p>{screen.name}</p><div className="receipt-lines"><span>ID<strong>TXN-928401</strong></span><span>Data<strong>24/09/2026 10:32</strong></span><span>Método<strong>UDX Pay</strong></span><span>Status<strong>Concluído</strong></span></div><button className="primary">{screen.primaryAction}</button><button>Baixar PDF</button></div>;
}

function Finance() {
  return <>
    <div className="stats-grid"><Stat label="Disponível" value="R$ 148.290,40" hint="saldo contábil" /><Stat label="Bloqueado" value="R$ 2.480,00" hint="em análise" /><Stat label="A liquidar" value="R$ 61.430,00" hint="D+1 / D+2" /><Stat label="Conciliação" value="99,92%" hint="últimas 24h" /></div>
    <div className="panel"><div className="toolbar"><h3>Movimentações financeiras</h3><button>Exportar CSV</button></div><Table /></div>
  </>;
}

function Report() {
  return <>
    <div className="panel report-filters"><div><span>Período</span><strong>01/09/2026 — 24/09/2026</strong></div><div><span>Filial</span><strong>Todas</strong></div><div><span>Método</span><strong>Todos</strong></div><button className="primary">Atualizar</button></div>
    <div className="grid-2"><div className="panel"><h3>Evolução</h3><div className="line-chart"><svg viewBox="0 0 600 180" role="img" aria-label="Gráfico de evolução"><polyline points="0,150 65,120 120,130 180,85 240,95 300,55 360,75 420,38 480,65 540,22 600,40" fill="none" stroke="currentColor" strokeWidth="4"/></svg></div></div><div className="panel"><h3>Distribuição</h3><div className="donut" /></div></div>
    <div className="panel"><Table /></div>
  </>;
}

function Backoffice() {
  return <>
    <div className="stats-grid"><Stat label="Fila operacional" value="37" hint="12 prioritários" /><Stat label="KYB pendente" value="18" hint="SLA médio 21 min" /><Stat label="Alertas" value="7" hint="2 alta severidade" /><Stat label="Conciliação" value="4" hint="itens divergentes" /></div>
    <div className="grid-2"><div className="panel"><h3>Fila prioritária</h3><Table /></div><div className="panel"><h3>Decisão operacional</h3><textarea placeholder="Registre a análise e evidências" /><div className="decision-buttons"><button>Solicitar dados</button><button className="danger">Bloquear</button><button className="primary">Aprovar</button></div></div></div>
  </>;
}

function Settings() {
  return <div className="settings-grid"><nav className="panel settings-nav">{["Geral","Segurança","Permissões","Integrações","Notificações","Auditoria"].map((x,i)=><span className={i===0?"active":""} key={x}>{x}</span>)}</nav><div className="panel form-panel"><h3>Configuração</h3><label>Nome da configuração<input defaultValue="UDX Payments" /></label><label>Ambiente<select defaultValue="sandbox"><option value="sandbox">Sandbox</option><option>Produção</option></select></label><label className="toggle-line"><span>Exigir MFA</span><input type="checkbox" defaultChecked /></label><label className="toggle-line"><span>Notificar eventos críticos</span><input type="checkbox" defaultChecked /></label><div className="form-actions"><button>Cancelar</button><button className="primary">Salvar alterações</button></div></div></div>;
}

function Pos() {
  return <div className="pos-grid"><div className="panel products"><div className="toolbar"><div className="fake-search">Buscar produto ou código</div><button>Escanear</button></div><div className="product-grid">{["Café","Água","Snack","Combo","Serviço","Produto A","Produto B","Produto C"].map((p,i)=><button className="product" key={p}><b>{p}</b><span>R$ {(12+i*4).toFixed(2)}</span></button>)}</div></div><aside className="panel cart"><h3>Venda atual</h3>{["Produto A × 2","Serviço × 1","Produto B × 1"].map(x=><div className="cart-row" key={x}><span>{x}</span><strong>R$ 24,00</strong></div>)}<div className="cart-total"><span>Total</span><strong>R$ 72,00</strong></div><button className="primary full">Continuar pagamento</button></aside></div>;
}

function Catalog() {
  return <><div className="toolbar panel"><div className="fake-search">Produto, SKU ou categoria</div><button>Importar</button><button className="primary">Novo produto</button></div><div className="catalog-grid">{Array.from({length:8},(_,i)=><div className="product-card" key={i}><div className="product-thumb">UDX</div><span className="status success">Ativo</span><h3>Produto {String(i+1).padStart(2,"0")}</h3><p>SKU UDX-{1000+i}</p><strong>R$ {(49+i*17).toFixed(2)}</strong></div>)}</div></>;
}

function Risk() {
  return <><div className="risk-banner"><span>RISCO MODERADO</span><strong>Score 64 / 100</strong><p>Evento requer revisão humana antes de qualquer ação irreversível.</p></div><div className="grid-2"><div className="panel"><h3>Sinais observados</h3>{["Frequência acima do padrão","Novo dispositivo","Valor fora da média","Geolocalização consistente"].map((x,i)=><div className="signal" key={x}><b className={i<2?"dot warn":"dot ok"} />{x}<span>{i<2?"Revisar":"OK"}</span></div>)}</div><div className="panel"><h3>Decisão</h3><textarea placeholder="Justificativa obrigatória" /><div className="decision-buttons"><button>Liberar</button><button className="danger">Bloquear</button><button className="primary">Solicitar revisão</button></div></div></div>;
}

function Pattern({ screen }: { screen: ScreenDefinition }) {
  switch (screen.pattern) {
    case "auth": return <Auth />;
    case "form": return <Form screen={screen} />;
    case "dashboard": return <Dashboard />;
    case "list": return <List />;
    case "detail": return <Detail />;
    case "payment": return <Payment screen={screen} />;
    case "receipt": return <Receipt screen={screen} />;
    case "finance": return <Finance />;
    case "report": return <Report />;
    case "backoffice": return <Backoffice />;
    case "settings": return <Settings />;
    case "pos": return <Pos />;
    case "catalog": return <Catalog />;
    case "risk": return <Risk />;
  }
}

export function UDXScreen({ screen, previous, next }: { screen: ScreenDefinition; previous?: ScreenDefinition; next?: ScreenDefinition }) {
  return <main className="screen-page">
    <header className="topbar"><Link href="/" className="logo">UDX<span>PAY</span></Link><div className="top-meta"><span>{screen.id}</span><span className={`phase ${screen.phase.toLowerCase()}`}>{screen.phase}</span></div></header>
    <div className="workspace">
      <aside className="sidebar"><Link href="/screens">← 114 telas</Link><div className="side-block"><span>DOMÍNIO</span><strong>{screen.domain}</strong></div><div className="side-block"><span>CANAIS</span><div className="chips">{screen.channels.map(c=><b key={c}>{c}</b>)}</div></div><div className="side-block"><span>PADRÃO</span><strong>{screen.pattern}</strong></div></aside>
      <section className="content">
        <div className="screen-title"><div><span className="eyebrow">{screen.id} · {screen.phase}</span><h1>{screen.name}</h1><p>{screen.summary}</p></div><button className="primary">{screen.primaryAction}</button></div>
        <div className={`prototype ${screen.channels.includes("mobile") && screen.channels.length===1 ? "mobile-only" : ""}`}><Pattern screen={screen} /></div>
        <footer className="screen-nav">{previous ? <Link href={`/screens/${previous.slug}`}>← {previous.id}</Link> : <span/>}<Link href="/screens">Mapa de telas</Link>{next ? <Link href={`/screens/${next.slug}`}>{next.id} →</Link> : <span/>}</footer>
      </section>
    </div>
  </main>;
}
