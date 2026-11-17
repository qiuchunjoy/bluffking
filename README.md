# BluffKing Daily Claim & Gift

Automatically claims recovery beans and gifts all available gold beans to 克劳德.

## Daily Schedule

GitHub Action runs daily at **00:30 UTC** (08:30 Singapore time).

## Manual Run

```bash
pip install -r requirements.txt
playwright install chromium
python claim_and_gift.py
```

## Notes

- Correctly parses `Available 2,180` style balances (with commas).
- Gifts only if balance >= 10.
- Password is currently hardcoded; consider using GitHub Secrets for production.
