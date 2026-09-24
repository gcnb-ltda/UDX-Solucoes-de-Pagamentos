import Link from "next/link";
import { domains, phaseCounts, screens } from "../../lib/screens";

export default function ScreensPage() {
  return <main className="gallery">
    <header className="gallery-hero">
      <div><span className="home-kicker">UDX INTERFACE MAP</span><h1>Mapa das <span>114 telas</span></h1><p>Cada card abre um protótipo funcional de interface, com padrão visual, canal, domínio e fase de implementação definidos.</p></div>
      <div className="hero-stats"><div className="stat"><span>MVP</span><strong>{phaseCounts.MVP}</strong><small>telas</small></div><div className="stat"><span>Fase 2</span><strong>{phaseCounts.F2}</strong><small>telas</small></div><div className="stat"><span>Fase 3</span><strong>{phaseCounts.F3}</strong><small>telas</small></div><div className="stat"><span>Total</span><strong>{screens.length}</strong><small>rotas</small></div></div>
    </header>
    {domains.map((domain) => {
      const group = screens.filter((screen) => screen.domain === domain);
      return <section className="domain" key={domain}><div className="domain-head"><h2>{domain}</h2><span>{group.length} telas</span></div><div className="screen-grid">{group.map((screen) => <Link href={`/screens/${screen.slug}`} className="screen-card" key={screen.id}><div className="card-top"><span>{screen.id}</span><span>{screen.phase}</span></div><h3>{screen.name}</h3><p>{screen.primaryAction}</p><div className="channels">{screen.channels.join(" · ")}</div></Link>)}</div></section>;
    })}
  </main>;
}
