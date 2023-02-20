![example workflow](https://github.com/mPyKen/rakuten-email-pts/actions/workflows/main.yml/badge.svg)
# 楽天クリックでポイント自動化ツール
## Setup
Go to https://emagazine.rakuten.co.jp and subscribe for emails from:

- [楽天スーパーポイントギャラリーニュース](mailto:point-g@emagazine.rakuten.co.jp)
- [楽天カレンダーお得なニュース](mailto:calendar-info@emagazine.rakuten.co.jp)
- [楽天特典付きキャンペーンニュース](mailto:incentive@emagazine.rakuten.co.jp)
- [メールdeポイント](mailto:info@pointmail.rakuten.co.jp)
- [ポイント10倍ニュース](mailto:pointo10henbai@emagazine.rakuten.co.jp)

Prepare following values:
- A: imap server url. e.g. `imap.gmail.com`
- B: folder to parse emails at. e.g. `"Rakuten Point"` (if using filters with labels on gmail)
- C: email address
- D: email password
- E: mark unrelated emails in the same folder as read, `true` or `false`
- F: password on rakuten

Generate the 1-line string
```
IMAP_SERVER='<A>';IMAP_FOLDER='<B>';EMAIL_ADDRESS='<C>';EMAIL_PASSWORD='<D>';EMAIL_MARK_READ='<E>';RAKUTEN_PASSWORD='<F>'
```
e.g.
```
IMAP_SERVER='imap.gmail.com';IMAP_FOLDER='"Rakuten Point"';EMAIL_ADDRESS='example@gmail.com';EMAIL_PASSWORD='Epassword';EMAIL_MARK_READ='false';RAKUTEN_PASSWORD='Rpassword'
```

and paste this string [here](https://opinionatedgeek.com/codecs/base64encoder) to generate a base64 string. If you have multiple accounts, repeat the previous steps and concatenate the resulting base64-encoded strings with a comma: `config1,config2,...`

Next, fork this repo (and star it while you are at it). Go to repository settings -> Secrets and variables -> Actions and add a secret called `CONFIGURATION` with the previously generated string as its value.

GitHub Actions should now run once per day to click on the links.
