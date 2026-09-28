#!/usr/bin/env python3
"""Bepul 1-1 sinov darsi landingini www.myteacher.uz/bepul-dars/ ga ko'chiradi.

Landingning yagona manbasi — live-lesson repo'dagi public/bepul-dars.html.
Bu skript uni shu saytga nusxalaydi va saytning kuzatuv kodlarini
(Yandex Metrika, Meta Pixel) qo'shadi.

Ishlatish:  python3 tools/bepul-dars-yangila.py [../live-lesson]
"""
import pathlib
import shutil
import sys

SAYT = pathlib.Path(__file__).resolve().parent.parent
MANBA = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else SAYT.parent / 'live-lesson')
MANZIL = SAYT / 'bepul-dars'

KUZATUV = """
<!-- Yandex.Metrika -->
<script>
  (function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();
  for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
  k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})
  (window, document,'script','https://mc.yandex.ru/metrika/tag.js', 'ym');
  ym(100441294, 'init', {webvisor:true, clickmap:true, referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
</script>
<!-- Meta Pixel -->
<script>
!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};if(!f._fbq)f._fbq=n;
n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}(window,document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '1491793359635771');
fbq('track', 'PageView');
</script>
<link rel="canonical" href="https://myteacher.uz/bepul-dars/">
"""


def main() -> None:
    html = (MANBA / 'public' / 'bepul-dars.html').read_text(encoding='utf-8')
    og = 'content="https://lesson.myteacher.uz/img/bepul/og.jpg"'
    assert og in html, 'OG rasm manzili topilmadi'
    html = html.replace(og, 'content="https://myteacher.uz/bepul-dars/img/bepul/og.jpg"')
    assert '</head>' in html
    html = html.replace('</head>', KUZATUV + '</head>', 1)

    (MANZIL / 'img' / 'bepul').mkdir(parents=True, exist_ok=True)
    (MANZIL / 'index.html').write_text(html, encoding='utf-8')
    for rasm in (MANBA / 'public' / 'img' / 'bepul').iterdir():
        shutil.copy2(rasm, MANZIL / 'img' / 'bepul' / rasm.name)
    print(f'yangilandi: {MANZIL}/index.html')


if __name__ == '__main__':
    main()
