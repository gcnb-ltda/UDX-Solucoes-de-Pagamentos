const cards = [
  { title: 'Receber', text: 'Pix e cobrança de teste', badge: 'PIX' },
  { title: 'Transações', text: 'Histórico operacional', badge: 'HISTÓRICO' },
  { title: 'Saldo', text: 'Visão financeira de teste', badge: 'LEDGER' },
  { title: 'Conciliação', text: 'Eventos e divergências', badge: 'BACKOFFICE' },
];

export default function Home() {
  return (
    <main className="shell">
      <section className="hero">
        <div className="brandRow">
          <span className="brandMark">UDX</span>
          <span className="environment">v0.1 TEST</span>
        </div>
        <p className="eyebrow">UDX SOLUÇÕES DE PAGAMENTOS</p>
        <h1>Recebimentos empresariais em uma única plataforma.</h1>
        <p className="lead">
          Primeira versão compilável para homologação web e Android. Operações financeiras reais permanecem desabilitadas até integração e homologação com provedor.
        </p>
        <div className="status"><span className="statusDot" /> Ambiente de testes</div>
      </section>

      <section className="grid" aria-label="Módulos principais">
        {cards.map((item) => (
          <article key={item.title} className="card">
            <span className="badge">{item.badge}</span>
            <h2>{item.title}</h2>
            <p>{item.text}</p>
            <button type="button" disabled>Em homologação</button>
          </article>
        ))}
      </section>

      <footer>
        <span>GCNB LTDA · CNPJ 29.718.432/0001-14</span>
        <span>Build 0.1.0-test</span>
      </footer>

      <style>{`
        :global(*){box-sizing:border-box}
        :global(html){background:#080808}
        :global(body){margin:0;background:#080808;color:#fff;font-family:Arial,Helvetica,sans-serif}
        .shell{min-height:100vh;padding:clamp(24px,5vw,64px);background:radial-gradient(circle at 80% 0%,#2b2500 0%,#0a0a0a 32%,#080808 62%);display:flex;flex-direction:column}
        .hero,.grid,footer{width:min(1100px,100%);margin-left:auto;margin-right:auto}
        .brandRow{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:48px}
        .brandMark{font-size:30px;font-weight:900;letter-spacing:-2px;color:#ffd400}
        .environment{border:1px solid #403900;background:#171500;color:#ffe454;padding:8px 12px;border-radius:999px;font-size:11px;font-weight:800;letter-spacing:.08em}
        .eyebrow{color:#ffd400;font-weight:800;letter-spacing:.12em;font-size:12px;margin:0 0 16px}
        h1{font-size:clamp(40px,7vw,78px);line-height:.98;letter-spacing:-.055em;max-width:900px;margin:0 0 24px}
        .lead{font-size:clamp(16px,2vw,20px);line-height:1.6;color:#aaa;max-width:760px;margin:0}
        .status{display:inline-flex;align-items:center;gap:10px;margin-top:28px;color:#d8d8d8;font-size:13px}
        .statusDot{width:8px;height:8px;border-radius:50%;background:#ffd400;box-shadow:0 0 18px #ffd400}
        .grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:56px}
        .card{min-height:210px;border:1px solid #222;border-radius:22px;padding:22px;background:rgba(17,17,17,.88);display:flex;flex-direction:column}
        .badge{font-size:10px;font-weight:800;letter-spacing:.08em;color:#ffd400}
        .card h2{font-size:22px;margin:36px 0 8px}
        .card p{color:#8c8c8c;margin:0;line-height:1.5}
        button{margin-top:auto;width:100%;border:1px solid #292929;background:#151515;color:#666;padding:12px;border-radius:12px;font-weight:700}
        footer{margin-top:auto;padding-top:56px;display:flex;justify-content:space-between;gap:20px;color:#555;font-size:11px}
        @media(max-width:820px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
        @media(max-width:520px){.shell{padding:24px 18px}.brandRow{margin-bottom:36px}.grid{grid-template-columns:1fr;margin-top:42px}.card{min-height:180px}.card h2{margin-top:28px}footer{flex-direction:column;padding-top:42px}h1{font-size:44px}}
      `}</style>
    </main>
  );
}
