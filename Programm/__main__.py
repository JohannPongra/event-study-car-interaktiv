"""Ein gemeinsamer Einstieg für Installation, Analyse, Prüfung und Oberfläche."""
from Programm.grundlagen.pfade import pfad
import argparse, importlib, os, sys
from Programm.grundlagen.pfade import ORDNER
sys.dont_write_bytecode = True
os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('MPLCONFIGDIR', str(pfad(ORDNER, 'Daten/Zwischenspeicher/Matplotlib')))

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('befehl', choices=['installieren', 'reproduzieren', 'analyse', 'oberflaeche', 'pruefen', 'transkripte', 'tests', 'aufbereiten', 'sentiment', 'berechnen', 'regression', 'akquise', 'kontextvergleich', 'laptop-import', 'satzcache'])
    a, rest = parser.parse_known_args(argv)
    old = sys.argv
    sys.argv = [old[0], *rest]
    try:
        if a.befehl == 'installieren':
            from Programm.werkzeuge.installation import main as run
            return run()
        if a.befehl == 'reproduzieren':
            from Programm.ablaeufe.reproduktion import main as run
            return run()
        if a.befehl == 'pruefen':
            from Programm.projektpruefung.dateiinventar import main as run
            return run(rest)
        if a.befehl == 'transkripte':
            from Programm.transkripte.berichte import main as run
            return run()
        if a.befehl == 'tests':
            from Programm.werkzeuge.tests import main as run
            return run(rest)
        if a.befehl == 'oberflaeche':
            p = argparse.ArgumentParser()
            p.add_argument('--alles', '--reproduzieren', action='store_true')
            p.add_argument('--port', type=int, default=8766)
            p.add_argument('--ohne-browser', action='store_true')
            args = p.parse_args(rest)
            if args.alles:
                from Programm.ablaeufe.reproduktion import reproduzieren
                reproduzieren()
                return 0
            from Programm.oberflaeche.server import starten
            starten(args.port, not args.ohne_browser)
            return 0
        if a.befehl == 'analyse':
            from Programm.ablaeufe.reproduktion import main as run
            return run()
        if a.befehl == 'satzcache':
            from Programm.werkzeuge.satzcache_uebernahme import vorbereiten
            vorbereiten()
            return 0
        p = argparse.ArgumentParser()
        p.add_argument('--config')
        if a.befehl == 'laptop-import':
            p.add_argument('export')
        args = p.parse_args(rest)
        from Programm.grundlagen.konfiguration import laden
        cfg = laden(args.config)
        if a.befehl == 'laptop-import':
            from Programm.werkzeuge.laptop_import import importieren
            importieren(args.export, cfg)
            return 0
        routes = {'aufbereiten': ('datenaufbereitung.aufbereitung', 'verarbeiten'), 'sentiment': ('sentiment.auswertung', 'auswerten'), 'berechnen': ('berechnung.berechnung', 'berechnen'), 'regression': ('statistik.auswertung', 'regressieren'), 'akquise': ('datenerhebung.sammlung', 'sammeln'), 'kontextvergleich': ('ablaeufe.kontextvergleich', 'vergleichen')}
        module, name = routes[a.befehl]
        if a.befehl == 'sentiment' and cfg['sentiment_method'] != 'sentence':
            module = 'sentiment.kontext.auswertung'
        getattr(importlib.import_module('Programm.' + module), name)(cfg)
        return 0
    except Exception as e:
        print('Nicht abgeschlossen: ' + str(e), file=sys.stderr)
        return 1
    finally:
        sys.argv = old
if __name__ == '__main__':
    raise SystemExit(main())
