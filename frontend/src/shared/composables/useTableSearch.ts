import { computed, ref, type MaybeRefOrGetter, toValue } from "vue"

type SearchableText = string | null | undefined

/** Client-side live filter — cocok untuk baris tabel yang sudah dimuat. */
export function useTableSearch<T>(
  rows: MaybeRefOrGetter<T[]>,
  getSearchableText: (row: T) => SearchableText | SearchableText[],
) {
  const query = ref("")

  const filtered = computed(() => {
    const q = query.value.trim().toLowerCase()
    const list = toValue(rows)
    if (!q) return list
    return list.filter((row) => {
      const texts = getSearchableText(row)
      const arr = Array.isArray(texts) ? texts : [texts]
      return arr.some((t) => String(t ?? "").toLowerCase().includes(q))
    })
  })

  return { query, filtered }
}
