@echo off
echo ========================================
echo CASCADE CONTINUOUS MONITOR
echo 80%% Win Rate Signal Scanner
echo ========================================
echo.
echo Starting continuous monitoring...
echo Press Ctrl+C to stop
echo.

cd C:\Users\Casey\Desktop\memory-phase-transition

python cascade_scanner.py --continuous --interval 15 --symbols COIN,RIOT,MARA,PLTR,NVDA,META,TSLA,AMD,AAPL,MSFT,GOOGL,ABNB,SNOW,SHOP,SQ,ROKU,SNAP,NFLX,MSTR,CLSK,BITF,HUT,SOFI,HOOD,RBLX,RIVN,LCID,ARM,IONQ,SMCI,AI,PATH,DDOG,NET,CRWD,ZS,OKTA,TWLO,U,PINS

pause