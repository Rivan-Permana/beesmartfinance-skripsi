function unavailable(message, status = 503) {
  return Response.json({ detail: message }, {
    status,
    headers: { "Cache-Control": "no-store" },
  })
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url)
    const isBackend = ["/api", "/media"].some(
      (prefix) => url.pathname === prefix || url.pathname.startsWith(`${prefix}/`),
    )
    if (!isBackend) return env.ASSETS.fetch(request)

    if (!env.BACKEND_ORIGIN) {
      return unavailable("Backend belum terhubung. Hubungi administrator aplikasi.")
    }

    let origin
    try {
      origin = new URL(env.BACKEND_ORIGIN)
      if (origin.protocol !== "https:" || origin.username || origin.password ||
          origin.pathname !== "/" || origin.search || origin.hash ||
          origin.origin === url.origin) {
        throw new Error("Invalid backend origin")
      }
    } catch {
      return unavailable("Konfigurasi backend tidak valid.")
    }

    // Set the origin explicitly: a path starting with // must not change the host.
    url.protocol = origin.protocol
    url.host = origin.host
    const upstream = new Request(url, request)
    upstream.headers.delete("host")
    try {
      // Preserve redirects for the browser instead of following them with JWT headers.
      const response = await fetch(upstream, { redirect: "manual" })
      const result = new Response(response.body, response)
      result.headers.set("Cache-Control", "no-store")
      return result
    } catch {
      return unavailable("Backend sedang tidak dapat dihubungi. Coba lagi nanti.", 502)
    }
  },
}
