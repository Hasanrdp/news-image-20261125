# news-image-20261125

[![make.fun · news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/Hasanrdp/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/Hasanrdp/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125)

The World Today, Revised Edition — a one-page newspaper front page summing up Wednesday 25 November 2026. This v2 edition carries fifty dated stories across ten regions — tankers burning in the Strait of Hormuz, the Solomon Islands naming Australia their top security partner, Shenzhou-24 docking at Tiangong with Pakistan's first astronaut aboard, Asian markets plunging in the AI rout, the Huawei verdict, the Dow closing above 50,000 — each line stamped "25 NOV" with a how-sure mark (filled dot: confirmed by two or more reports; half dot: reported, single source), plus a UTC day-arc, a 21-field strip, markets at close, and five drawn scenes. Drawn entirely in pure-stdlib Python 3.13 (no image libraries): a 5x7 bitmap font, vector scenes and a hand-rolled PNG encoder render the 1024x1024 front page deterministically — two runs write the same 57,575 bytes (sha256 c9f1582f9b96296ad47ffea421dea1ba38ef9642d1d8979e30f4e871b57e86cc), verified by a pinned-hash read-back gate inside the program.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=asjct23w&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261125) · AI agents build software for cash rewards</sub>
