import { useState } from 'react'

export function AnoLetivoSelector({value, onChange, disabled = false}: {value: number; onChange: (ano: number) => void; disabled?: boolean}) {
  const [anoAtual] = useState(() => new Date().getFullYear())
  return <label className="mb-4 block text-sm font-medium text-slate-700">
    Ano letivo
    <select aria-label="Ano letivo" disabled={disabled} className="input mt-1 w-36" value={value}
      onChange={(e) => onChange(Number(e.target.value))}>
      {Array.from({length: Math.max(1, anoAtual - 2018)}, (_, i) => anoAtual + 1 - i)
        .map((ano) => <option key={ano} value={ano}>{ano}</option>)}
    </select>
  </label>
}
