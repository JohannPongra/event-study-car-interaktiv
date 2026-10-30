from Programm.ausgabe.grafiken.speichern import speichern_grafik
from Programm.grundlagen.pfade import pfad
from Programm.ausgabe.formatierung import renditeeinheit
from Programm.ausgabe.formatierung import GOLD
from Programm.ausgabe.formatierung import GRUEN
from Programm.grundlagen.konfiguration import modell_predictors
import matplotlib.pyplot as plt
from Programm.ausgabe.formatierung import zahl

def ereignisverlauf(out, data, daily, cfg):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7))
    if not daily.empty:
        curve = daily.groupby('relative_day')[['ar', 'cumulative_ar']].mean() * 100
        axes[0].plot(curve.index, curve.ar, marker='o', color=GRUEN, label='Mittlere AR')
        axes[0].plot(curve.index, curve.cumulative_ar, marker='o', color=GOLD, label='Kumulierte mittlere AR')
        axes[0].axhline(0, color='#999999', lw=0.7)
        axes[0].set_xticks(curve.index)
        axes[0].legend(frameon=False, fontsize=8)
    axes[0].set(xlabel='Handelstage relativ zum Ereignis', ylabel=renditeeinheit(cfg), title='Mittlere Kursreaktion (deskriptiv)')
    corr = data[list(dict.fromkeys([*cfg['predictors'], *modell_predictors(cfg, 'abs_car'), 'car', 'abs_car']))].corr()
    img = axes[1].imshow(corr, vmin=-1, vmax=1, cmap='BrBG')
    axes[1].set(xticks=range(len(corr)), yticks=range(len(corr)), xticklabels=corr.columns.str.upper(), yticklabels=corr.columns.str.upper(), title='Korrelationen')
    axes[1].tick_params(axis='x', labelsize=8)
    axes[1].grid(False)
    for i in range(len(corr)):
        for j in range(len(corr)):
            axes[1].text(j, i, zahl(corr.iloc[i, j], 2), ha='center', va='center', fontsize=8, color='white' if abs(corr.iloc[i, j]) > 0.75 else '#17312f')
    fig.colorbar(img, ax=axes[1], shrink=0.75)
    speichern_grafik(fig, pfad(out, 'ueberblick'))
