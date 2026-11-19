"""Baja un video (YouTube, Twitch VOD o clip, o cualquier web que soporte yt-dlp) o copia un archivo local.

Uso: python clipper/descargar.py <enlace o archivo> [--desde 1:20:00 --hasta 2:10:00]
Deja trabajo/<id>/video.mp4 e info.json e imprime la carpeta.
--desde/--hasta sirven para directos largos de Twitch: baja solo ese trozo.
Tiene que correr en el portatil: desde GitHub Actions y la nube YouTube suele bloquear la descarga.
"""
import argparse, hashlib, json, os, shutil, subprocess, sys

RAIZ= os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'trabajo')


def main():
    ap= argparse.ArgumentParser()
    ap.add_argument('fuente'); ap.add_argument('--desde'); ap.add_argument('--hasta')
    a= ap.parse_args()
    ident= hashlib.md5((a.fuente + str(a.desde) + str(a.hasta)).encode()).hexdigest()[:10]
    carpeta= os.path.abspath(os.path.join(RAIZ, ident)); os.makedirs(carpeta, exist_ok=True)
    destino= os.path.join(carpeta, 'video.mp4')
    info= {'fuente': a.fuente, 'desde': a.desde, 'hasta': a.hasta}
    if os.path.isfile(a.fuente):
        if a.desde or a.hasta:
            cmd= ['ffmpeg', '-v', 'error', '-y'] + (['-ss', a.desde] if a.desde else []) + (['-to', a.hasta] if a.hasta else [])
            subprocess.run(cmd + ['-i', a.fuente, '-c', 'copy', destino], check=True)
        else:
            shutil.copy(a.fuente, destino)
        info['titulo']= os.path.splitext(os.path.basename(a.fuente))[0]
    elif not os.path.exists(destino):
        cmd= [sys.executable, '-m', 'yt_dlp', '-f', 'bv*[height<=1080]+ba/b[height<=1080]/b', '--merge-output-format', 'mp4',
              '-o', destino, '--write-info-json', '--no-playlist']
        if a.desde or a.hasta:
            cmd+= ['--download-sections', f"*{a.desde or '0'}-{a.hasta or 'inf'}", '--force-keyframes-at-cuts']
        subprocess.run(cmd + [a.fuente], check=True)
        meta= os.path.join(carpeta, 'video.info.json')
        if os.path.exists(meta):
            m= json.load(open(meta, encoding='utf-8'))
            info.update(titulo=m.get('title'), canal=m.get('uploader') or m.get('channel'), url=m.get('webpage_url'),
                        duracion=m.get('duration'), plataforma=m.get('extractor_key'))
            os.remove(meta)
    json.dump(info, open(os.path.join(carpeta, 'info.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(carpeta)


if __name__ == '__main__':
    main()
