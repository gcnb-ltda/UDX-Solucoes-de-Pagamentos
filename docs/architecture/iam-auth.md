# IAM, Companies, Branches e Autenticação

## Escopo implementado

Este módulo cria a base multiempresa do MVP da UDX Soluções de Pagamentos.

### Entidades

- `companies`: empresa/tenant principal.
- `branches`: filiais pertencentes a uma empresa.
- `users`: usuários vinculados obrigatoriamente a uma empresa.
- `user_branches`: vínculo N:N entre usuários e filiais autorizadas.
- `refresh_sessions`: sessões de refresh JWT revogáveis e rotacionáveis.

## Perfis RBAC

- `admin`
- `finance`
- `manager`
- `cashier`
- `accounting`

A autorização é validada no backend. O `company_id` do token é comparado ao tenant persistido do usuário e as consultas administrativas sempre filtram o tenant.

## Bootstrap inicial

O primeiro tenant é criado por:

`POST /api/v1/onboarding/bootstrap`

O endpoint exige o header `X-Bootstrap-Token`, cujo valor vem de `BOOTSTRAP_TOKEN`. O bootstrap é recusado depois que o primeiro usuário existe.

O bootstrap cria:

1. empresa;
2. filial principal;
3. primeiro usuário `admin`.

Em produção, `APP_SECRET_KEY` e `BOOTSTRAP_TOKEN` devem ser valores aleatórios fortes mantidos fora do repositório.

## Autenticação

### Login

`POST /api/v1/auth/login`

Sem MFA ativo, retorna `access_token` e `refresh_token`.

Com MFA ativo, retorna um `challenge_token` curto que deve ser concluído em:

`POST /api/v1/auth/mfa/verify`

### Access token

- JWT assinado;
- validade padrão: 15 minutos;
- inclui `sub`, `company_id`, `role`, `iss`, `aud`, `jti`, `iat` e `exp`.

### Refresh token

- validade padrão: 7 dias;
- cada refresh possui `jti` persistido;
- refresh bem-sucedido revoga a sessão anterior e cria uma nova;
- reutilização do token anterior é rejeitada.

### Logout

`POST /api/v1/auth/logout`

Revoga a sessão de refresh informada.

## MFA TOTP

1. usuário autenticado chama `POST /api/v1/auth/mfa/setup`;
2. recebe segredo e provisioning URI para aplicativo autenticador;
3. confirma o código em `POST /api/v1/auth/mfa/confirm`;
4. logins seguintes exigem `POST /api/v1/auth/mfa/verify`.

O segredo TOTP é armazenado criptografado, derivando a chave de criptografia do `APP_SECRET_KEY` no MVP. Uma futura arquitetura de produção pode migrar essa chave para KMS/HSM ou secret manager dedicado.

## Companies e Branches

- `GET /api/v1/companies/me`
- `GET /api/v1/companies/me/branches`
- `POST /api/v1/companies/me/branches`
- `PATCH /api/v1/companies/me/branches/{branch_id}/deactivate`

Criação de filial: `admin` ou `manager`.
Desativação: `admin`.

## Usuários

- `GET /api/v1/users`
- `POST /api/v1/users`
- `PATCH /api/v1/users/{user_id}/deactivate`

Criação e desativação: `admin`.
Listagem: `admin` e `manager`.

Usuários não podem ser vinculados a filiais de outro tenant.

## Migrations

Alembic controla o schema. Para aplicar:

```bash
cd backend
alembic upgrade head
```

No Docker Compose, o backend aplica `alembic upgrade head` antes de iniciar o Uvicorn.

## Gates de produção deste módulo

Antes de produção real, além do CI atual, devem existir:

- gestão de segredo em cofre/KMS;
- rate limiting de login/MFA;
- política de bloqueio progressivo após falhas;
- trilha de auditoria de mudanças de papel e status;
- recuperação segura de MFA;
- política formal de rotação de chaves JWT;
- testes de segurança e pentest;
- HTTPS obrigatório na borda.
