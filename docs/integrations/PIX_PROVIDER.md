# Contrato de integração Pix/PSP

O núcleo UDX não deve assumir acesso direto ao SPI/DICT. O provider concreto deve encapsular o contrato do banco/PSP escolhido.

## Operações mínimas do adapter produtivo

- criar cobrança Pix dinâmica;
- consultar cobrança/status;
- receber e verificar webhook do PSP;
- identificar `txid`, `EndToEndId` e identificador externo;
- solicitar devolução total/parcial quando contratualmente suportado;
- consultar devolução;
- iniciar transferência Pix somente quando o modelo jurídico/contratual permitir;
- aplicar idempotência também no provider;
- mapear códigos de erro para estados internos estáveis;
- suportar mTLS/certificado cliente quando exigido;
- implementar timeout, retry com backoff e circuit breaker;
- nunca registrar certificados, tokens, chaves Pix completas ou segredos em logs.

## Webhook interno de referência

O adapter deve normalizar eventos para o formato:

```json
{
  "id": "provider-event-id",
  "type": "pix.received",
  "data": {
    "provider_charge_id": "charge-id",
    "amount": "100.00",
    "end_to_end_id": "E..."
  }
}
```

A assinatura de referência é HMAC-SHA256 de `timestamp + '.' + raw_body`. Um adapter real pode substituir esta camada pela assinatura nativa do PSP, desde que mantenha autenticação, replay protection e idempotência.
