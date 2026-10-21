async (page, name, check) => {
  const geometry = [], errors = []
  const onError = error => errors.push(String(error))
  page.on('pageerror', onError)
  async function measure() {
    return page.evaluate(() => {
      const issues = [], visible = e => e.getBoundingClientRect().width && e.getBoundingClientRect().height
      if (document.documentElement.scrollWidth > innerWidth + 1) issues.push('Page overflows horizontally')
      for (const button of document.querySelectorAll('.bee-select-clear')) {
        if (!visible(button)) continue
        const box = button.getBoundingClientRect(), select = button.closest('.p-select').getBoundingClientRect()
        const icon = button.querySelector('svg').getBoundingClientRect()
        if (Math.abs(icon.y + icon.height / 2 - select.y - select.height / 2) > 1) issues.push('Clear icon is off centre')
        if (box.width < 44 || box.height < 44 || box.right > select.right || box.x < select.x) issues.push('Clear target is clipped or too small')
      }
      for (const dialog of document.querySelectorAll('.p-dialog')) {
        if (!visible(dialog)) continue
        const box = dialog.getBoundingClientRect(), footer = dialog.querySelector('.p-dialog-footer')
        const content = dialog.querySelector('.p-dialog-content')
        if (box.x < -1 || box.right > innerWidth + 1 || box.y < -1 || box.bottom > innerHeight + 1) issues.push('Dialog exceeds viewport')
        if (dialog.scrollWidth > dialog.clientWidth + 1 || content?.scrollWidth > content?.clientWidth + 1) issues.push('Dialog overflows horizontally')
        if (footer && content) {
          const edge = footer.getBoundingClientRect()
          if (content.getBoundingClientRect().bottom > edge.y + 1) issues.push('Content overlaps footer')
          for (const button of footer.querySelectorAll('button')) {
            const b = button.getBoundingClientRect()
            if (b.x < box.x || b.right > box.right || b.y < edge.y || b.bottom > edge.bottom) issues.push('Footer action is clipped')
          }
          const scrollTop = content.scrollTop
          content.scrollTop = content.scrollHeight
          const last = [...content.querySelectorAll('input, textarea, [role="combobox"]')].filter(visible).at(-1)
          if (last && last.getBoundingClientRect().bottom > edge.y + 1) issues.push('Last field cannot scroll above footer')
          content.scrollTop = scrollTop
        }
      }
      const overflow = issues.length ? [...document.querySelectorAll('body *')].filter(e => { const r = e.getBoundingClientRect(); return visible(e) && r.right > innerWidth + 1 && getComputedStyle(e).position !== 'absolute' }).slice(0, 12).map(e => ({tag:e.tagName, class:e.getAttribute('class'), right:e.getBoundingClientRect().right})) : []
      return { width: innerWidth, height: innerHeight, pageWidth:document.documentElement.scrollWidth, containers:[...document.querySelectorAll('.p-datatable-table-container')].map(e=>({overflow:getComputedStyle(e).overflow,client:e.clientWidth,scroll:e.scrollWidth})), bodyChildren:[...document.body.children].map(e=>({tag:e.tagName,cls:e.getAttribute('class'),right:e.getBoundingClientRect().right})).filter(e=>e.right>innerWidth+1), dialogs: document.querySelectorAll('.p-dialog').length, clearButtons: document.querySelectorAll('.bee-select-clear').length, issues, overflow }
    })
  }
  const reviewedPage = new Proxy(page, { get(target, key) {
    if (key === 'screenshot') return async options => {
      const original = page.viewportSize()
      const print = await page.evaluate(() => matchMedia('print').matches)
      const sizes = print ? [{width:794,height:1123}] : [{width:1440,height:1000},{width:1024,height:768},{width:768,height:900},{width:390,height:844},{width:320,height:640},{width:720,height:450}]
      for (const size of sizes) {
        await page.setViewportSize(size)
        await page.evaluate(async () => { await Promise.all(document.getAnimations().filter(a => a.effect?.getComputedTiming().iterations !== Infinity).map(a => a.finished.catch(() => {}))) })
        await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
        const row = await measure()
        geometry.push({ screen: options.path.split('/').at(-1), ...row })
        if (row.issues.length) {
          await page.screenshot({path:`design-artifacts/bee-design-system/audit-${name}-failure.png`, animations:'disabled', scale:'css'})
          throw new Error(`${name} ${options.path} ${JSON.stringify(row)}`)
        }
      }
      await page.setViewportSize(original)
      return target.screenshot({ ...options, path: options.path.replace(/([^/]+)$/, 'audit-$1') })
    }
    const value = Reflect.get(target, key)
    return typeof value === 'function' ? value.bind(target) : value
  } })
  try {
    const result = await check(reviewedPage)
    if (result.ok === false) throw new Error(result.error)
    if (errors.length) throw new Error(errors.join('\n'))
    return { name, ok: true, geometry, flow: result, errors }
  } finally {
    page.off('pageerror', onError)
    await page.unroute('**/api/**')
    await page.evaluate(() => { localStorage.removeItem('bee_access'); localStorage.removeItem('bee_refresh'); document.querySelector('#app')?.__vue_app__?.unmount() })
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/login')
  }
}
