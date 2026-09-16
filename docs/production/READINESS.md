# UDX Payments — Production Readiness

## Implementado

- PostgreSQL + Alembic
- IAM/RBAC, JWT, MFA e recovery codes
- rate limiting e lockout progressivo
- auditoria imutável para eventos críticos
- ledger de dupla entrada com proteção contra mutação
- bloqueio de saída Pix sem saldo de customer funds
- cobrança Pix abstrata por provider
- webhook HMAC com janela anti-replay
- idempotência de eventos de provider
- reconciliação automática de valor recebido x transação
- liveness, readiness e financial readiness
- request correlation ID e log HTTP estruturado
- container backend sem `--reload` e executando como usuário não-root
- migration separada do processo de aplicação
- CI com Ruff, testes, Bandit, pip-audit bloqueante, npm audit e build de containers
- pipeline de release para imagens GHCR

## Bloqueadores externos para movimentação real

1. Selecionar e contratar PSP/banco participante do Pix.
2. Implementar adapter específico do provider e seus endpoints/certificados.
3. Receber credenciais de produção, mTLS/certificados quando exigidos e segredos de webhook.
4. Homologar criação de cobrança, consulta, devolução, webhook e reconciliação no ambiente do provider.
5. Definir juridicamente se a UDX atua apenas como camada tecnológica, subcredenciador, instituição de pagamento ou outra modalidade aplicável.
6. Concluir KYC/KYB/PLD-FTP e controles antifraude exigidos pelo modelo contratado.
7. Criar política de backup, PITR e restore testado no banco gerenciado escolhido.
8. Definir observabilidade externa (APM, alertas, SIEM) e plantão operacional.
9. Executar pentest independente antes do go-live financeiro.

`PAYMENT_PROVIDER=disabled` é o estado seguro padrão. O endpoint `/health/financial` retorna indisponível enquanto não houver provider configurado.
