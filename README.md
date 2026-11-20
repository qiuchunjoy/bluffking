# BluffKing Daily Bean Claims

For each configured account, the script claims eligible recovery beans and the daily subsidy. The GitHub Actions log shows each reward separately and the final available balance.

## Daily Schedule

GitHub Action runs daily at **00:30 UTC** (08:30 Singapore time).

## Manual Run

```bash
pip install -r requirements.txt
playwright install chromium
python claim_and_gift.py
```

## Notes

- Each reported credit is matched to a new wallet history entry. Disabled claims show zero and the reason from the wallet. An unverified claim is marked for review.
- Password is currently hardcoded; consider using GitHub Secrets for production.
