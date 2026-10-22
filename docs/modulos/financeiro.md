# Financeiro

Mensalidades usam matrículas ativas e preços por série/ano. Não existe valor padrão
na falta de preço. Aluno sem matrícula ativa no ano não recebe mensalidade.
O índice parcial garante uma mensalidade por aluno/competência inclusive sob concorrência.
Na implantação da migration 0007, duplicidades existentes devem ser resolvidas previamente.

Cobranças PENDENTE ou ATRASADA vencidas além da tolerância contam como inadimplência.
A leitura exibe o atraso e filtra pelo status efetivo sem escrever no banco.
A aprovação de matrícula publica um evento compartilhado; o financeiro cria a taxa na
mesma transação. O pagamento publica o evento de ativação. Taxa zero é quitada automaticamente.

Auditoria obrigatória: `bolsa.criar`, `bolsa.alterar`, `cobranca.pagar`.
Os registros incluem autor, entidade e valores anteriores/novos. Webhooks assinados
usam o autor SISTEMA; repetir o pagamento não gera outra baixa nem outro log.
O assistente encaminha a identidade autenticada para os mesmos services da API.
