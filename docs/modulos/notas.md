# Notas e boletim

`GET /api/v1/notas/alunos/{aluno_id}/boletim?ano_letivo=2026` retorna somente o ano solicitado.
Sem parâmetro, usa o ano atual; a resposta identifica `ano_letivo`.
Responsáveis e alunos continuam sujeitos ao vínculo de acesso.
Em transferências no mesmo ano, por disciplina e bimestre, vale o lançamento mais recente
(data de lançamento e ID como desempate). A média usa apenas esses registros.
O lançamento exige matrícula ativa na turma e, para professor, vínculo docente.
