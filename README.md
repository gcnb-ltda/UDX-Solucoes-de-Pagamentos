# UDX Soluções de Pagamentos

Plataforma tecnológica da UDX para recebimentos empresariais, gestão de transações, Pix, links de pagamento, conciliação, ledger e integrações.

> Status: estrutura inicial do MVP. Integrações financeiras reais dependem de parceiros homologados, credenciais, contratos e requisitos regulatórios aplicáveis.

## Arquitetura inicial

- Backend: Python + FastAPI
- Banco: PostgreSQL
- Cache/mensageria inicial: Redis
- Frontend Web: Next.js/React
- Mobile: React Native/Expo
- Infraestrutura local: Docker Compose
- CI: GitHub Actions

## Fluxo do MVP

Onboarding/KYB → IAM → Empresas/Filiais → Backoffice → Pix → Transações → Ledger → Saldos/Recebíveis → Conciliação → Links → Relatórios → API/Webhooks → Risco/Compliance.

## Execução local

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`

Documentação OpenAPI: `http://localhost:8000/docs`

Web: `http://localhost:3000`

## Repositório

A branch `main` representa a linha estável. O desenvolvimento é realizado em `develop` e branches de feature.

## Segurança

Nunca faça commit de chaves, certificados, tokens, CSC, credenciais de adquirentes ou segredos de produção. Utilize secret manager/cofre seguro em produção.
