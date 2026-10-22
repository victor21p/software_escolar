import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AxiosError, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import { api, getAccessToken, setAccessToken } from './client'

function response(config: InternalAxiosRequestConfig, data: unknown, status = 200): AxiosResponse {
  return {config, data, status, statusText: String(status), headers: {}}
}

beforeEach(() => {localStorage.clear(); setAccessToken(null)})

describe('autenticação da API', () => {
  it('envia o token e remove a sessão no logout', async () => {
    const adapter = vi.fn(async (config) => response(config, {}))
    api.defaults.adapter = adapter
    setAccessToken('token-de-teste')
    await api.get('/pessoas/alunos')
    expect(adapter.mock.calls[0][0].headers.Authorization).toBe('Bearer token-de-teste')
    setAccessToken(null)
    expect(getAccessToken()).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('compartilha um único refresh entre requisições simultâneas', async () => {
    let refreshes = 0
    api.defaults.adapter = async (config) => {
      if (config.url === '/auth/refresh') {
        refreshes++
        return response(config, {access_token:'renovado'})
      }
      if (config.headers.Authorization !== 'Bearer renovado') {
        throw new AxiosError('Expirado', 'ERR_BAD_REQUEST', config, null, response(config, {}, 401))
      }
      return response(config, {ok:true})
    }
    setAccessToken('expirado')
    const results = await Promise.all([api.get('/um'), api.get('/dois')])
    expect(results.every((r) => r.data.ok)).toBe(true)
    expect(refreshes).toBe(1)
    expect(getAccessToken()).toBe('renovado')
  })

  it('não repete login nem entra em loop quando o refresh é recusado', async () => {
    const adapter = vi.fn(async (config) => {
      throw new AxiosError('Sem sessão', 'ERR_BAD_REQUEST', config, null, response(config, {}, 401))
    })
    api.defaults.adapter = adapter
    setAccessToken('expirado')
    await expect(api.get('/restrito')).rejects.toBeInstanceOf(AxiosError)
    expect(adapter).toHaveBeenCalledTimes(2)
    expect(getAccessToken()).toBeNull()
    adapter.mockClear()
    await expect(api.post('/auth/login', {})).rejects.toBeInstanceOf(AxiosError)
    expect(adapter).toHaveBeenCalledTimes(1)
  })
})
