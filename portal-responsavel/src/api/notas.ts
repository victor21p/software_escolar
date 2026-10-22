import { api } from './client'
import type { BoletimRead } from '../types/api'

export const notasApi = {
  boletim: (alunoId: number, anoLetivo?: number) =>
    api.get<BoletimRead>(`/notas/alunos/${alunoId}/boletim`, { params: { ano_letivo: anoLetivo } }).then((r) => r.data),
}
