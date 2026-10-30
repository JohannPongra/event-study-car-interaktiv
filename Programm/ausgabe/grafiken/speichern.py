import matplotlib.pyplot as plt

def speichern_grafik(fig, path):
    fig.tight_layout()
    fig.savefig(path.with_suffix('.png'), dpi=170, bbox_inches='tight')
    fig.savefig(path.with_suffix('.pdf'), bbox_inches='tight')
    plt.close(fig)
