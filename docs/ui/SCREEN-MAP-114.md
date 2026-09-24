# UDX UI Map — 114 telas

Esta implementação transforma o mapa funcional da UDX em **114 rotas reais de interface** no frontend Next.js.

## Distribuição

- MVP: 73 telas
- Fase 2: 27 telas
- Fase 3: 14 telas
- Total: 114 telas lógicas

## Canais

Cada definição informa os canais aplicáveis: `mobile`, `web` e/ou `backoffice`. As telas são responsivas e compartilham componentes para evitar divergência visual.

## Rotas

- `/` — apresentação do sistema de interface.
- `/screens` — mapa completo das 114 telas.
- `/screens/tela-001` até `/screens/tela-114` — protótipos individuais.

## Design system

Identidade UDX em preto/amarelo, painéis escuros, alta legibilidade, estados semânticos de sucesso/atenção/risco e navegação consistente. O renderer trabalha com padrões reutilizáveis: autenticação, formulário, dashboard, lista, detalhe, pagamento, comprovante, financeiro, relatório, backoffice, configurações, PDV, catálogo e risco.

## Regra de implementação

As telas são protótipos navegáveis e não ativam transações reais. Qualquer operação financeira continua condicionada a provider/PSP homologado, credenciais e controles de produção.
