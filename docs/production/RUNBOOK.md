# Runbook de Produção

## Deploy

1. CI deve estar verde.
2. Gerar tag de release e imagens imutáveis.
3. Executar backup/snapshot pré-migração.
4. Executar `alembic upgrade head` em job único.
5. Subir backend e validar `/health/ready`.
6. Validar `/health/financial` somente após provider homologado.
7. Subir frontend.
8. Executar smoke tests de login, MFA, cobrança e backoffice.

## Rollback

- Não fazer downgrade destrutivo de banco durante incidente.
- Reverter imagem da aplicação para SHA anterior compatível com o schema.
- Se migration incompatível exigir reversão, usar procedimento aprovado e snapshot validado.

## Incidente financeiro

1. Desabilitar novas submissões no provider sem alterar ledger histórico.
2. Preservar `provider_events`, `audit_logs` e `ledger_entries`.
3. Comparar provider x transactions x reconciliation_records.
4. Não corrigir saldo editando lançamento existente; gerar lançamento compensatório em fluxo aprovado.
5. Registrar causa, impacto, linha do tempo e ação corretiva.

## Chaves e segredos

- Segredos somente em Secret Manager/KMS ou mecanismo equivalente.
- Rotacionar JWT adicionando nova `kid`, torná-la ativa e manter a anterior apenas durante a janela de expiração.
- Nunca remover uma chave antiga antes de expirar todos os tokens emitidos por ela.
- Rotacionar webhook secret em coordenação com o PSP.

## Backup

Produção deve usar PostgreSQL com backup automático, PITR e restore testado. O teste de restore deve ser executado periodicamente em ambiente isolado, com evidência registrada.
