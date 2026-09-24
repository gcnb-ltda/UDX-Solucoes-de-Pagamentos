import Link from "next/link";
import { phaseCounts, screens } from "../lib/screens";

export default function Home() {
  return <main className="home">
    <section className="home-hero">
      <span className="home-kicker">UDX SOLUÇÕES DE PAGAMENTOS · UI SYSTEM</span>
      <h1>114 telas.<br/><span>Um único sistema.</span></h1>
      <p>Arquitetura visual navegável para Mobile, Portal Web do lojista e Backoffice UDX, cobrindo o MVP e as fases 2 e 3 da plataforma.</p>
      <div className="home-actions"><Link href="/screens" className="primary">Explorar todas as telas</Link><a href="https://github.com/gcnb-ltda/UDX-Solucoes-de-Pagamentos">Repositório</a></div>
    </section>
    <section className="home-strip">
      <div><strong>{screens.length}</strong><span>Telas lógicas</span></div>
      <div><strong>{phaseCounts.MVP}</strong><span>MVP operacional</span></div>
      <div><strong>{phaseCounts.F2}</strong><span>Fase 2</span></div>
      <div><strong>{phaseCounts.F3}</strong><span>Fase 3</span></div>
    </section>
  </main>;
}
