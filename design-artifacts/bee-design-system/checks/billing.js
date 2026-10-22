async (page) => {
  await page.goto('http://127.0.0.1:4173/design-system.html')
  const initial = await page.evaluate(async () => {
    const { billingSamples, billingAccounts } = await import('/src/design-system/billing-fixtures.ts')
    return JSON.parse(JSON.stringify({ rows: billingSamples, accounts: billingAccounts }))
  })
  let rows=initial.rows
  let rejectPayment=true
  let failList=false
  let legacyOnRead=false
  let negativeOnRead=false
  let holdJanuary=false
  let releaseJanuary
  let januaryReadyResolve
  let januaryReady
  const writes=[]
  const paged=(results)=>({count:results.length,next:null,previous:null,results})
  function invoice(row) { return {no_tagihan:row.id,sekolah:'RA Lebah Madu',siswa:row.siswa_nama,nis:'CONTOH',kelompok:null,periode:'Oktober 2026',periode_bulan:row.periode_bulan,periode_tahun:row.periode_tahun,status:row.status,sections:[],rincian:row.detail.map(line=>({komponen:line.komponen,label:line.keterangan,nominal:line.nominal})),total:row.total,no_jurnal:null,total_terbayar:row.total_terbayar,sisa_tagihan:row.sisa_tagihan,perlu_rekonsiliasi:row.perlu_rekonsiliasi} }
  await page.unroute('**/api/**')
  await page.evaluate(()=>localStorage.setItem('bee_access','synthetic-local-review'))
  await page.route('**/api/**',async route=>{
    const request=route.request()
    const url=new URL(request.url())
    const path=url.pathname.replace(/^.*\/api\/v1/,'')
    if(request.method()!=='GET') {
      const payload=request.postDataJSON()
      writes.push({method:request.method(),path,payload})
      if(path==='/tagihan/1/bayar/' && request.method()==='POST') {
        if(rejectPayment) return route.fulfill({status:503,json:{detail:'Simulated temporary failure'}})
        const old=rows[0]
        const payment={id:3,tanggal:payload.tanggal,no_bukti:payload.no_bukti,nominal:payload.nominal,akun_kas:payload.akun_kas,jurnal:'CONTOH-JURNAL-3',jurnal_status:'DRAFT',created_by:1,dibatalkan:false,alasan_batal:'',dibatalkan_pada:null,alokasi:payload.alokasi}
        rows=[{...old,total_terbayar:payload.nominal,sisa_tagihan:(Number(old.total)-Number(payload.nominal)).toFixed(2),status:'SEBAGIAN',pembayaran:[payment]},...rows.slice(1)]
        return route.fulfill({status:200,json:{detail:'Contoh berhasil',tagihan:rows[0],pembayaran:payment,jurnal_id:'CONTOH-JURNAL-3'}})
      }
      if(path==='/tagihan/preview-batch/') return route.fulfill({status:200,json:{count:4,skipped:[],previews:[rows[0]]}})
      return route.fulfill({status:405,json:{detail:'Local review: mutation disabled'}})
    }
    let data=paged([])
    if(path==='/auth/me/') data={id:1,username:'contoh',nama:'Pengguna Contoh',is_superuser:false,groups:['Administration']}
    else if(path==='/tagihan/') {
      if(failList) return route.fulfill({status:503,json:{detail:'Synthetic failure'}})
      data=paged(rows)
    } else if(path==='/siswa/') data=paged(rows.map(row=>({id:row.siswa,nama:row.siswa_nama,status:'aktif',spp_nominal:'750000.00'})))
    else if(path==='/coa/') data=paged(initial.accounts)
    else if(path==='/jenjang/') data=paged([{id:1,kode:'TK A',nama:'TK A'}])
    else if(path==='/tarif-katering/') {
      const month=Number(url.searchParams.get('bulan'))
      if(holdJanuary && month===1) await new Promise(resolve=>{releaseJanuary=resolve;januaryReadyResolve()})
      data={tarif_harian:month===1?'11100.00':month===2?'22200.00':'25000.00'}
    } else if(/^\/tagihan\/\d+\/struk\/$/.test(path)) data=invoice(rows.find(row=>row.id===Number(path.split('/')[2])))
    else if(/^\/tagihan\/\d+\/$/.test(path)) {
      data=rows.find(row=>row.id===Number(path.split('/')[2]))
      if(legacyOnRead && data.id===1) data={...data,perlu_rekonsiliasi:true,total_terbayar:null,sisa_tagihan:null}
      if(negativeOnRead && data.id===1) data={...data,detail:[...data.detail,{id:99,komponen:'LAIN',kategori:'LAIN',keterangan:'Potongan contoh',akun_pendapatan:'411',nominal:'-100'}]}
    }
    return route.fulfill({status:200,json:data})
  })
  try {
    await page.setViewportSize({width:1440,height:1000})
    await page.goto('http://127.0.0.1:4173/tagihan')
    await page.locator('.tagihan-desktop tbody tr').first().waitFor()
    await page.locator('.tagihan-directory[aria-busy="false"]').waitFor()
    await page.evaluate(()=>document.fonts.ready)
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Administration-tagihan-04.png',scale:'css',animations:'disabled'})
    const pay=page.getByRole('button',{name:'Catat pembayaran Alya Putri Oktober 2026',exact:true})
    legacyOnRead=true
    await pay.click()
    await page.getByText(/Pembayaran lama perlu direkonsiliasi/).first().waitFor()
    if(await page.getByRole('dialog',{name:'Catat pembayaran'}).count()) throw new Error('Reconciliation allowed payment')
    legacyOnRead=false
    negativeOnRead=true
    await pay.click()
    await page.getByText(/Sesuaikan potongan menjadi rincian netto/).first().waitFor()
    if(await page.getByRole('dialog',{name:'Catat pembayaran'}).count()) throw new Error('Negative component allowed payment')
    negativeOnRead=false
    await pay.click()
    const dialog=page.getByRole('dialog',{name:'Catat pembayaran',exact:true})
    await dialog.getByRole('button',{name:'Simpan pembayaran',exact:true}).click()
    await dialog.getByText('Isi nomor bukti penerimaan.',{exact:true}).waitFor()
    if(writes.length) throw new Error('Blank form sent a payment')
    await dialog.locator('#bukti-bayar').fill(' BKT-DECIMAL ')
    await dialog.locator('#tanggal-bayar').fill('16/10/2026')
    await dialog.locator('#tanggal-bayar').press('Tab')
    await dialog.getByLabel('SPP Oktober',{exact:true}).fill('Rp 0,10')
    await dialog.getByLabel('Katering Oktober',{exact:true}).fill('Rp 0,20')
    await dialog.getByLabel('Katering Oktober',{exact:true}).press('Tab')
    await dialog.getByRole('button',{name:'Simpan pembayaran',exact:true}).click()
    await dialog.locator('.payment-notice').waitFor()
    const proof=await dialog.locator('#bukti-bayar').inputValue()
    if(proof.trim()!=='BKT-DECIMAL') throw new Error('Payment proof lost on failure')
    const first=writes[0].payload
    if(first.nominal!=='0.30' || first.tanggal!=='2026-10-16' || first.no_bukti!=='BKT-DECIMAL' || first.alokasi[0].nominal!=='0.10' || first.alokasi[1].nominal!=='0.20') throw new Error('Payment payload changed')
    rejectPayment=false
    await dialog.getByRole('button',{name:'Simpan pembayaran',exact:true}).click()
    await dialog.waitFor({state:'hidden'})
    if(writes[1].payload.request_id!==first.request_id) throw new Error('Retry changed idempotency key')
    await page.getByRole('button',{name:'Rincian tagihan Alya Putri Oktober 2026',exact:true}).click()
    await page.getByRole('menuitem',{name:'Riwayat pembayaran',exact:true}).click()
    const history=page.getByRole('dialog',{name:'Riwayat pembayaran',exact:true})
    await history.getByText('BKT-DECIMAL',{exact:true}).waitFor()
    await history.getByText('Menunggu pencatatan keuangan',{exact:true}).waitFor()
    await history.getByRole('button',{name:'Tutup',exact:true}).click()
    await page.getByRole('button',{name:'Rincian tagihan Daffa Ramadhan September 2026',exact:true}).click()
    if(await page.getByRole('menuitem',{name:'Ubah tagihan',exact:true}).count()) throw new Error('Legacy invoice can be edited')
    await page.getByRole('menuitem',{name:'Lihat faktur',exact:true}).click()
    const struk=page.getByRole('dialog',{name:'Faktur tagihan',exact:true})
    await struk.getByText('Perlu dicocokkan',{exact:true}).waitFor()
    if((await struk.innerText()).includes('Dibayar: Rp 0')) throw new Error('Unknown invoice printed zero')
    await page.evaluate(()=>{window.print=()=>{window.__printProbe={classActive:document.body.classList.contains('bee-print-struk'),masks:document.querySelectorAll('body > .struk-print-mask').length};window.dispatchEvent(new Event('afterprint'))}})
    await struk.getByRole('button',{name:'Cetak',exact:true}).click()
    const print=await page.evaluate(()=>({...window.__printProbe,classClean:!document.body.classList.contains('bee-print-struk')}))
    if(!print.classActive || print.masks!==1 || !print.classClean) throw new Error('Print masking or cleanup changed')
    await struk.getByRole('button',{name:'Tutup',exact:true}).last().click()
    await page.getByRole('button',{name:'Buat sekaligus',exact:true}).click()
    const batch=page.getByRole('dialog',{name:'Buat tagihan sekaligus',exact:true})
    await batch.getByRole('button',{name:'Periksa daftar',exact:true}).click()
    const generate=batch.getByRole('button',{name:'Buat tagihan terpilih',exact:true})
    await page.waitForFunction(()=>!Array.from(document.querySelectorAll('button')).find(el=>el.textContent.includes('Buat tagihan terpilih')).disabled)
    await batch.locator('#batch-bulan').click()
    await page.getByRole('option',{name:'Januari',exact:true}).click()
    if(!await generate.isDisabled()) throw new Error('Stale batch preview remained usable')
    await batch.getByRole('button',{name:'Batal',exact:true}).click()
    holdJanuary=true
    januaryReady=new Promise(resolve=>{januaryReadyResolve=resolve})
    await page.getByRole('button',{name:'Buat tagihan',exact:true}).click()
    const gen=page.getByRole('dialog',{name:'Buat tagihan',exact:true})
    await gen.locator('#generate-bulan').click()
    await page.getByRole('option',{name:'Januari',exact:true}).click()
    await januaryReady
    await gen.locator('#generate-bulan').click()
    await page.getByRole('option',{name:'Februari',exact:true}).click()
    await page.waitForFunction(()=>document.querySelector('#generate-tarif').value.replace(/\D/g,'')==='22200')
    const responseA=page.waitForResponse(response=>response.url().includes('/tarif-katering/') && new URL(response.url()).searchParams.get('bulan')==='1')
    releaseJanuary()
    await (await responseA).finished()
    await page.evaluate(()=>new Promise(requestAnimationFrame))
    const tariff=await gen.locator('#generate-tarif').inputValue()
    if(tariff.replace(/\D/g,'')!=='22200') throw new Error('Old tariff response overwrote the selected period')
    await gen.getByRole('button',{name:'Batal',exact:true}).click()
    await page.setViewportSize({width:320,height:800})
    await page.evaluate(()=>scrollTo(0,0))
    await page.waitForFunction(()=>document.documentElement.scrollWidth<=innerWidth)
    await page.screenshot({path:'design-artifacts/bee-design-system/role-Administration-tagihan-mobile-04.png',scale:'css',animations:'disabled'})
    await page.locator('.tagihan-mobile').getByRole('button',{name:'Catat pembayaran',exact:true}).first().click()
    await dialog.waitFor()
    const mobile=await dialog.evaluate(el=>({scroll:el.scrollWidth,client:el.clientWidth,viewport:innerWidth}))
    if(mobile.scroll>mobile.client) throw new Error('Mobile payment dialog overflows')
    await page.screenshot({path:'design-artifacts/bee-design-system/tagihan-payment-mobile-04.png',scale:'css',animations:'disabled'})
    await dialog.getByRole('button',{name:'Batal',exact:true}).click()
    failList=true
    await page.reload()
    await page.getByText('Tagihan belum berhasil dimuat. Periksa koneksi, lalu coba lagi.',{exact:true}).waitFor()
    if(await page.getByText('Belum ada tagihan siswa',{exact:true}).count()) throw new Error('Loading failure was shown as empty data')
    return {payment:first,requestIdPreserved:writes[1].payload.request_id===first.request_id,guards:['reconciliation','negative component','blank form','stale batch preview'],print,tariff,mobile,source:'All API requests intercepted; print stubbed, no school data or printer changed',writes:writes.map(item=>({path:item.path,method:item.method}))}
  } finally {
    releaseJanuary?.()
    await page.unroute('**/api/**')
    await page.goto('http://127.0.0.1:4173/design-system.html#layar-tagihan')
    await page.evaluate(()=>localStorage.removeItem('bee_access'))
  }
}
