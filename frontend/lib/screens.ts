export type Channel = "mobile" | "web" | "backoffice";
export type Phase = "MVP" | "F2" | "F3";
export type Pattern =
  | "auth" | "form" | "dashboard" | "list" | "detail" | "payment"
  | "receipt" | "finance" | "report" | "backoffice" | "settings"
  | "pos" | "catalog" | "risk";

export type ScreenDefinition = {
  id: string;
  slug: string;
  name: string;
  domain: string;
  phase: Phase;
  channels: Channel[];
  pattern: Pattern;
  primaryAction: string;
  summary: string;
};

const summary = (name: string, domain: string) =>
  `${name}: interface UDX para o domínio ${domain}, com hierarquia operacional, estados claros, auditoria e ações consistentes entre canais.`;

const s = (
  n: number,
  name: string,
  domain: string,
  phase: Phase,
  channels: Channel[],
  pattern: Pattern,
  primaryAction: string,
): ScreenDefinition => ({
  id: `TELA-${String(n).padStart(3, "0")}`,
  slug: `tela-${String(n).padStart(3, "0")}`,
  name,
  domain,
  phase,
  channels,
  pattern,
  primaryAction,
  summary: summary(name, domain),
});

export const screens: ScreenDefinition[] = [
  s(1, "Login", "Login, MFA e segurança", "MVP", ["mobile","web"], "auth", "Entrar"),
  s(2, "Desafio MFA", "Login, MFA e segurança", "MVP", ["mobile","web"], "auth", "Validar código"),
  s(3, "Recuperação MFA", "Login, MFA e segurança", "MVP", ["mobile","web"], "auth", "Usar código de recuperação"),
  s(4, "Recuperação de senha", "Login, MFA e segurança", "MVP", ["mobile","web"], "form", "Solicitar recuperação"),
  s(5, "Segurança da conta", "Login, MFA e segurança", "MVP", ["mobile","web"], "settings", "Atualizar segurança"),
  s(6, "Sessões e dispositivos", "Login, MFA e segurança", "MVP", ["web","backoffice"], "list", "Revogar sessão"),
  s(7, "Início do cadastro", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Começar cadastro"),
  s(8, "Dados da empresa", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Salvar e continuar"),
  s(9, "Endereço", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Confirmar endereço"),
  s(10, "Representante legal", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Salvar representante"),
  s(11, "Dados bancários", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Validar conta"),
  s(12, "Documentos KYB", "Onboarding e KYB", "MVP", ["mobile","web"], "form", "Enviar documentos"),
  s(13, "Revisão do cadastro", "Onboarding e KYB", "MVP", ["mobile","web"], "detail", "Enviar para análise"),
  s(14, "Status da análise", "Onboarding e KYB", "MVP", ["mobile","web","backoffice"], "detail", "Ver pendências"),
  s(15, "Dashboard do lojista", "Dashboards", "MVP", ["mobile","web"], "dashboard", "Receber pagamento"),
  s(16, "Dashboard executivo", "Dashboards", "MVP", ["web","backoffice"], "dashboard", "Abrir visão financeira"),
  s(17, "Central de notificações", "Dashboards", "MVP", ["mobile","web"], "list", "Marcar como lida"),
  s(18, "Status operacional", "Dashboards", "MVP", ["web","backoffice"], "dashboard", "Ver incidentes"),
  s(19, "Perfil da empresa", "Empresa, filiais e usuários", "MVP", ["mobile","web","backoffice"], "detail", "Editar empresa"),
  s(20, "Lista de filiais", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "list", "Nova filial"),
  s(21, "Nova filial", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "form", "Criar filial"),
  s(22, "Detalhe da filial", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "detail", "Editar filial"),
  s(23, "Usuários", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "list", "Novo usuário"),
  s(24, "Novo usuário", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "form", "Convidar usuário"),
  s(25, "Permissões do usuário", "Empresa, filiais e usuários", "MVP", ["web","backoffice"], "settings", "Salvar permissões"),
  s(26, "Dispositivos", "Empresa, filiais e usuários", "MVP", ["mobile","web","backoffice"], "list", "Gerenciar dispositivo"),
  s(27, "Menu Receber", "Pix", "MVP", ["mobile","web"], "payment", "Nova cobrança"),
  s(28, "Nova cobrança Pix", "Pix", "MVP", ["mobile","web"], "payment", "Gerar cobrança"),
  s(29, "QR Code Pix", "Pix", "MVP", ["mobile","web"], "payment", "Compartilhar QR Code"),
  s(30, "Pix copia e cola", "Pix", "MVP", ["mobile","web"], "detail", "Copiar código Pix"),
  s(31, "Status da cobrança", "Pix", "MVP", ["mobile","web","backoffice"], "detail", "Atualizar status"),
  s(32, "Detalhe Pix", "Pix", "MVP", ["mobile","web","backoffice"], "detail", "Ver evento"),
  s(33, "Enviar Pix", "Pix", "MVP", ["mobile","web"], "payment", "Continuar envio"),
  s(34, "Confirmação Pix", "Pix", "MVP", ["mobile","web"], "payment", "Confirmar Pix"),
  s(35, "Comprovante Pix", "Pix", "MVP", ["mobile","web"], "receipt", "Compartilhar comprovante"),
  s(36, "Links de pagamento", "Links e QR", "MVP", ["mobile","web"], "list", "Criar link"),
  s(37, "Criar link", "Links e QR", "MVP", ["mobile","web"], "form", "Gerar link"),
  s(38, "Detalhe do link", "Links e QR", "MVP", ["mobile","web"], "detail", "Editar link"),
  s(39, "Compartilhar link", "Links e QR", "MVP", ["mobile","web"], "receipt", "Compartilhar"),
  s(40, "Lista de transações", "Transações e devoluções", "MVP", ["mobile","web","backoffice"], "list", "Abrir transação"),
  s(41, "Filtros de transações", "Transações e devoluções", "MVP", ["mobile","web","backoffice"], "settings", "Aplicar filtros"),
  s(42, "Detalhe da transação", "Transações e devoluções", "MVP", ["mobile","web","backoffice"], "detail", "Ver lançamento"),
  s(43, "Cancelamento", "Transações e devoluções", "MVP", ["web","backoffice"], "form", "Confirmar cancelamento"),
  s(44, "Devolução", "Transações e devoluções", "MVP", ["mobile","web","backoffice"], "form", "Solicitar devolução"),
  s(45, "Comprovante", "Transações e devoluções", "MVP", ["mobile","web"], "receipt", "Compartilhar comprovante"),
  s(46, "Saldo", "Saldo, ledger e recebíveis", "MVP", ["mobile","web","backoffice"], "finance", "Ver extrato"),
  s(47, "Recebíveis", "Saldo, ledger e recebíveis", "MVP", ["mobile","web","backoffice"], "finance", "Ver agenda"),
  s(48, "Agenda de recebíveis", "Saldo, ledger e recebíveis", "MVP", ["web","backoffice"], "report", "Exportar agenda"),
  s(49, "Liquidação", "Saldo, ledger e recebíveis", "MVP", ["web","backoffice"], "finance", "Ver liquidação"),
  s(50, "Razão e Ledger", "Saldo, ledger e recebíveis", "MVP", ["web","backoffice"], "finance", "Auditar lançamento"),
  s(51, "Conciliação", "Conciliação financeira", "MVP", ["web","backoffice"], "finance", "Executar conciliação"),
  s(52, "Divergências", "Conciliação financeira", "MVP", ["web","backoffice"], "list", "Analisar divergência"),
  s(53, "Não conciliados", "Conciliação financeira", "MVP", ["web","backoffice"], "list", "Resolver pendência"),
  s(54, "Detalhe da conciliação", "Conciliação financeira", "MVP", ["web","backoffice"], "detail", "Registrar decisão"),
  s(55, "Central de relatórios", "Relatórios", "MVP", ["mobile","web","backoffice"], "report", "Gerar relatório"),
  s(56, "Relatório diário", "Relatórios", "MVP", ["mobile","web","backoffice"], "report", "Exportar relatório"),
  s(57, "Relatório de tarifas", "Relatórios", "MVP", ["web","backoffice"], "report", "Exportar tarifas"),
  s(58, "Relatório por filial e vendedor", "Relatórios", "MVP", ["web","backoffice"], "report", "Comparar desempenho"),
  s(59, "Exportação de relatórios", "Relatórios", "MVP", ["web","backoffice"], "settings", "Gerar arquivo"),
  s(60, "Dashboard Backoffice", "Backoffice, risco e compliance", "MVP", ["backoffice"], "backoffice", "Abrir fila operacional"),
  s(61, "Fila KYB", "Backoffice, risco e compliance", "MVP", ["backoffice"], "list", "Analisar cadastro"),
  s(62, "Análise KYB", "Backoffice, risco e compliance", "MVP", ["backoffice"], "backoffice", "Registrar decisão"),
  s(63, "Alertas de risco", "Backoffice, risco e compliance", "MVP", ["backoffice"], "risk", "Investigar alerta"),
  s(64, "Detalhe de risco", "Backoffice, risco e compliance", "MVP", ["backoffice"], "risk", "Aplicar decisão"),
  s(65, "Audit Log", "Backoffice, risco e compliance", "MVP", ["backoffice"], "list", "Exportar evidência"),
  s(66, "Eventos do PSP", "Backoffice, risco e compliance", "MVP", ["backoffice"], "list", "Abrir evento"),
  s(67, "Operações financeiras", "Backoffice, risco e compliance", "MVP", ["backoffice"], "finance", "Revisar operação"),
  s(68, "Configurações da empresa", "Configurações e integrações", "MVP", ["mobile","web"], "settings", "Salvar configurações"),
  s(69, "Tarifas e planos", "Configurações e integrações", "MVP", ["web","backoffice"], "settings", "Alterar plano"),
  s(70, "APIs e API Keys", "Configurações e integrações", "MVP", ["web","backoffice"], "settings", "Criar API Key"),
  s(71, "Webhooks e integrações", "Configurações e integrações", "MVP", ["web","backoffice"], "settings", "Adicionar webhook"),
  s(72, "Preferências e notificações", "Configurações e integrações", "MVP", ["mobile","web"], "settings", "Salvar preferências"),
  s(73, "Central de suporte", "Suporte", "MVP", ["mobile","web","backoffice"], "list", "Abrir chamado"),
  s(74, "Visão de cartões", "Cartões", "F2", ["mobile","web","backoffice"], "dashboard", "Nova venda no cartão"),
  s(75, "Nova venda no cartão", "Cartões", "F2", ["mobile","web"], "payment", "Cobrar cartão"),
  s(76, "Parcelamento", "Cartões", "F2", ["mobile","web"], "payment", "Escolher parcelas"),
  s(77, "Autorização do cartão", "Cartões", "F2", ["mobile","web","backoffice"], "detail", "Consultar autorização"),
  s(78, "Comprovante de cartão", "Cartões", "F2", ["mobile","web"], "receipt", "Compartilhar comprovante"),
  s(79, "Devolução no cartão", "Cartões", "F2", ["web","backoffice"], "form", "Solicitar estorno"),
  s(80, "Ativação Tap to Pay", "Tap to Pay", "F2", ["mobile"], "form", "Ativar dispositivo"),
  s(81, "Venda Tap to Pay", "Tap to Pay", "F2", ["mobile"], "payment", "Aproximar cartão"),
  s(82, "Processamento Tap to Pay", "Tap to Pay", "F2", ["mobile"], "payment", "Processar pagamento"),
  s(83, "Terminais e dispositivos", "Tap to Pay", "F2", ["web","backoffice"], "list", "Vincular terminal"),
  s(84, "PDV - Início", "PDV", "F2", ["mobile","web"], "pos", "Iniciar venda"),
  s(85, "PDV - Nova venda", "PDV", "F2", ["mobile","web"], "pos", "Adicionar itens"),
  s(86, "PDV - Carrinho", "PDV", "F2", ["mobile","web"], "pos", "Ir para pagamento"),
  s(87, "PDV - Checkout", "PDV", "F2", ["mobile","web"], "pos", "Finalizar venda"),
  s(88, "PDV - Comprovante", "PDV", "F2", ["mobile","web"], "receipt", "Nova venda"),
  s(89, "Catálogo", "Catálogo e estoque", "F2", ["mobile","web"], "catalog", "Novo produto"),
  s(90, "Novo produto", "Catálogo e estoque", "F2", ["mobile","web"], "catalog", "Cadastrar produto"),
  s(91, "Produto - detalhe e edição", "Catálogo e estoque", "F2", ["mobile","web"], "catalog", "Salvar produto"),
  s(92, "Estoque", "Catálogo e estoque", "F2", ["mobile","web"], "catalog", "Movimentar estoque"),
  s(93, "Movimentação de estoque", "Catálogo e estoque", "F2", ["web"], "form", "Registrar movimentação"),
  s(94, "Clientes", "CRM", "F2", ["mobile","web"], "list", "Novo cliente"),
  s(95, "Detalhe do cliente", "CRM", "F2", ["mobile","web"], "detail", "Editar cliente"),
  s(96, "Vendedores", "Vendedores", "F2", ["web","backoffice"], "list", "Novo vendedor"),
  s(97, "Desempenho do vendedor", "Vendedores", "F2", ["web","backoffice"], "report", "Ver transações"),
  s(98, "Disputas", "Disputas e chargebacks", "F2", ["web","backoffice"], "list", "Abrir disputa"),
  s(99, "Detalhe da disputa", "Disputas e chargebacks", "F2", ["web","backoffice"], "backoffice", "Enviar evidência"),
  s(100, "Chargebacks", "Disputas e chargebacks", "F2", ["web","backoffice"], "risk", "Responder chargeback"),
  s(101, "Pagamentos recorrentes", "Recorrência", "F3", ["web","backoffice"], "list", "Nova recorrência"),
  s(102, "Detalhe da assinatura", "Recorrência", "F3", ["web","backoffice"], "detail", "Gerenciar assinatura"),
  s(103, "Regras de split", "Split", "F3", ["web","backoffice"], "settings", "Criar regra de split"),
  s(104, "Transação com split", "Split", "F3", ["web","backoffice"], "finance", "Ver distribuição"),
  s(105, "Marketplace", "Marketplace", "F3", ["web","backoffice"], "dashboard", "Cadastrar seller"),
  s(106, "Seller do marketplace", "Marketplace", "F3", ["web","backoffice"], "detail", "Gerenciar seller"),
  s(107, "Subcontas", "Subcontas", "F3", ["web","backoffice"], "list", "Criar subconta"),
  s(108, "Conta empresarial", "Conta e banking", "F3", ["mobile","web"], "finance", "Movimentar conta"),
  s(109, "Transferências", "Conta e banking", "F3", ["mobile","web"], "payment", "Nova transferência"),
  s(110, "Contas a pagar", "Conta e banking", "F3", ["mobile","web"], "list", "Pagar conta"),
  s(111, "Cartões empresariais", "Conta e banking", "F3", ["mobile","web"], "dashboard", "Gerenciar cartões"),
  s(112, "White label", "White label", "F3", ["web","backoffice"], "settings", "Publicar identidade"),
  s(113, "Motor de regras antifraude", "Fraude avançada", "F3", ["backoffice"], "risk", "Criar regra"),
  s(114, "Caso de investigação", "Fraude avançada", "F3", ["backoffice"], "risk", "Registrar decisão"),
];

export const screenBySlug = new Map(screens.map((screen) => [screen.slug, screen]));
export const screenById = new Map(screens.map((screen) => [screen.id, screen]));

export const domains = Array.from(new Set(screens.map((screen) => screen.domain)));
export const phaseCounts = {
  MVP: screens.filter((screen) => screen.phase === "MVP").length,
  F2: screens.filter((screen) => screen.phase === "F2").length,
  F3: screens.filter((screen) => screen.phase === "F3").length,
};
