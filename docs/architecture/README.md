# Arquitetura UDX Soluções de Pagamentos

## Objetivo

Construir uma plataforma modular para recebimentos empresariais, mantendo separação entre produto tecnológico UDX e provedores financeiros regulados/homologados.

## Domínios iniciais

1. Identity & Access
2. Companies & Branches
3. Payments
4. Pix
5. Payment Links
6. Transactions
7. Ledger
8. Balances & Receivables
9. Settlement
10. Reconciliation
11. Risk & Compliance
12. Reporting
13. Webhooks & Integrations
14. Support

## Princípios

- Idempotência em operações financeiras críticas.
- Ledger imutável com lançamentos compensatórios.
- Separação de adapters de parceiros financeiros.
- Nenhum segredo em código-fonte.
- Observabilidade e auditabilidade desde o MVP.
- PostgreSQL como fonte de verdade financeira.
- Redis apenas para cache, locks e processamento assíncrono, nunca como única fonte de saldo.

## Fluxo de pagamento

```text
Cliente -> Canal UDX -> API -> Payments Service -> Risk -> Provider Adapter
                                      |
                                      v
                                  Transaction
                                      |
                                      v
                                    Ledger
                                      |
                                      v
                             Reconciliation/Settlement
```

## Estado atual

O endpoint inicial de pagamento cria apenas uma intenção local de desenvolvimento. Ele não representa Pix ou cartão liquidado. Integrações reais devem ser adicionadas por adapters próprios após homologação.
