import { describe, expect, it, vi } from 'vitest'
vi.mock('@/core/api',()=>({api:{get:vi.fn()}}))
import { api } from '@/core/api'
import { gajiApi, pinjamanApi } from './api'
describe('employee finance pagination',()=>{
  it.each([['gaji',gajiApi],['pinjaman',pinjamanApi]] as const)('loads all %s pages and exposes fresh detail',async(path,client)=>{
    vi.mocked(api.get).mockReset().mockResolvedValueOnce({data:{results:[{id:1}],next:'page-2'}}).mockResolvedValueOnce({data:{results:[{id:2}],next:null}})
    expect(await client.listAll()).toEqual([{id:1},{id:2}])
    expect(api.get).toHaveBeenNthCalledWith(2,`/${path}/`,{params:{page:2}})
    vi.mocked(api.get).mockResolvedValueOnce({data:{id:2}});expect(await client.get(2)).toEqual({id:2})
  })
})
