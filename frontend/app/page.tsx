export default function Home() {
  return (
    <main style={{minHeight:'100vh',background:'#0a0a0a',color:'#fff',padding:'48px',fontFamily:'Arial, sans-serif'}}>
      <div style={{maxWidth:'960px',margin:'0 auto'}}>
        <p style={{color:'#ffd400',fontWeight:700,letterSpacing:'0.08em'}}>UDX SOLUÇÕES DE PAGAMENTOS</p>
        <h1 style={{fontSize:'56px',lineHeight:1.05,margin:'16px 0'}}>Recebimentos empresariais em uma única plataforma.</h1>
        <p style={{fontSize:'20px',color:'#bdbdbd',maxWidth:'700px'}}>
          Base inicial do painel UDX Pay para Pix, links de pagamento, transações, saldos, recebíveis e conciliação.
        </p>
        <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(200px,1fr))',gap:'16px',marginTop:'40px'}}>
          {['Receber','Transações','Saldo','Recebíveis'].map((item) => (
            <div key={item} style={{border:'1px solid #2a2a2a',borderRadius:'16px',padding:'24px',background:'#111'}}>
              <strong>{item}</strong>
              <p style={{color:'#888'}}>Módulo em desenvolvimento.</p>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
