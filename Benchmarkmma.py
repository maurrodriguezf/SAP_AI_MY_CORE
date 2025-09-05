import os
import subprocess
import time
import shutil
import sys
import torch
import torch.nn.functional as F

# Archivos de kernel
cpp_file = "wmma_kernel.cpp"
exe_file = "wmma_bench"

# —————— COMPILACIÓN WMMA ——————
def compile_wmma():
    # Busca la ruta absoluta de hipcc
    hipcc_path = shutil.which("hipcc")
    if hipcc_path is None:
        print("ERROR: 'hipcc' no se encuentra en PATH.", file=sys.stderr)
        print("Asegúrate de que ROCm/HIP esté instalado y que 'hipcc.exe' esté en tu PATH.", file=sys.stderr)
        sys.exit(1)

    # Construye el comando base
    cmd = [
        hipcc_path,
        "--offload-arch=gfx1102",
    ]

    # Agrega automáticamente los includes de MSVC/Windows SDK
    include_env = os.environ.get("INCLUDE", "")
    if include_env:
        for inc_path in include_env.split(os.pathsep):
            if os.path.isdir(inc_path):
                cmd.extend(["-I", inc_path])

    # Agrega el archivo fuente y el ejecutable de salida
    cmd.extend([cpp_file, "-o", exe_file])

    print("Compilando WMMA kernel:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print("Error al compilar WMMA kernel:\n", p.stderr, file=sys.stderr)
        sys.exit(1)
    print("Compilación WMMA OK.\n")

# —————————— PARTE PYTORCH ——————————
class FP8SimNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.l1 = torch.nn.Linear(1024, 1024).half().cuda()
    def forward(self, x):
        scale = x.abs().max() / 127.0
        x_int8 = torch.round(x/scale).clamp(-127,127).to(torch.int8)
        x = x_int8.float() * scale
        return F.relu(self.l1(x))

model = FP8SimNet().eval()
inp   = torch.randn(64, 1024).half().cuda()

def benchmark(fn, warmup=10, iters=100):
    for _ in range(warmup):
        _ = fn()
    torch.cuda.synchronize()
    t0 = time.time()
    for _ in range(iters):
        _ = fn()
    torch.cuda.synchronize()
    return (time.time() - t0) / iters

def run_fp16():
    return F.relu(model.l1(inp))

def run_fp8sim():
    scale   = inp.abs().max() / 127.0
    inp_i8  = torch.round(inp/scale).clamp(-127,127).to(torch.int8)
    x_half  = (inp_i8.float()*scale).half()
    return F.relu(model.l1(x_half))

# —————— EJECUCIÓN WMMA ——————
def run_wmma_bench():
    p = subprocess.run(f"./{exe_file}", shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        print("Error al ejecutar WMMA bench:\n", p.stderr, file=sys.stderr)
        sys.exit(1)
    for line in p.stdout.splitlines():
        if "Elapsed GPU time" in line:
            return float(line.split(":")[1].split()[0])
    raise RuntimeError("No encontré el tiempo en output de WMMA bench")

def benchmark_wmma(iters=100):
    times = []
    for _ in range(iters):
        t = run_wmma_bench()
        times.append(t / 1000.0)
    return sum(times) / len(times)

# —————— MAIN ——————
if __name__ == "__main__":
    # Ejecutar benchmarks PyTorch
    t_fp16   = benchmark(run_fp16,   warmup=10, iters=100)
    t_fp8sim = benchmark(run_fp8sim, warmup=10, iters=100)

    # Compilar y ejecutar WMMA
    compile_wmma()
    time.sleep(0.2)
    t_wmma = benchmark_wmma(iters=100)

    # Reporte final
    print(f"FP16 puro:    {t_fp16*1000:.2f} ms / iter")
    print(f"FP8 simulado: {t_fp8sim*1000:.2f} ms / iter → {t_fp8sim/t_fp16:.2f}×")
    print(f"WMMA (HIP):   {t_wmma*1000:.2f} ms / iter → {t_wmma/t_fp16:.2f}×")
