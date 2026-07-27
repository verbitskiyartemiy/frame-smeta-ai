from __future__ import annotations
import base64
import io
import os

BASE = os.path.dirname(__file__)
FIG = os.path.abspath(os.path.join(BASE, "..", "reports", "figures"))
OUT = os.path.abspath(os.path.join(BASE, "..", "docs", "deck_ml.html"))


def img(name: str) -> str:
    with open(os.path.join(FIG, name + ".png"), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


HEAD = """<title>FRAME · ИИ-слой продукта · 1920x1080</title>
<style>
  :root{
    --bg:#0e1216; --slide:#ffffff; --ink:#13171b; --soft:#4b555e; --faint:#8b959e;
    --line:#e4e8ec; --wash:#f5f7f9;
    --key:#1d5fa8; --ok:#1e8b5f; --warm:#c1571f; --bad:#b8402c; --gold:#8a6a1a;
    --mono:ui-monospace,"Cascadia Code",Consolas,"SF Mono",Menlo,monospace;
    --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);font-family:var(--sans);-webkit-font-smoothing:antialiased}
  .wrap{padding:26px 16px 80px}
  .bar{max-width:1400px;margin:0 auto 22px;color:#dfe5ea;display:flex;gap:14px;
    align-items:baseline;flex-wrap:wrap;padding:0 6px}
  .bar h1{font-size:15px;font-weight:700}
  .bar span{font-family:var(--mono);font-size:11.5px;color:#8b959e}

  .scaler{max-width:1400px;margin:0 auto 30px;overflow:hidden}
  .slide{width:1920px;height:1080px;background:var(--slide);color:var(--ink);
    padding:70px 92px 64px;position:relative;display:flex;flex-direction:column;
    transform-origin:top left;overflow:hidden}

  .tag{display:inline-block;font-family:var(--mono);font-size:19px;font-weight:700;
    letter-spacing:.1em;text-transform:uppercase;color:#fff;background:var(--key);
    padding:8px 18px;border-radius:8px}
  .tag.g{background:var(--ok)} .tag.o{background:var(--warm)} .tag.d{background:var(--gold)}
  h2{font-size:60px;font-weight:770;letter-spacing:-.025em;line-height:1.05;
    margin:18px 0 6px;max-width:32ch}
  h2.sm{font-size:50px}
  .pg{position:absolute;right:92px;bottom:38px;font-family:var(--mono);
    font-size:18px;color:var(--faint)}

  /* pain → change → value strip */
  .strip{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;border:2px solid var(--line);
    border-radius:16px;overflow:hidden;margin-top:26px}
  .strip > div{padding:26px 30px;border-right:2px solid var(--line)}
  .strip > div:last-child{border-right:none}
  .strip .h{font-family:var(--mono);font-size:16px;letter-spacing:.11em;
    text-transform:uppercase;font-weight:700;color:var(--faint);margin-bottom:14px}
  .strip .big{font-size:44px;font-weight:770;line-height:1.08;letter-spacing:-.02em}
  .strip .big.bad{color:var(--bad)} .strip .big.ok{color:var(--ok)} .strip .big.key{color:var(--key)}
  .strip p{font-size:23px;color:var(--soft);line-height:1.35;margin-top:12px}
  .strip.pain{background:var(--wash)}

  .cols{display:grid;grid-template-columns:1fr 1fr;gap:52px;flex:1;min-height:0;
    align-items:center;margin-top:24px}
  .cols.wide{grid-template-columns:1.25fr 1fr}
  .cols > div{min-width:0}
  .figbox{display:flex;align-items:center;justify-content:center;min-height:0;height:100%}
  .fig{max-width:100%;max-height:100%;object-fit:contain}

  .lbl{font-family:var(--mono);font-size:17px;letter-spacing:.11em;text-transform:uppercase;
    font-weight:700;color:var(--faint);margin-bottom:14px}

  .before{display:grid;grid-template-columns:1fr auto 1fr;gap:26px;align-items:center;
    margin-top:6px}
  .ba{border:2px solid var(--line);border-radius:14px;padding:24px 26px}
  .ba.now{background:var(--wash)}
  .ba .t{font-family:var(--mono);font-size:16px;letter-spacing:.1em;text-transform:uppercase;
    font-weight:700;margin-bottom:12px}
  .ba.was .t{color:var(--bad)} .ba.now .t{color:var(--ok)}
  .ba p{font-size:25px;line-height:1.35;color:var(--soft)}
  .ba b{color:var(--ink)}
  .arr{font-size:46px;color:var(--faint)}

  .demo{border:2px solid var(--line);border-radius:14px;overflow:hidden;font-size:23px}
  .demo .row{display:grid;grid-template-columns:1fr auto;gap:18px;padding:14px 20px;
    border-bottom:1px solid var(--line);align-items:center}
  .demo .row:last-child{border-bottom:none}
  .demo .row.head{background:var(--wash);font-family:var(--mono);font-size:16px;
    letter-spacing:.06em;text-transform:uppercase;color:var(--faint);font-weight:700}
  .demo .row.total{background:#f8fafb;font-weight:700;font-size:26px}
  .v{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap;font-weight:700}
  .v.bad{color:var(--bad)} .v.good{color:var(--ok)} .v.dim{color:var(--faint)}
  .muted{color:var(--faint)}

  .card{border:2px solid var(--line);border-left:8px solid var(--key);border-radius:12px;
    padding:16px 20px;margin-bottom:14px;font-size:22px}
  .card.o{border-left-color:var(--warm)} .card.g{border-left-color:var(--ok)}
  .card .t{font-family:var(--mono);font-size:15px;letter-spacing:.08em;
    text-transform:uppercase;color:var(--key);font-weight:700}
  .card.o .t{color:var(--warm)} .card.g .t{color:var(--ok)}
  .card .m{margin-top:7px;line-height:1.35}
  .card .btns{margin-top:11px;display:flex;gap:9px;flex-wrap:wrap}
  .btn{font-size:18px;border:2px solid var(--line);border-radius:8px;padding:6px 14px;
    color:var(--soft);font-weight:600}
  .btn.p{background:var(--key);border-color:var(--key);color:#fff}

  ul{list-style:none} li{padding-left:32px;position:relative;margin:15px 0;
    font-size:25px;line-height:1.38;color:var(--soft)}
  li::before{content:"";position:absolute;left:2px;top:.55em;width:11px;height:11px;
    border-radius:3px;background:var(--key)}
  li.ok::before{background:var(--ok)} li.warm::before{background:var(--warm)}
  li b{color:var(--ink);font-weight:680}

  .moat{border:2px solid var(--gold);background:#fdfaf2;border-radius:14px;
    padding:22px 26px;margin-top:22px}
  .moat .t{font-family:var(--mono);font-size:16px;letter-spacing:.1em;text-transform:uppercase;
    font-weight:700;color:var(--gold);margin-bottom:10px}
  .moat p{font-size:26px;line-height:1.35;color:var(--ink);font-weight:600}

  .evid{margin-top:auto;padding-top:20px;border-top:2px solid var(--line);
    display:flex;gap:44px;flex-wrap:wrap;align-items:baseline}
  .evid .e{font-size:21px;color:var(--soft)}
  .evid .e b{font-family:var(--mono);font-size:26px;color:var(--ok);font-weight:750}
  .evid .cap{font-family:var(--mono);font-size:15px;letter-spacing:.1em;
    text-transform:uppercase;color:var(--faint);font-weight:700}

  /* flywheel */
  .wheel{display:grid;grid-template-columns:repeat(3,1fr);gap:30px;margin-top:30px;flex:1;
    align-items:stretch}
  .node{border:2px solid var(--line);border-radius:16px;padding:26px 26px;display:flex;
    flex-direction:column;position:relative}
  .node .n{font-family:var(--mono);font-size:16px;letter-spacing:.1em;font-weight:700;
    text-transform:uppercase}
  .node h3{font-size:32px;font-weight:750;margin:10px 0;line-height:1.12;letter-spacing:-.015em}
  .node .gives{margin-top:auto;padding-top:16px;border-top:2px dashed var(--line);
    font-size:21px;color:var(--soft);line-height:1.32}
  .node .gives b{color:var(--ink)}

  .three{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;flex:1;
    align-items:stretch;margin-top:26px}
  .feat{border:2px solid var(--line);border-radius:16px;padding:28px 26px;
    display:flex;flex-direction:column}
  .feat .fi{font-family:var(--mono);font-size:16px;letter-spacing:.1em;font-weight:700;
    text-transform:uppercase}
  .feat h3{font-size:33px;font-weight:750;margin:11px 0;line-height:1.12;letter-spacing:-.015em}
  .feat p{font-size:22px;color:var(--soft);line-height:1.35;flex:1}
  .feat .st{margin-top:16px;font-family:var(--mono);font-size:20px;font-weight:700;color:var(--ok)}

  table{border-collapse:collapse;width:100%;font-size:24px}
  th,td{text-align:left;padding:13px 16px;border-bottom:1px solid var(--line)}
  thead th{font-family:var(--mono);font-size:16px;letter-spacing:.06em;
    text-transform:uppercase;color:var(--faint);font-weight:700}
  tbody tr:last-child td{border-bottom:none}
  td.n{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
  .win{color:var(--ok);font-weight:700} .mark{color:var(--warm);font-weight:700}

  .quote{border-left:6px solid var(--key);padding:16px 0 16px 26px;font-size:29px;
    line-height:1.32;color:var(--ink);font-weight:640;margin-top:20px}
  .quote.ok{border-left-color:var(--ok)} .quote.w{border-left-color:var(--warm)}
  .note{font-size:20px;color:var(--faint);margin-top:12px;line-height:1.35}
  code{font-family:var(--mono);font-size:.86em;background:#eef2f6;padding:3px 9px;border-radius:6px}

  @media print{
    body{background:#fff} .wrap{padding:0} .bar{display:none}
    .scaler{max-width:none;margin:0;overflow:visible}
    .slide{transform:none !important;page-break-after:always}
  }
</style>
<script>
  function fit(){
    document.querySelectorAll(".scaler").forEach(function(s){
      var sl=s.querySelector(".slide"), k=s.clientWidth/1920;
      sl.style.transform="scale("+k+")"; s.style.height=(1080*k)+"px";
    });
  }
  addEventListener("resize",fit);
  addEventListener("DOMContentLoaded",fit);
  addEventListener("load",fit);
</script>
<div class="wrap">
<div class="bar"><h1>FRAME &middot; ИИ-слой продукта</h1><span>6 слайдов &middot; 1920&times;1080 &middot; вставляются в основной дек после «Продукт» &middot; экспорт: Ctrl+P</span></div>
"""


def slide(n, inner):
    return (f'<div class="scaler"><section class="slide">\n{inner}\n'
            f'<div class="pg">{n} / 6</div>\n</section></div>\n')


def build():
    P = []

    # 1 — ИИ как часть бизнес-модели
    P.append(slide(1, """
  <span class="tag">ИИ-слой FRAME</span>
  <h2>ИИ — не витрина, а платный слой продукта</h2>
  <div class="strip">
    <div class="pain">
      <div class="h">Боль · из наших интервью</div>
      <div class="big bad">88%</div>
      <p>заказчиков доплачивают сверх сметы, <b>60%</b> хотели бы независимую проверку —
      это самый частый запрос в кастдеве</p>
    </div>
    <div>
      <div class="h">Альтернатива сегодня</div>
      <div class="big">8–15%</div>
      <p>бюджета стоит строительный технадзор — единственный способ проверить подрядчика.
      Для частного ремонта это неподъёмно</p>
    </div>
    <div>
      <div class="h">Наше предложение</div>
      <div class="big ok">790 ₽/мес</div>
      <p>подписка <b>FRAME UPGRADE</b>: ИИ закрывает ценовую часть работы технадзора
      и делает её массовой</p>
    </div>
  </div>
  <div class="three">
    <div class="feat">
      <div class="fi" style="color:var(--key)">Фича 1 · работает</div>
      <h3>Аудит сметы</h3>
      <p>Проверяет каждую строку сметы по реальным рыночным ценам и показывает,
      о чём спросить подрядчика</p>
      <div class="st">закрывает страх переплаты</div>
    </div>
    <div class="feat">
      <div class="fi" style="color:var(--ok)">Фича 2 · работает</div>
      <h3>Рейтинг мастера</h3>
      <p>Профиль подрядчика по девяти сторонам вместо одной звезды, собранный
      из текста отзывов</p>
      <div class="st">закрывает страх выбора</div>
    </div>
    <div class="feat">
      <div class="fi" style="color:var(--warm)">Фича 3 · MVP</div>
      <h3>AI-координатор</h3>
      <p>Превращает переписку по проекту в задачи, решения и напоминания —
      ничего не теряется</p>
      <div class="st">закрывает страх потери контроля</div>
    </div>
  </div>"""))

    # 2 — фича 1
    P.append(slide(2, """
  <span class="tag">Фича 1 · Аудит сметы</span>
  <h2 class="sm">Заказчик перестаёт быть слабой стороной переговоров</h2>
  <div class="before">
    <div class="ba was">
      <div class="t">Было</div>
      <p>Смета на 194 650 ₽. Человек не знает рыночных цен, спросить не у кого.
      Либо переплачивает, либо ссорится <b>наугад</b></p>
    </div>
    <div class="arr">&rarr;</div>
    <div class="ba now">
      <div class="t">Стало</div>
      <p>За секунды видит: <b>плитка дороже рынка вдвое</b>, штукатурка в норме.
      Идёт к подрядчику с тремя конкретными вопросами</p>
    </div>
  </div>
  <div class="cols" style="margin-top:24px">
    <div>
      <div class="demo">
        <div class="row head"><span>Позиция сметы</span><span>Вердикт</span></div>
        <div class="row"><span>Укладка плитки — 3 200 ₽/м²<br>
          <span class="muted" style="font-size:19px">рынок 891 – 2 112 ₽</span></span>
          <span class="v bad">+182%</span></div>
        <div class="row"><span>Штукатурка стен — 520 ₽/м²<br>
          <span class="muted" style="font-size:19px">рынок 300 – 1 236 ₽</span></span>
          <span class="v good">в норме</span></div>
        <div class="row"><span>Монтаж телепорта — 50 000 ₽<br>
          <span class="muted" style="font-size:19px">работы нет в базе</span></span>
          <span class="v dim">не оцениваем</span></div>
        <div class="row total"><span>Найденная переплата</span>
          <span class="v bad">+82 370 ₽</span></div>
      </div>
      <p class="note">Продукт отдаёт не приговор, а <b>вопрос подрядчику</b> — это снимает
      юридический риск и сохраняет отношения в проекте.</p>
    </div>
    <div>
      <div class="moat">
        <div class="t">Почему это не скопировать</div>
        <p>Базы рыночных цен на ремонт по России <b>не существует в открытом доступе</b>.
        Мы собрали её сами: 2 369 цен, 22 компании, 7 городов. Конкурент должен
        повторить этот сбор с нуля</p>
      </div>
      <ul style="margin-top:20px">
        <li class="ok"><b>Окупает подписку с первой сметы:</b> найденные 82 тысячи против
        790 ₽/мес</li>
        <li><b>Отказывается оценивать</b> незнакомую работу вместо того, чтобы выдумать
        цену — это фича доверия, а не ограничение</li>
      </ul>
    </div>
  </div>
  <div class="evid">
    <span class="cap">Доказательство</span>
    <span class="e"><b>2 369</b> цен собрано вручную</span>
    <span class="e"><b>82%</b> флагов «дорого» верны</span>
    <span class="e"><b>22</b> компании в проверке на незнакомых данных</span>
  </div>"""))

    # 3 — фича 2
    P.append(slide(3, """
  <span class="tag g">Фича 2 · Рейтинг мастера</span>
  <h2 class="sm">Репутация, которую нельзя купить</h2>
  <div class="before">
    <div class="ba was">
      <div class="t">Было</div>
      <p>«4.8 звезды» у всех подряд. Накручивается за деньги, ничего не говорит
      о <b>конкретных рисках</b> мастера</p>
    </div>
    <div class="arr">&rarr;</div>
    <div class="ba now">
      <div class="t">Стало</div>
      <p>Видно: <b>плитку кладёт отлично, но срывает сроки</b>. Заказчик выбирает
      под свой приоритет, а не по средней цифре</p>
    </div>
  </div>
  <div class="cols wide" style="margin-top:20px">
    <div class="figbox"><img class="fig" src="{ASPECT}" alt="Профиль мастера по аспектам"></div>
    <div>
      <div class="moat">
        <div class="t">Почему это не скопировать</div>
        <p>Рейтинг строится на <b>событиях сделки внутри платформы</b>: сметы, приёмки
        этапов, эскроу-платежи. Подделать их дороже, чем написать отзыв — а перенести
        на другую площадку невозможно</p>
      </div>
      <ul style="margin-top:20px">
        <li class="ok"><b>Удерживает подрядчиков:</b> репутация накоплена здесь и здесь
        же приносит заказы</li>
        <li><b>Основа для матчинга:</b> следующий шаг — подбирать подрядчика под проект
        по этим же девяти измерениям</li>
        <li class="warm"><b>Честно:</b> тональность работает, привязка к аспектам пока
        сырая. Проверил — и не выпустил в продакшен</li>
      </ul>
    </div>
  </div>
  <div class="evid">
    <span class="cap">Доказательство</span>
    <span class="e"><b>1 212</b> отзывов собрано</span>
    <span class="e"><b>0.96</b> нейросеть против <b>0.87</b> у простого метода</span>
    <span class="e">единственная фича, где сложная модель выиграла</span>
  </div>""".replace("{ASPECT}", img("13_aspect_profile"))))

    # 4 — фича 3
    P.append(slide(4, """
  <span class="tag o">Фича 3 · AI-координатор</span>
  <h2 class="sm">Проект перестаёт жить в переписке</h2>
  <div class="before">
    <div class="ba was">
      <div class="t">Было</div>
      <p><b>100% опрошенных</b> ведут ремонт в мессенджерах. Через месяц никто не помнит,
      кто что обещал и на что соглашались</p>
    </div>
    <div class="arr">&rarr;</div>
    <div class="ba now">
      <div class="t">Стало</div>
      <p>Каждое сообщение превращается в <b>задачу, решение или напоминание</b>
      с кнопкой подтверждения</p>
    </div>
  </div>
  <div class="cols" style="margin-top:20px">
    <div>
      <div class="card o">
        <div class="t">Обнаружена задача</div>
        <div class="m">«Настя, пришли до вторника спецификацию по сантехнике»<br>
        <b>Кто:</b> Настя &nbsp;·&nbsp; <b>Срок:</b> вторник &nbsp;·&nbsp; <b>Этап:</b> сантехника</div>
        <div class="btns"><span class="btn p">Создать задачу</span><span class="btn">Изменить срок</span></div>
      </div>
      <div class="card g">
        <div class="t">Запрос приёмки этапа</div>
        <div class="m">«Демонтаж завершён, мусор вывезли. Прошу принять этап»</div>
        <div class="btns"><span class="btn p">Принять этап</span><span class="btn">Запросить исправления</span></div>
      </div>
      <div class="card">
        <div class="t">Напоминание</div>
        <div class="m">Изменение бюджета на <b>8 500 ₽</b> не согласовано — никто не ответил</div>
      </div>
    </div>
    <div>
      <div class="moat">
        <div class="t">Почему это не скопировать</div>
        <p>Ценность появляется только там, где рядом лежат <b>смета, график и договор
        одного проекта</b>. Отдельный чат-бот этого контекста не имеет — а у нас он
        уже есть</p>
      </div>
      <ul style="margin-top:20px">
        <li class="ok"><b>Главный драйвер retention:</b> платформа становится местом,
        где живёт проект, а не ещё одним мессенджером</li>
        <li><b>Питает рейтинг:</b> из карточек считаются сроки, приёмки с первого раза
        и скорость ответов подрядчика</li>
        <li class="warm"><b>ИИ ничего не решает сам</b> — не принимает этап и не двигает
        бюджет без подтверждения человека</li>
      </ul>
    </div>
  </div>
  <div class="evid">
    <span class="cap">Доказательство</span>
    <span class="e"><b>21</b> карточка из 45 сообщений</span>
    <span class="e"><b>100%</b> точность — ни одной ложной карточки</span>
    <span class="e">поймал потерянную договорённость на 8 500 ₽</span>
  </div>"""))

    # 5 — маховик
    P.append(slide(5, """
  <span class="tag d">Как это работает вместе</span>
  <h2 class="sm">Три фичи производят данные друг для друга</h2>
  <p style="font-size:28px;color:var(--soft);margin-top:8px;max-width:88ch">
  По отдельности это три полезных инструмента. Вместе — механизм, где каждый проект
  на платформе делает следующий точнее.</p>
  <div class="wheel">
    <div class="node">
      <div class="n" style="color:var(--key)">Аудит сметы</div>
      <h3>Сметы и версии смет</h3>
      <div class="gives">Даёт рейтингу: <b>ценовую честность</b> подрядчика и
      <b>рост сметы</b> против исходной — объективно, из документов</div>
    </div>
    <div class="node">
      <div class="n" style="color:var(--warm)">Координатор</div>
      <h3>Приёмки, сроки, ответы</h3>
      <div class="gives">Даёт рейтингу: <b>приёмки с первого раза</b>,
      <b>соблюдение сроков</b>, <b>скорость реакции</b> — из реальных событий проекта</div>
    </div>
    <div class="node">
      <div class="n" style="color:var(--ok)">Рейтинг мастера</div>
      <h3>Профиль доверия</h3>
      <div class="gives">Даёт платформе: <b>подбор подрядчика</b> под проект и причину
      подрядчику оставаться — репутация работает только здесь</div>
    </div>
  </div>
  <div class="moat" style="margin-top:26px">
    <div class="t">Ров, который конкурент не скопирует</div>
    <p>Сегодня модели учатся на публичных данных — это решает холодный старт,
    продукт полезен с первого дня. Но <b>сметы, приёмки и споры рождаются только
    внутри платформы</b>. Чем больше проектов — тем точнее аудит, честнее рейтинг
    и умнее подбор. Эти данные нельзя купить</p>
  </div>"""))

    # 6 — зрелость решений
    P.append(slide(6, """
  <span class="tag">Зрелость решений</span>
  <h2 class="sm">Каждую фичу проверял: сложная модель или простая</h2>
  <div class="cols wide" style="margin-top:18px">
    <div class="figbox"><img class="fig" src="{EXP}" alt="Три эксперимента"></div>
    <div>
      <ul>
        <li class="ok"><b>Нейросеть применил там, где она выиграла измерением</b> — на текстах
        отзывов. Один раз из трёх</li>
        <li class="warm"><b>Дважды отказался от сложного:</b> на ценах и на разборе чатов
        простые методы оказались точнее — и я взял их</li>
        <li><b>Что не выпустил:</b> аспектную часть рейтинга и поиск по договорам —
        качество не подтвердилось, честно перенёс в roadmap</li>
      </ul>
      <div class="quote ok">Продукту нужна не самая модная модель, а та, что доказала
      пользу. Я выбираю по данным, а не по моде</div>
      <div class="evid" style="margin-top:26px">
        <span class="cap">Инженерия</span>
        <span class="e"><b>68</b> автотестов и CI</span>
        <span class="e"><b>3 581</b> запись собрана своими скраперами</span>
      </div>
    </div>
  </div>""".replace("{EXP}", img("12_three_experiments"))))

    html = HEAD + "".join(P) + "</div>\n"
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{OUT}  ·  {len(html)/1024:.0f} КБ  ·  6 слайдов 1920x1080")


if __name__ == "__main__":
    build()
