#!/usr/bin/env python3
import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://stellar_user:stellar_password@localhost:5432/stellar_sales')
    row = await conn.fetchrow(
        'SELECT crm_data FROM final_records WHERE transcript_id = $1 ORDER BY created_at DESC LIMIT 1',
        '61775137'
    )
    await conn.close()

    if row:
        crm_data = row['crm_data']
        print(f"Deal: {crm_data.get('deal', 'N/A')}")
        print(f"Deposit: {crm_data.get('deposit', 'N/A')}")
        print(f"Outcome: {crm_data.get('outcome', 'N/A')}")
        print(f"Close Date: {crm_data.get('close_date', 'N/A')}")
        print(f"Win Probability: {crm_data.get('win_probability', 'N/A')}")
    else:
        print("No record found")

asyncio.run(check())
