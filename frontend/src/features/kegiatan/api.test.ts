import { describe, expect, it, vi } from "vitest"
vi.mock("@/core/api",()=>({api:{get:vi.fn()}}))
import { api } from "@/core/api"
import { kegiatanApi } from "./api"
describe("kegiatanApi.listAll",()=>{
  it("includes later pages and keeps the selected period on every request",async()=>{
    vi.mocked(api.get).mockResolvedValueOnce({data:{results:[{id:1}],next:"/kegiatan/?page=2"}}).mockResolvedValueOnce({data:{results:[{id:2}],next:null}})
    expect((await kegiatanApi.listAll({periode:7})).map(row=>row.id)).toEqual([1,2])
    expect(api.get).toHaveBeenNthCalledWith(1,"/kegiatan/",{params:{page_size:200,periode:7,page:1}})
    expect(api.get).toHaveBeenNthCalledWith(2,"/kegiatan/",{params:{page_size:200,periode:7,page:2}})
  })
})
