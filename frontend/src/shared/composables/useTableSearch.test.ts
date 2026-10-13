import { describe, expect, it } from "vitest"
import { ref } from "vue"

import { useTableSearch } from "./useTableSearch"

describe("useTableSearch", () => {
  it("hanya cocokkan field yang disertakan getter", () => {
    const rows = ref([
      { nama: "Aisyah Putri", ibu: "Ibu Wali" },
      { nama: "Bima Sakti", ibu: "Ibu Wali" },
    ])
    const { query, filtered } = useTableSearch(rows, (r) => [r.nama])

    query.value = "b"
    expect(filtered.value.map((r) => r.nama)).toEqual(["Bima Sakti"])
  })
})
