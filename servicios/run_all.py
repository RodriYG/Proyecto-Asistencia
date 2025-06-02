import subprocess

scripts = [
    "busca.py",
    "gestj.py",
    "histo.py",
    "justi.py",
    "login.py",
    "masis.py",
    "modas.py",
    "regel.py",
    "rport.py",
    "tuper.py",
    "vturn.py"
]

processes = []

for script in scripts:
    print(f"Ejecutando {script}...")
    p = subprocess.Popen(["python", script])
    processes.append(p)

for p in processes:
    p.wait()