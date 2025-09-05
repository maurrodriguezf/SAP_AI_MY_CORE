import torch
import torch.nn as nn
import torch.nn.functional as F

# Simula la cuantización a FP8 usando INT8 + escala
def fake_fp8_quant(x):
    # Escala por tensor (también podrías hacerlo por canal)
    scale = x.abs().max() / 127.0
    x_int8 = torch.round(x / scale).clamp(-127, 127).to(torch.int8)
    return x_int8, scale

# Simula la desquantización desde INT8 a FP16
def fake_fp8_dequant(x_int8, scale):
    return x_int8.float() * scale

# Red simple con simulación de FP8 en la entrada
class FP8SimNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear1 = nn.Linear(8, 16)
        self.linear2 = nn.Linear(16, 4)

    def forward(self, x):
        # Cuantizamos la entrada como si fuera FP8
        x_int8, scale = fake_fp8_quant(x)
        x = fake_fp8_dequant(x_int8, scale)

        # Seguimos el flujo en FP16 o FP32
        x = F.relu(self.linear1(x.half()))  # simula uso FP16
        x = self.linear2(x)
        return x.float()  # opcional: convertir a FP32 para salida final
    
model = FP8SimNet().cuda().half()
model.eval()

# Tensor de prueba
input_tensor = torch.randn(1, 8).cuda().half()

with torch.no_grad():
    output = model(input_tensor)
    print("Output:", output)

