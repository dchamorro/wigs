"""
build_demo.py — Genera una version demo del marcador con un tablero embebido.
Uso: python3 scripts/build_demo.py web/marcador.html dist/demo_data.xlsx dist/demo.html
"""
import sys, base64

def main(html_path, xlsx_path, out_path):
    b64 = base64.b64encode(open(xlsx_path,'rb').read()).decode()
    html = open(html_path).read()
    anchor = "setInterval(()=>{const d=new Date();"
    assert anchor in html, 'anchor de inyeccion no encontrado en el HTML'
    inject = f"""
/* ---- DEMO: tablero embebido; arrastrar un archivo real lo reemplaza ---- */
const EMBEDDED_B64='{b64}';
(function(){{
  try{{
    const bin=atob(EMBEDDED_B64), arr=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)arr[i]=bin.charCodeAt(i);
    const wb=XLSX.read(arr,{{type:'array'}});
    document.getElementById('drop').classList.add('hidden');
    document.getElementById('weekinfo').textContent='DATOS DE DEMOSTRACIÓN';
    buildSlides(parseWorkbook(wb));
  }}catch(e){{console.error('demo load',e);}}
}})();
"""
    open(out_path,'w').write(html.replace(anchor, inject + anchor))
    print('demo ->', out_path)

if __name__ == '__main__':
    if len(sys.argv)!=4: print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
