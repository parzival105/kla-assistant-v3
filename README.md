# KLA Business Suite

Aplikasi internal PT KLA Teknologi Indonesia: inventory, analisa cabang, dan PC builder.
Frontend Next.js (pages router) plus API Python serverless di folder `api/`, deploy di Vercel.

Live (production): https://kla-vercel-theta.vercel.app
Login default: `admin` / `admin123`

## Stack

- Next.js 14 (pages router), React 18, Tailwind CSS
- Python 3.12 serverless functions (`api/**/*.py`), pandas untuk analisa Excel
- Deploy: Vercel (framework preset `nextjs`)

## Catatan penting: versi tanpa Supabase

Versi ini berjalan TANPA Supabase. Data (users, metadata analisa, komponen PC)
disimpan lokal di `/tmp/kla_data` saat runtime, dan auth memakai token HMAC
stateless (ditandatangani dengan `JWT_SECRET`).

Konsekuensi: `/tmp` bersifat ephemeral per instance serverless, jadi data yang
di-upload tidak persisten lintas cold start. Cocok untuk demo. Untuk pemakaian
tim yang butuh data permanen dan dipakai bersama, sambungkan kembali database
(mis. Supabase) di `lib/python/db.py` dan `lib/python/storage.py`.

## Environment variables

Lihat `.env.local.example`. Yang wajib untuk produksi:

- `JWT_SECRET` — string acak panjang untuk menandatangani token. Kalau tidak
  diset, kode memakai default bawaan (JANGAN dipakai di produksi).

Opsional:

- `KLA_DATA_DIR` — direktori penyimpanan data lokal (default `/tmp/kla_data`).

## Menjalankan secara lokal

```bash
npm install
npm run dev        # http://localhost:3000
```

Untuk menjalankan API Python secara lokal seperti di Vercel:

```bash
npm i -g vercel
vercel dev
```

## Deploy

```bash
vercel deploy --prod
```

Fungsi serverless dibatasi 12 di Vercel Hobby plan. Endpoint auth dan inventory
sudah dikonsolidasi jadi dua router (`api/auth.py`, `api/inventory.py`) lewat
rewrite `?__sub=` di `vercel.json` supaya total fungsi tetap di bawah batas.

## Struktur

```
api/            Python serverless functions
  auth.py       router: login, logout, me, users
  inventory.py  router: upload, status, summary, products, dst
  branch/       ringkasan dan detail cabang
  pc_builder/   config dan build PC
  sales/        query asisten sales
  export/       export Excel
components/      komponen React (UI, chart, layout)
lib/
  api.ts        axios client
  auth.ts       helper auth (cookie)
  python/        engine analisa, config, db, storage
pages/          halaman Next.js
styles/         Tailwind global
```

## Follow-up yang belum dikerjakan

- Set `JWT_SECRET` produksi di Vercel (sekarang masih pakai default bawaan).
- Rekonsiliasi path frontend/backend: `lib/api.ts` memanggil `/api/pc-builder/*`
  dan `/api/inventory/dead-stock` (pakai tanda hubung), sedangkan fungsi/router
  memakai underscore (`pc_builder`, `deadstock`). Route ini masih 404 sampai
  diseragamkan.
- Kalau butuh data persisten untuk tim, sambungkan kembali database.
"# kla-assistant-v3" 
