import subprocess

scripts = [
    "busca.py",
    "gestj.py",
    "histo.py",
    "justi.py",
    "login.py",
    "masis.py"
]

processes = []

for script in scripts:
    print(f"Ejecutando {script}...")
    p = subprocess.Popen(["python", script])
    processes.append(p)

# (Opcional) Esperar a que todos los procesos terminen
for p in processes:
    p.wait()