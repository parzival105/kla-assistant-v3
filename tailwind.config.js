module.exports = {
  content: ['./pages/**/*.{js,ts,jsx,tsx}','./components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: { 400:'#a855f7',500:'#8b2fc9',600:'#6d28a0',700:'#431061',800:'#2d0840',900:'#1a0530' },
        dark:  { 50:'#c4b5d4',100:'#9d7fba',200:'#7c5fa0',300:'#6b4f8a',400:'#4a3060',500:'#2d1a45',600:'#1f1035',700:'#180d28',800:'#130a1e',900:'#0d0516' },
      },
      fontFamily: { sans:['Inter','sans-serif'], mono:['JetBrains Mono','monospace'] },
    },
  },
  plugins: [],
}
