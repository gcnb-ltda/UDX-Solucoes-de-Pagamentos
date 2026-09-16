# Boundary regulatório e operacional

Este repositório implementa software de pagamentos; ele não concede, por si só, autorização regulatória nem participação no Pix.

Antes do go-live financeiro, a UDX deve documentar formalmente qual papel exerce em cada fluxo: camada tecnológica, estabelecimento/subcredenciador, instituição de pagamento, participante Pix ou outro papel contratual/regulatório aplicável.

## Gates

- contrato e homologação do PSP/banco;
- matriz de responsabilidades UDX x provider;
- KYC/KYB e PLD/FTP conforme o modelo aplicável;
- controles de fraude e incidentes;
- LGPD, retenção e direitos de titulares;
- PCI DSS v4.0.1 se houver captura/processamento/armazenamento de dados de cartão no escopo;
- termos, políticas e evidências de consentimento;
- plano de continuidade, backup, restore e resposta a incidentes;
- pentest independente e correção de achados críticos/altos.

Nenhum endpoint interno deve ser interpretado como conexão homologada com SPI/DICT sem o respectivo contrato, autorização e integração operacional.
